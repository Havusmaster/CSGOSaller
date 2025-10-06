import asyncio
import logging
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from flask import Flask
from config import BOT_TOKEN, ADMIN_ID

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO)

# === Инициализация бота ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Flask (для Render) ===
app = Flask(__name__)

@app.route("/")
def index():
    return f"✅ Telegram Bot is running on Render!<br>Admin ID: {ADMIN_ID}"

# === /start — приветствие ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[KeyboardButton(text="🚀 Start")]]
    )
    await message.answer(
        "Добро пожаловать! 👋\n\nНажмите кнопку 🚀 Start, чтобы продолжить.",
        reply_markup=keyboard
    )

# === Кнопка “🚀 Start” ===
@dp.message(F.text == "🚀 Start")
async def handle_start_button(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lang_uz")]
        ]
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)

# === Русский язык ===
@dp.callback_query(F.data == "lang_ru")
async def lang_ru(callback: types.CallbackQuery):
    shop_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Перейти в магазин", callback_data="open_shop")]
        ]
    )
    await callback.message.answer(
        "Привет! 👋\n\nДобро пожаловать в наш бот-магазин. Здесь вы можете посмотреть товары и сделать заказ.",
        reply_markup=shop_button
    )
    await callback.answer()

# === Узбекский язык ===
@dp.callback_query(F.data == "lang_uz")
async def lang_uz(callback: types.CallbackQuery):
    shop_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Do‘konga o‘tish", callback_data="open_shop")]
        ]
    )
    await callback.message.answer(
        "Salom! 👋\n\nBot-do‘konimizga xush kelibsiz. Bu yerda siz mahsulotlarni ko‘rishingiz va buyurtma berishingiz mumkin.",
        reply_markup=shop_button
    )
    await callback.answer()

# === Магазин ===
@dp.callback_query(F.data == "open_shop")
async def open_shop(callback: types.CallbackQuery):
    await callback.message.answer("🛍 Здесь будет магазин. (Позже можно добавить товары или ссылки)")
    await callback.answer()

# === Flask-сервер (в отдельном потоке) ===
def run_flask():
    logging.info("🌐 Flask сервер запущен...")
    app.run(host="0.0.0.0", port=10000)

# === Запуск Telegram-бота ===
async def run_bot():
    logging.info("🚀 Запуск Telegram-бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# === Главная функция ===
async def main():
    # Flask запускаем в отдельном потоке
    Thread(target=run_flask, daemon=True).start()
    # Aiogram работает в главном asyncio цикле
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())
