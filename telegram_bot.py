import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN, BOT_USERNAME

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    # Default to Russian; could be enhanced to detect user language from Telegram
    lang = 'ru'
    # Check if user prefers Uzbek (e.g., based on Telegram language or stored preference)
    if message.from_user.language_code == 'uz':
        lang = 'uz'
    welcome_url = f"https://csgosaller-1.onrender.com/?user_id={user_id}&lang={lang}&show_welcome=true"
    welcome_message = (
        "Добро пожаловать в CSGO Saller!" if lang == 'ru' else
        "CSGO Saller’ga xush kelibsiz!"
    )
    await message.reply(
        f"{welcome_message}\n"
        f"Посетите наш сайт для покупки скинов и участия в аукционах:\n"
        f"{welcome_url}",
        disable_web_page_preview=True
    )
    logging.info(f"Sent /start response to user {user_id} with lang={lang}")

async def run_bot():
    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(run_bot())