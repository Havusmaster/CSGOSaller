
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, BOT_USERNAME

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

try:
    bot = Bot(token=BOT_TOKEN)
except Exception as e:
    logging.error(f"Failed to initialize Bot: {e}")
    raise

dp = Dispatcher(storage=MemoryStorage())

async def notify_admins_product(product_id, product_name, description, price, quantity, float_value, trade_ban, product_type, user_id, trade_link, product_link):
    message = (
        f"New purchase request!\n"
        f"Product ID: {product_id}\n"
        f"Name: {product_name}\n"
        f"Description: {description}\n"
        f"Price: {price}₽\n"
        f"Quantity: {quantity}\n"
        f"Float: {float_value if float_value is not None else 'N/A'}\n"
        f"Trade Ban: {'Yes' if trade_ban else 'No'}\n"
        f"Type: {product_type}\n"
        f"User ID: {user_id}\n"
        f"Trade Link: {trade_link}\n"
        f"Product Link: {product_link}"
    )
    await bot.send_message(chat_id=user_id, text=message)

async def notify_admins_auction(lot_id, lot_name, description, current_price, step, end_time, float_value, trade_ban, product_type, user_id, product_link):
    message = (
        f"New auction bid!\n"
        f"Lot ID: {lot_id}\n"
        f"Name: {lot_name}\n"
        f"Description: {description}\n"
        f"Current Price: {current_price}₽\n"
        f"Step: {step}₽\n"
        f"End Time: {end_time if end_time else 'No limit'}\n"
        f"Float: {float_value if float_value is not None else 'N/A'}\n"
        f"Trade Ban: {'Yes' if trade_ban else 'No'}\n"
        f"Type: {product_type}\n"
        f"User ID: {user_id}\n"
        f"Product Link: {product_link}"
    )
    await bot.send_message(chat_id=user_id, text=message)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="O'zbek", callback_data="lang_uz")]
    ])
    await message.reply("Выберите язык / Tilni tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda query: query.data.startswith('lang_'))
async def handle_language_choice(callback: types.CallbackQuery):
    lang = callback.data.split('_')[1]
    user_id = callback.from_user.id
    shop_url = f"https://csgosaller-1.onrender.com/shop?user_id={user_id}&lang={lang}"
    welcome_message = (
        "Добро пожаловать в CSGO Saller! Откройте магазин:" if lang == 'ru' else
        "CSGO Saller'ga xush kelibsiz! Do'konni oching:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть магазин / Do'konni ochish", url=shop_url)]
    ])
    await callback.message.edit_text(welcome_message, reply_markup=keyboard)
    logging.info(f"User {user_id} selected lang {lang} and received shop URL")

async def run_bot():
    try:
        logging.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot polling failed: {e}")
        raise
    finally:
        logging.info("Closing bot storage and session...")
        await dp.storage.close()
        await bot.session.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(run_bot())