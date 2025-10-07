import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://csgosaller-1.onrender.com{WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# === Хендлеры ===
@dp.message()
async def handle_message(message: types.Message):
    await message.answer("Привет! Бот работает через webhook 🚀")

# === Flask / AioHTTP сервер ===
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("🧹 Webhook удалён и бот выключен")

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 5000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
