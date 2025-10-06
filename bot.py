import logging
from flask import Flask, request
from telegram_bot import dp, bot
from aiogram import types
import asyncio

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# === Flask: Главная страница ===
@app.route("/")
def index():
    return "✅ Бот и веб-панель работают на Render!"


# === Flask: Приём webhook ===
@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        update = types.Update.model_validate(await request.get_json())
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"Ошибка при обработке webhook: {e}")
    return "ok"


# === Запуск Flask ===
if __name__ == "__main__":
    logging.info("🚀 Flask + Telegram бот запущены!")
    app.run(host="0.0.0.0", port=10000)
