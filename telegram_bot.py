import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# /start — показывает кнопку “🚀 Start”
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="🚀 Start")]
        ]
    )
    await message.answer(
        "Добро пожаловать! 👋\n\nНажмите кнопку 🚀 Start, чтобы продолжить.",
        reply_markup=keyboard
    )


# Обработка нажатия кнопки “🚀 Start”
@dp.message(F.text == "🚀 Start")
async def handle_start_button(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lang_uz")]
        ]
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)


# Обработка выбора языка — РУССКИЙ
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


# Обработка выбора языка — УЗБЕКСКИЙ
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


# Кнопка магазина (пример)
@dp.callback_query(F.data == "open_shop")
async def open_shop(callback: types.CallbackQuery):
    await callback.message.answer("🛍 Здесь будет магазин. (Позже можно добавить товары или ссылки)")
    await callback.answer()


# 🚀 Основная функция запуска
async def run_bot():
    logging.info("🚀 Запуск Telegram-бота...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("✅ Webhook отключён и старые апдейты очищены.")

        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run_bot())
