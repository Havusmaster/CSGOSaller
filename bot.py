# bot.py
"""
Запуск Telegram-бота (aiogram 3.x) + Flask сайт (webapp) в фоне.
Все тексты — из translations.yaml (через config.t(lang,key)).
Язык и тема пользователя сохраняются в SQLite (database.set_user_pref).
По умолчанию: узбекский + тёмная тема.

Инструкции:
1) Установите зависимости: pip install -r requirements.txt
2) В окружении (Render/Replit) задайте BOT_TOKEN и ADMIN_IDS (по желанию).
3) Запуск: python bot.py
"""

import asyncio
import logging
import threading
import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import TOKEN, t, DEFAULT_LANG, DEFAULT_THEME, APP_URL, ADMIN_IDS
import database
from webapp import app as flask_app

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка токена
if not TOKEN:
    logger.error("❌ BOT_TOKEN не задан! Установите переменную окружения BOT_TOKEN.")
    raise SystemExit("BOT_TOKEN not set")

# Инициализация бота и диспетчера
bot = Bot(TOKEN)
dp = Dispatcher()

# ----------------------------
#  Помощники
# ----------------------------
def get_user_lang(tg_id: int):
    prefs = database.get_user_pref(tg_id)
    return prefs.get("lang", DEFAULT_LANG)

def get_user_theme(tg_id: int):
    prefs = database.get_user_pref(tg_id)
    return prefs.get("theme", DEFAULT_THEME)

def make_lang_kb(current_lang):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"setlang:ru"),
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data=f"setlang:uz")
    )
    return kb

def make_theme_kb(current_theme):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="🌙 Тёмная", callback_data="settheme:dark"),
        InlineKeyboardButton(text="☀️ Светлая", callback_data="settheme:light")
    )
    return kb

# ----------------------------
#  Команды
# ----------------------------
@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    # При старте создаём запись пользователя, если её нет
    tg_id = message.from_user.id
    database.set_user_pref(tg_id)  # сохранит дефолты при отсутствии
    lang = get_user_lang(tg_id)
    text = t(lang, "bot.start")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Выбрать язык", callback_data="choose_lang")],
        [InlineKeyboardButton(text="🎨 Выбрать тему", callback_data="choose_theme")],
        [InlineKeyboardButton(text="🛍️ Открыть магазин", url=APP_URL + f"?tg_id={tg_id}")]
    ])
    await message.answer(text, reply_markup=kb)

@dp.message(Command(commands=["help"]))
async def cmd_help(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(t(lang, "bot.help"))

@dp.message(Command(commands=["shop"]))
async def cmd_shop(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    prods = database.get_products(only_available=True)
    if not prods:
        await message.answer(t(lang, "bot.shop_empty"))
        return
    for p in prods:
        text = f"📦 <b>{p['name']}</b>\n{p['description']}\n💰 {p['price']}\n"
        if p['type'] == "weapon" and p.get('float_value'):
            text += f"🔢 Float: {p['float_value']}\n"
        kb = InlineKeyboardMarkup(row_width=2)
        if p.get('link'):
            kb.add(InlineKeyboardButton("🔗 Ссылка на продукт", url=p['link']))
        if ADMIN_IDS:
            kb.add(InlineKeyboardButton("💬 Написать админу", url=f"tg://user?id={ADMIN_IDS[0]}"))
        kb.add(InlineKeyboardButton("🛒 Купить", callback_data=f"buy:{p['id']}"))
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

# ----------------------------
#  Callback handlers (language/theme/buy)
# ----------------------------
@dp.callback_query(lambda c: c.data == "choose_lang")
async def choose_lang_callback(cq: types.CallbackQuery):
    tg_id = cq.from_user.id
    lang = get_user_lang(tg_id)
    await cq.message.answer(t(lang, "bot.choose_lang"), reply_markup=make_lang_kb(lang))
    await cq.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("setlang:"))
async def setlang_callback(cq: types.CallbackQuery):
    tg_id = cq.from_user.id
    _, new_lang = cq.data.split(":", 1)
    database.set_user_pref(tg_id, lang=new_lang)
    # подтверждение на новом языке
    confirm_key = "bot.lang_uz_selected" if new_lang == "uz" else "bot.lang_ru_selected"
    await cq.message.answer(t(new_lang, "bot.lang_uz_selected") if new_lang == "uz" else t(new_lang, "bot.lang_ru_selected"))
    await cq.answer()

@dp.callback_query(lambda c: c.data == "choose_theme")
async def choose_theme_callback(cq: types.CallbackQuery):
    tg_id = cq.from_user.id
    lang = get_user_lang(tg_id)
    await cq.message.answer(t(lang, "bot.choose_theme"), reply_markup=make_theme_kb(get_user_theme(tg_id)))
    await cq.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("settheme:"))
