# bot.py
"""
Главный файл — точка входа. Запускает Telegram-бот (aiogram) и Flask WebApp в отдельных потоках.
README:
1) Установите зависимости:
   pip install aiogram==2.25.1 Flask

2) Установите переменные окружения (или правьте config.py):
   - BOT_TOKEN: токен Telegram бота
   - ADMIN_IDS: через запятую список admin ID, например "123456789,987654321"
   - APP_URL: публичный адрес вашего веб-приложения (Replit URL), например "https://my-repl.username.repl.co"

3) Запуск:
   python bot.py

4) Открыть WebApp:
   - Откройте в браузере APP_URL (на Replit URL)
   - Или в Telegram нажмите кнопку "Открыть магазин" в боте (команда /shop)

Описание:
- Магазин доступен через веб или команды бота.
- При нажатии "Купить" бот попросит ссылку и отправит заявку админу.
- Админы получают уведомления о покупках и результатах аукционов.
"""

import threading
import time
import logging
import re

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import BOT_TOKEN, ADMIN_IDS, APP_URL, FLASK_PORT
from webapp import app as flask_app  # импортируем Flask приложение
from database import get_products, get_product, place_bid, get_auctions, get_highest_bid, finish_auction
from admin import is_admin
import database

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Aiogram setup -----
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для покупки
class BuyStates(StatesGroup):
    waiting_for_link = State()

# Утилиты
def admin_notify_text_for_purchase(product_name, price, buyer, link):
    return f"🛒 Новая покупка!\n📦 Товар: {product_name}\n💰 Цена: {price}\n👤 Покупатель: {buyer}\n🔗 Ссылка: {link}"

# ----- Команды -----
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    text = "👋 Привет! Это бот CSsaler — магазин и аукцион.\n\n" \
           "Команды:\n" \
           "/shop — открыть список товаров\n" \
           "/auctions — показать активные аукционы\n" \
           "/buy <id> — купить товар по ID\n\n" \
           f"Также можно открыть WebApp: {APP_URL}"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛍️ Открыть магазин", url=APP_URL))
    await message.answer(text, reply_markup=kb)

