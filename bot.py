# telegram_bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from config import BOT_TOKEN

# Настройка
WEBHOOK_HOST = "https://csgosaller-1.onrender.com"  # URL Render
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)


# === Хендлеры ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="🚀 Start"))
    await message.answer("Добро пожаловать! 👋", reply_markup=keyboard)


@dp.message(F.text == "🚀 Start")
async def start_pressed(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lang_uz")]
    ])
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    if lang == "ru":
        await callback.message.answer("Язык установлен: Русский 🇷🇺")
    else:
        await callback.message.answer("Til o‘rnatildi: O‘zbek 🇺🇿")
    await callback.answer()


# === Функции запуска ===

async def run_bot():
    """Асинхронный запуск Telegram-бота в режиме webhook."""
    app = web.Application()

    async def handle_webhook(request):
        update = await request.json()
        await dp.feed_webhook_update(bot, update)
        return web.Response()

    app.router.add_post(WEBHOOK_PATH, handle_webhook)

    async def on_startup(app):
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"✅ Webhook установлен: {WEBHOOK_URL}")

    async def on_shutdown(app):
        await bot.delete_webhook()
        await bot.session.close()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logging.info("🚀 Запуск Telegram-бота через webhook...")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=10000)
    await site.start()

    # Не даём функции завершиться (чтобы бот оставался активным)
    while True:
        await asyncio.sleep(3600)


# Если файл запущен напрямую
if __name__ == "__main__":
    asyncio.run(run_bot())
