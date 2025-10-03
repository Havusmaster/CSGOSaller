import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from config import BOT_TOKEN, BOT_USERNAME

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

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
    lang = 'ru'
    if message.from_user.language_code == 'uz':
        lang = 'uz'

    welcome_url = f"https://csgosaller-1.onrender.com/?user_id={user_id}&lang={lang}&show_welcome=true"
    welcome_message = (
        "Добро пожаловать в CSGO Saller!" if lang == 'ru' else
        "CSGO Saller’ga xush kelibsiz!"
    )

    await message.answer(
        f"{welcome_message}\n"
        f"Посетите наш сайт для покупки скинов и участия в аукционах:\n"
        f"{welcome_url}",
        disable_web_page_preview=True,
        reply_markup=start_kb   # показываем клавиатуру
    )
    logging.info(f"Sent /start response to user {user_id} with lang={lang}")


# ================= Обработка кнопки =================
@dp.message(F.text == "🚀 Start")
async def start_button(message: types.Message):
    await start_command(message)   # повторно вызываем /start


# ================= Запуск =================
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