import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.enums import ParseMode
import logging
from config import BOT_TOKEN  # В config.py должен быть токен бота

# Включаем логирование, чтобы видеть ошибки
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


# Команда /start — показывает кнопку 🚀 Start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🚀 Start"))
    await message.answer(
        "Добро пожаловать! 👋\n\nНажмите кнопку 🚀 Start, чтобы открыть меню.",
        reply_markup=keyboard
    )


# Обработка нажатия кнопки 🚀 Start
@dp.message(F.text == "🚀 Start")
async def start_button(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lang_uz")]
    ])
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)


# Обработка выбора языка
@dp.callback_query(F.data == "lang_ru")
async def lang_ru(callback: types.CallbackQuery):
    await callback.message.answer("Вы выбрали 🇷🇺 Русский язык!")
    await callback.answer()

@dp.callback_query(F.data == "lang_uz")
async def lang_uz(callback: types.CallbackQuery):
    await callback.message.answer("Siz 🇺🇿 O'zbek tilini tanladingiz!")
    await callback.answer()


# Тестовый хэндлер — чтобы видеть, что бот получает
@dp.message()
async def debug_all(message: types.Message):
    print("Получено сообщение:", message.text)


async def run_bot():
    logging.info("🚀 Бот запущен...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