async def settheme_callback(cq: types.CallbackQuery):
    tg_id = cq.from_user.id
    _, theme = cq.data.split(":", 1)
    database.set_user_pref(tg_id, theme=theme)
    lang = get_user_lang(tg_id)
    if theme == "dark":
        await cq.message.answer(t(lang, "bot.theme_dark_selected"))
    else:
        await cq.message.answer(t(lang, "bot.theme_light_selected"))
    await cq.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("buy:"))
async def buy_callback(cq: types.CallbackQuery):
    pid = int(cq.data.split(":", 1)[1])
    p = database.get_product(pid)
    if not p:
        await cq.message.answer("❌ Товар не найден.")
        await cq.answer()
        return
    # Сохраняем ожидание ссылки
    if not hasattr(dp, "waiting_for_purchase"):
        dp.waiting_for_purchase = {}
    dp.waiting_for_purchase[cq.from_user.id] = pid
    lang = get_user_lang(cq.from_user.id)
    await cq.message.answer(t(lang, "bot.purchase_request"))
    await cq.answer()

# ----------------------------
#  Обработка текстовых сообщений (в т.ч. ссылка после "Купить")
# ----------------------------
@dp.message()
async def handle_text(message: types.Message):
    uid = message.from_user.id
    lang = get_user_lang(uid)

    # Если пользователь в процессе покупки — обрабатываем ссылку
    if hasattr(dp, "waiting_for_purchase") and uid in dp.waiting_for_purchase:
        pid = dp.waiting_for_purchase.pop(uid, None)
        p = database.get_product(pid)
        if not p:
            await message.answer("❌ Товар больше недоступен.")
            return
        link = message.text.strip()
        buyer = f"@{message.from_user.username}" if message.from_user.username else f"ID:{uid}"
        text = f"🛒 Новая покупка!\n📦 Товар: {p['name']}\n💰 Цена: {p['price']}\n👤 Покупатель: {buyer}\n🔗 Ссылка: {link}"
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(int(aid), text)
            except Exception as e:
                logger.warning("Не удалось отправить админам: %s", e)
        await message.answer(t(lang, "bot.purchase_sent"))
        return

    # Обычные сообщения — подсказка
    await message.answer(t(lang, "bot.help"))

# ----------------------------
#  Аукцион: периодическая проверка (опционально)
# ----------------------------
async def check_auctions_loop():
    while True:
        try:
            now = int(time.time())
            with database.get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM auctions WHERE finished=0 AND end_timestamp<=?", (now,))
                rows = cur.fetchall()
                for row in rows:
                    auction = dict(row)
                    aid = auction['id']
                    cur.execute("SELECT * FROM bids WHERE auction_id=? ORDER BY amount DESC, created_at ASC LIMIT 1", (aid,))
                    best = cur.fetchone()
                    if best:
                        best = dict(best)
                        winner = best['bidder_identifier']
                        amount = best['amount']
                        # уведомляем админов
                        summary = f"🏁 Аукцион завершён!\n🏷 Лот: {auction['title']}\nПобедитель: {winner}\nСтавка: {amount}"
                        for admin in ADMIN_IDS:
                            try:
                                await bot.send_message(int(admin), summary)
                            except Exception as e:
                                logger.warning("Не удалось уведомить админа: %s", e)
                    else:
                        for admin in ADMIN_IDS:
                            try:
                                await bot.send_message(int(admin), f"⚠️ Аукцион {auction['title']} закончился — ставок не было.")
                            except Exception as e:
                                logger.warning("Не удалось уведомить админа: %s", e)
                    cur.execute("UPDATE auctions SET finished=1 WHERE id=?", (aid,))
                conn.commit()
        except Exception as e:
            logger.exception("Ошибка проверки аукционов: %s", e)
        await asyncio.sleep(30)

# ----------------------------
#  Запуск Flask в фоне + polling (с предварительным удалением webhook)
# ----------------------------
def run_flask_background():
    logger.info("Запуск Flask WebApp в фоне...")
    flask_app.run(host="0.0.0.0", port=5000, threaded=True)

async def main():
    # Запустим Flask в фоне
    flask_thread = threading.Thread(target=run_flask_background, daemon=True)
    flask_thread.start()

    # Удаляем webhook (чтобы не было конфликта) — безопасно
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Удалён webhook (если был). Теперь используем polling.")
    except Exception as e:
        logger.warning("Не удалось удалить webhook: %s", e)

    # Старт цикла проверки аукционов
    asyncio.create_task(check_auctions_loop())

    # Запуск polling
    logger.info("Запуск polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Завершение работы...")
