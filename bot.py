# bot.py
"""
Точка входа: запускает Flask (webapp.app) в фоне и aiogram 3.x бота.
Всё на русском — покупки отсылаются администраторам.
"""

import asyncio
import logging
import threading
import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import TOKEN, ADMIN_IDS, APP_URL, FLASK_HOST, FLASK_PORT, AUCTION_CHECK_INTERVAL
import database
from webapp import app as flask_app
from admin import is_admin
from database import get_products, get_product, get_auctions, get_highest_bid, get_bids_for_auction, place_bid, finish_auction

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(TOKEN)
dp = Dispatcher()

# -----------------------------
#  Утилиты
# -----------------------------
def format_purchase_text(name, price, buyer, link):
    return f"🛒 Новая покупка!\n📦 Товар: {name}\n💰 Цена: {price}\n👤 Покупатель: {buyer}\n🔗 Ссылка: {link}"

# -----------------------------
#  Команды бота
# -----------------------------
@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Открыть магазин", url=APP_URL)],
        [InlineKeyboardButton(text="⚔️ Аукционы", callback_data="show_auctions")]
    ])
    await message.answer("👋 Добро пожаловать в CSsaler! Выберите действие:", reply_markup=kb)

@dp.message(Command(commands=["shop"]))
async def cmd_shop(message: types.Message):
    prods = get_products(only_available=True)
    if not prods:
        await message.answer("❗ В магазине пока нет товаров.")
        return
    for p in prods:
        text = f"📦 <b>{p['name']}</b>\n{p['description']}\n💰 Цена: {p['price']}\nТип: {'🔫 Оружие' if p['type']=='weapon' else '💼 Агент'}"
        if p['type']=='weapon' and p['float_value']:
            text += f"\n🔢 Float: {p['float_value']}"
        kb = InlineKeyboardMarkup(row_width=2)
        if p.get('link'):
            kb.add(InlineKeyboardButton("🔗 Ссылка на продукт", url=p['link']))
        if ADMIN_IDS:
            kb.add(InlineKeyboardButton("💬 Написать админу", url=f"tg://user?id={ADMIN_IDS[0]}"))
        kb.add(InlineKeyboardButton("🛒 Купить", callback_data=f"buy:{p['id']}"))
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(lambda c: c.data and c.data.startswith("buy:"))
async def callback_buy(callback: types.CallbackQuery):
    # Формат callback 'buy:{id}'
    pid = int(callback.data.split(":", 1)[1])
    p = get_product(pid)
    if not p:
        await callback.message.answer("❌ Товар не найден или уже продан.")
        await callback.answer()
        return
    # Просим пользователя прислать ссылку — сохраняем в памяти (простая схема)
    # Так как aiogram3 имеет встроенный state, можно использовать dispatcher.storage,
    # для простоты реализуем временное поле в user_data через dispatcher.storage (не долговечно)
    # Но проще: попросим пользователь отправить ссылку в следующем сообщении и пометим текст
    await callback.message.answer(f"🛒 Вы выбрали <b>{p['name']}</b>.\nПришлите, пожалуйста, ссылку на предмет.", parse_mode="HTML")
    # Сохраняем ожидаемый product_id в простом словаре
    if not hasattr(dp, "waiting_for_purchase"):
        dp.waiting_for_purchase = {}
    dp.waiting_for_purchase[callback.from_user.id] = p['id']
    await callback.answer()

@dp.message()
async def handle_text(message: types.Message):
    # Если пользователь в процессе покупки — ожидаем ссылку
    uid = message.from_user.id
    if hasattr(dp, "waiting_for_purchase") and uid in dp.waiting_for_purchase:
        pid = dp.waiting_for_purchase.pop(uid, None)
        p = get_product(pid)
        if not p:
            await message.answer("❌ Товар больше не доступен.")
            return
        link = message.text.strip()
        buyer = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
        # Отправляем сообщение всем админам
        text = format_purchase_text(p['name'], p['price'], buyer, link)
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(int(aid), text)
            except Exception as e:
                logger.warning("Не удалось уведомить админа %s: %s", aid, e)
        await message.answer("✅ Заявка на покупку отправлена админу!")
        return

    # Обычное поведение — эхо / подсказка
    await message.answer("✉️ Чтобы открыть магазин — нажмите /shop или используйте кнопку в /start")

