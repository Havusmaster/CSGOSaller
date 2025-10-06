import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import BOT_TOKEN

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# === Команда /start ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Start")]],
        resize_keyboard=True
    )
    await message.answer("Привет 👋 Нажми 🚀 Start, чтобы начать.", reply_markup=kb)


# === Кнопка “🚀 Start” ===
@dp.message(F.text == "🚀 Start")
async def on_start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lang_uz")]
        ]
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=kb)


# === Обработка выбора языка ===
@dp.callback_query(F.data == "lang_ru")
async def lang_ru(callback: types.CallbackQuery):
    await callback.message.answer("Привет! Магазин скоро откроется 🛍")
    await callback.answer()


@dp.callback_query(F.data == "lang_uz")
async def lang_uz(callback: types.CallbackQuery):
    await callback.message.answer("Salom! Do‘kon tez orada ochiladi 🛍")
    await callback.answer()
