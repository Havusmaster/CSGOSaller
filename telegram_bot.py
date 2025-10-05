import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import BOT_TOKEN

# Настройка логов
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Команда /start ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lang_uz")]
    ])
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)


# --- Обработка выбора языка ---
@dp.callback_query(F.data.startswith("lang_"))
async def handle_language_choice(callback: types.CallbackQuery):
    lang = callback.data.split('_')[1]
    user_id = callback.from_user.id

    # URL магазина (WebApp)
    shop_url = f"https://csgosaller-1.onrender.com/shop?user_id={user_id}&lang={lang}"

    # Текст приветствия
    welcome_text = (
        "👋 Добро пожаловать в *CSGO Saller!*\n\n"
        "Здесь вы можете купить скины, участвовать в аукционах и отслеживать свои покупки.\n\n"
        "👇 Нажмите кнопку ниже, чтобы открыть магазин."
        if lang == "ru" else
        "👋 CSGO Saller'ga xush kelibsiz!\n\n"
        "Bu yerda siz skinlar sotib olishingiz, auksionlarda qatnashishingiz va xaridlaringizni kuzatishingiz mumkin.\n\n"
        "👇 Do'konni ochish uchun quyidagi tugmani bosing."
    )

    # Кнопка WebApp
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Открыть магазин / Do'konni ochish", web_app=WebAppInfo(url=shop_url))]
    ])

    await callback.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=keyboard)
    logging.info(f"User {user_id} selected language {lang} and opened shop WebApp")


# --- Функция запуска бота ---
async def run_bot():
    """Функция запускается из bot.py в отдельном потоке"""
    try:
        logging.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot polling failed: {e}")
    finally:
        logging.info("Bot stopped. Closing session...")
        await dp.storage.close()
        await bot.session.close()