@dp.message_handler(commands=['shop'])
async def cmd_shop(message: types.Message):
    prods = get_products(only_available=True)
    if not prods:
        await message.answer("❗ В магазине пока нет товаров.")
        return
    for p in prods:
        text = f"📦 <b>{p['name']}</b>\n{p['description']}\n💰 Цена: {p['price']}\nТип: {'🔫 Оружие' if p['type']=='weapon' else '💼 Агент'}"
        if p['type']=='weapon' and p['float_value']:
            text += f"\n🔢 Float: {p['float_value']}"
        kb = types.InlineKeyboardMarkup(row_width=2)
        if p.get('link'):
            kb.add(types.InlineKeyboardButton("🔗 Ссылка на продукт", url=p['link']))
        # Кнопка "Написать админу" — возьмём первого админа
        if ADMIN_IDS:
            kb.add(types.InlineKeyboardButton("💬 Написать админу", url=f"tg://user?id={ADMIN_IDS[0]}"))
        kb.add(types.InlineKeyboardButton("🛒 Купить", callback_data=f"buy_{p['id']}"))
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("buy_"))
async def process_buy_callback(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_",1)[1])
    p = get_product(product_id)
    if not p:
        await callback_query.answer("❗ Товар не найден", show_alert=True)
        return
    await bot.send_message(callback_query.from_user.id, f"🛒 Вы выбрали <b>{p['name']}</b>.\nПришлите, пожалуйста, ссылку на предмет.", parse_mode="HTML")
    # Сохраняем в FSM context id товара
    state = dp.current_state(user=callback_query.from_user.id)
    await state.update_data(product_id=product_id)
    await BuyStates.waiting_for_link.set()
    await callback_query.answer()

@dp.message_handler(state=BuyStates.waiting_for_link, content_types=types.ContentTypes.TEXT)
async def process_buy_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")
    link = message.text.strip()
    p = get_product(product_id)
    if not p:
        await message.answer("❗ Товар больше не доступен.")
        await state.finish()
        return
    # Отправляем админу сообщение(я)
    buyer = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    text = admin_notify_text_for_purchase(p['name'], p['price'], buyer, link)
    # Отправляем всем администраторам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(int(admin_id), text)
        except Exception as e:
            logger.warning(f"Не удалось отправить админу {admin_id}: {e}")
    await message.answer("✅ Заявка на покупку отправлена админу!")
    await state.finish()

# ----- Аукционы: показать через /auctions -----
@dp.message_handler(commands=['auctions'])
async def cmd_auctions(message: types.Message):
    auctions = get_auctions(only_active=True)
    if not auctions:
        await message.answer("ℹ️ Нет активных аукционов.")
        return
    for a in auctions:
        highest = get_highest_bid(a['id'])
        highest_str = f"{highest['amount']} ({highest['bidder_identifier']})" if highest else "Пока нет ставок"
        remaining = a['end_timestamp'] - int(time.time())
        minutes = remaining//60 if remaining>0 else 0
        text = f"🏷 <b>{a['title']}</b>\n{a['description']}\nСтарт: {a['start_price']} | Шаг: {a['step']}\nТекущий максимум: {highest_str}\nОсталось: {minutes} мин"
        await message.answer(text, parse_mode="HTML")

# ----- Простая команда для админов: /announce_auction_end чтобы финализировать вручную (только админы) -----
@dp.message_handler(commands=['announce_auction_end'])
async def cmd_announce_end(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Только админы могут это делать.")
        return
    # Здесь можно финализировать все завершившиеся аукционы
    await message.answer("🔎 Запуск проверки аукционов...")
    await check_and_finalize_auctions(send_messages=True)
    await message.answer("✅ Проверка завершена.")

# ----- Функция для периодической проверки и завершения аукционов -----
async def check_and_finalize_auctions(send_messages=False):
    """
    Проходит по всем активным аукционам, у которых истёк end_timestamp.
    Если есть победитель — сообщает ему и администраторам.
    """
    import time
    now = int(time.time())
    with database.get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM auctions WHERE finished=0 AND end_timestamp<=?", (now,))
        rows = cur.fetchall()
        for row in rows:
            auction = dict(row)
            aid = auction['id']
            # получить лучшую ставку
            cur.execute("SELECT * FROM bids WHERE auction_id=? ORDER BY amount DESC, created_at ASC LIMIT 1", (aid,))
            best = cur.fetchone()
            if best:
                best = dict(best)
                winner_identifier = best['bidder_identifier']
                amount = best['amount']
                # отправляем победителю (если это Telegram ID или @username)
                # пытаемся определить Telegram ID из формата ID:123 or @username
                sent_to_winner = False
                try:
                    if str(winner_identifier).startswith("ID:"):
                        tid = int(str(winner_identifier).split("ID:")[1])
                        await bot.send_message(tid, f"🏆 Поздравляем! Вы победили в аукционе <b>{auction['title']}</b>.\nСумма: {amount}", parse_mode="HTML")
                        sent_to_winner = True
                    elif str(winner_identifier).startswith("@"):
                        # найти по username — отправить через @username нельзя напрямую, попробуем отправить через ссылку (не гарантируется)
                        # просто оповестим админов, что победителем является этот username
                        sent_to_winner = False
                except Exception as e:
                    logger.warning(f"Не удалось отправить сообщение победителю: {e}")
                # отправляем администраторам итог
                result_text = f"🏁 Аукцион завершён!\n🏷 Лот: {auction['title']}\nПобедитель: {winner_identifier}\nСтавка: {amount}"
                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(int(admin_id), result_text)
                    except Exception as e:
                        logger.warning(f"Не удалось отправить админам итог аукциона: {e}")
            else:
                # нет ставок
                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(int(admin_id), f"⚠️ Аукцион <b>{auction['title']}</b> закончился — ставок не было.", parse_mode="HTML")
                    except Exception as e:
                        logger.warning(f"Не удалось отправить админам сообщение о пустом аукционе: {e}")
            # отмечаем как завершённый
            cur.execute("UPDATE auctions SET finished=1 WHERE id=?", (aid,))
        conn.commit()

# ----- Background thread для проверки аукционов -----
def start_auction_checker(loop):
    """
    Запускает цикл, который раз в 30 секунд проверяет аукционы и завершает просроченные.
    Запускается в отдельном потоке.
    """
    import asyncio
    async def runner():
        while True:
            try:
                await check_and_finalize_auctions(send_messages=True)
            except Exception as e:
                logger.exception("Ошибка при проверке аукционов: %s", e)
            await asyncio.sleep(30)
    # Запуск в event loop aiogram
    asyncio.run_coroutine_threadsafe(runner(), loop)

# ----- Запуск Flask в отдельном потоке -----
def run_flask():
    # Запускаем Flask приложение (webapp.app) в отдельном потоке
    # В Replit важно слушать 0.0.0.0:PORT (Flask app по умолчанию в webapp.py использует port 5000).
    flask_app.run(host="0.0.0.0", port=FLASK_PORT)

# ----- Главная точка старта -----
if __name__ == "__main__":
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask WebApp запущен в фоне.")

    # Запускаем цикл aiogram (polling)
    # Перед запуском polling — запустим background checker, ожидающий loop
    from aiogram import executor as aiogram_executor

    # Перед стартом polling получим loop и запустим проверщик
    loop = dp.loop
    checker_thread = threading.Thread(target=start_auction_checker, args=(loop,), daemon=True)
    checker_thread.start()
    logger.info("Запуск проверщика аукционов.")

    # Запуск Long Polling
    logger.info("Запуск Telegram бота (polling)...")
    aiogram_executor.start_polling(dp, skip_updates=True)
