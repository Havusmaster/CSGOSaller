import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import BOT_TOKEN

# 🌐 Настройки для Render
WEBHOOK_HOST = "https://csgosaller-1.onrender.com"  # Замени на свой Render-домен
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# 🔧 Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


# === /start команда ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Start")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Добро пожаловать! 👋\n\nНажмите кнопку 🚀 Start, чтобы продолжить.",
        reply_markup=keyboard
    )


# === Нажатие кнопки “🚀 Start” ===
@dp.message(F.text == "🚀 Start")
async def handle_start_button(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="O'zbek 🇺🇿", callback_data="lang_uz")]
        ]
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)


# === Язык: Русский ===
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


# === Язык: Узбекский ===
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


# === Кнопка “Магазин” ===
@dp.callback_query(F.data == "open_shop")
async def open_shop(callback: types.CallbackQuery):
    await callback.message.answer("🛍 Здесь будет магазин. (Позже можно добавить товары или ссылки)")
    await callback.answer()


# === Настройки Webhook ===
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("🛑 Webhook удалён и бот завершил работу.")


# === Обработчик webhook-запросов ===
async def handle_webhook(request):
    try:
        update = await request.json()
        await dp.feed_webhook_update(bot, update)
    except Exception as e:
        logging.error(f"Ошибка обработки webhook: {e}")
    return web.Response()


# === Создание aiohttp-приложения ===
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)


# === Функция для запуска (используется в bot.py) ===
async def run_bot():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=10000)
    logging.info("🚀 Telegram-бот запущен через webhook на порту 10000.")
    await site.start()
    await asyncio.Event().wait()  # держим бота активным