# -----------------------------
#  Аукцион: показать через callback
# -----------------------------
@dp.callback_query(lambda c: c.data == "show_auctions")
async def show_auctions_cb(callback: types.CallbackQuery):
    auctions = get_auctions(only_active=True)
    if not auctions:
        await callback.message.answer("ℹ️ Нет активных аукционов.")
        await callback.answer()
        return
    for a in auctions:
        highest = get_highest_bid(a['id'])
        highest_str = f"{highest['amount']} ({highest['bidder_identifier']})" if highest else "Пока нет ставок"
        remaining = max(0, a['end_timestamp'] - int(time.time()))
        minutes = remaining // 60
        text = f"🏷 <b>{a['title']}</b>\n{a['description']}\nСтарт: {a['start_price']} | Шаг: {a['step']}\nТекущий максимум: {highest_str}\nОсталось: {minutes} мин"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Открыть в браузере", url=APP_URL)]
        ])
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

# -----------------------------
#  Функция проверки и завершения аукционов
# -----------------------------
async def check_and_finalize_auctions():
    """Периодически проверяет аукционы и уведомляет админов и победителей."""
    logger.info("Запущен цикл проверки аукционов")
    while True:
        try:
            now = int(time.time())
            # получаем все завершившиеся и не помеченные
            with database.get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM auctions WHERE finished=0 AND end_timestamp<=?", (now,))
                rows = cur.fetchall()
                for row in rows:
                    auction = dict(row)
                    aid = auction['id']
                    # лучшая ставка
                    cur.execute("SELECT * FROM bids WHERE auction_id=? ORDER BY amount DESC, created_at ASC LIMIT 1", (aid,))
                    best = cur.fetchone()
                    if best:
                        best = dict(best)
                        winner_identifier = best['bidder_identifier']
                        amount = best['amount']
                        # Попробуем отправить пользователю, если указан ID в формате ID:123
                        try:
                            if str(winner_identifier).startswith("ID:"):
                                tid = int(str(winner_identifier).split("ID:")[1])
                                await bot.send_message(tid, f"🏆 Поздравляем! Вы выиграли аукцион <b>{auction['title']}</b>.\nСумма: {amount}", parse_mode="HTML")
                        except Exception as e:
                            logger.warning("Не удалось отправить победителю: %s", e)
                        # уведомляем админов
                        result_text = f"🏁 Аукцион завершён!\n🏷 Лот: {auction['title']}\nПобедитель: {winner_identifier}\nСтавка: {amount}"
                        for admin in ADMIN_IDS:
                            try:
                                await bot.send_message(int(admin), result_text)
                            except Exception as e:
                                logger.warning("Не удалось отправить админам итог: %s", e)
                    else:
                        # нет ставок
                        for admin in ADMIN_IDS:
                            try:
                                await bot.send_message(int(admin), f"⚠️ Аукцион <b>{auction['title']}</b> закончился — ставок не было.", parse_mode="HTML")
                            except Exception as e:
                                logger.warning("Не удалось отправить админам сообщение о пустом аукционе: %s", e)
                    # пометить как завершённый
                    cur.execute("UPDATE auctions SET finished=1 WHERE id=?", (aid,))
                conn.commit()
        except Exception as e:
            logger.exception("Ошибка при проверке аукционов: %s", e)
        await asyncio.sleep(AUCTION_CHECK_INTERVAL)

# -----------------------------
#  Функция запуска Flask в фоне
# -----------------------------
def run_flask_background():
    # Запускаем Flask в отдельном потоке (режим dev server — для простоты).
    # На продуктиве можно выставить gunicorn, но поскольку мы запускаем всё в одном процессе, используем встроенный сервер.
    logger.info("Запуск Flask WebApp в фоне...")
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True)

# -----------------------------
#  Основная точка входа
# -----------------------------
async def main():
    # Запускаем Flask в фоне (thread)
    flask_thread = threading.Thread(target=run_flask_background, daemon=True)
    flask_thread.start()

    # Запуск задач: проверка аукционов
    asyncio.create_task(check_and_finalize_auctions())

    # Запуск aiogram polling
    logger.info("Запуск Telegram-бота (aiogram 3.x)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка приложения...")
