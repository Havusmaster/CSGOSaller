import sqlite3
import logging
import time
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Конфигурация
BOT_USERNAME = "UzSaler"  # Имя бота без @
ADMIN_IDS = [1939282952, 5266027747]  # Список ID админов
ADMIN_USERNAME = "UzSaler"  # Имя админа без @ или ссылка на группу
DB_PATH = "auction_shop.db"

# Логирование
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

def main_kb(user_id=None):
    if user_id in ADMIN_IDS:
        return types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [
                types.KeyboardButton(
                    text="🛒 Магазин",
                    web_app=types.WebAppInfo(url=f"https://csgosaller-1.onrender.com/?user_id={user_id}")
                )
            ]
        ])
    else:
        return types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [
                types.KeyboardButton(
                    text="🛒 Магазин",
                    web_app=types.WebAppInfo(url="https://csgosaller-1.onrender.com/")
                )
            ]
        ])

async def start_bot(token):
    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start_cmd(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or f"ID{user_id}"
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("product_"):
            try:
                product_id = int(args[1].replace("product_", ""))
                logging.info(f"Обработка /start product_{product_id} для user_id: {user_id}, username: {username}")
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT name, description, price, quantity, float_value, trade_ban, type FROM products WHERE id=? AND sold=0 AND quantity>0', (product_id,))
                prod = c.fetchone()
                if prod:
                    float_text = f"Float: {prod[4]:.4f}" if prod[4] is not None and prod[6] == 'weapon' else "Float: N/A"
                    ban_text = "Trade Ban: Да" if prod[5] else "Trade Ban: Нет"
                    type_text = "Тип: Оружие" if prod[6] == 'weapon' else "Тип: Агент"
                    text = (f"📦 Товар: {prod[0]}\n"
                            f"📜 Описание: {prod[1]}\n"
                            f"💰 Цена: {prod[2]}₽\n"
                            f"📦 Количество: {prod[3]}\n"
                            f"🔢 {float_text}\n"
                            f"🚫 {ban_text}\n"
                            f"🎮 {type_text}\n\n"
                            f"Пожалуйста, отправьте вашу трейд-ссылку для покупки!")
                    admin_url = f"https://t.me/{ADMIN_USERNAME}" if not ADMIN_USERNAME.startswith('+') else f"https://t.me/{ADMIN_USERNAME}"
                    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
                        resize_keyboard=True,
                        keyboard=[
                            [types.KeyboardButton(text="🛒 Вернуться в магазин", web_app=types.WebAppInfo(url="https://csgosaller-1.onrender.com/shop"))]
                        ]
                    ))
                    user_link = f"@{username}" if message.from_user.username else f"https://t.me/+{user_id}"
                    admin_text = (f"🔔 Пользователь {user_link} заинтересован в товаре!\n"
                                  f"📦 Товар: {prod[0]} (ID: {product_id})\n"
                                  f"📜 Описание: {prod[1]}\n"
                                  f"💰 Цена: {prod[2]}₽\n"
                                  f"📦 Количество: {prod[3]}\n"
                                  f"🔢 {float_text}\n"
                                  f"🚫 {ban_text}\n"
                                  f"🎮 {type_text}\n"
                                  f"📊 Посмотреть в админ-панели: https://csgosaller-1.onrender.com/admin/product/{product_id}\n"
                                  f"Ожидается трейд-ссылка...")
                    for admin_id in ADMIN_IDS:
                        try:
                            await bot.send_message(admin_id, admin_text)
                            logging.info(f"Уведомление отправлено админу ID{admin_id} о продукте {product_id}")
                        except Exception as e:
                            logging.error(f"Ошибка отправки админу ID{admin_id}: {e}")
                    c.execute('INSERT OR REPLACE INTO pending_requests (user_id, product_id, timestamp) VALUES (?, ?, ?)',
                              (user_id, product_id, int(time.time())))
                    conn.commit()
                    logging.info(f"Пользователь {username} (ID{user_id}) запросил продукт {product_id}: {prod[0]}")
                else:
                    await message.answer("Товар не найден или недоступен.", reply_markup=main_kb(user_id))
                conn.close()
            except Exception as e:
                if 'conn' in locals():
                    conn.close()
                logging.error(f"Ошибка обработки /start product_{product_id}: {str(e)}")
                await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=main_kb(user_id))
        else:
            await message.answer("Добро пожаловать!", reply_markup=main_kb(user_id))

    @dp.message()
    async def handle_trade_link(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or f"ID{user_id}"
        text = message.text.strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT product_id FROM pending_requests WHERE user_id=? AND timestamp>?', (user_id, int(time.time()) - 300))
        request = c.fetchone()
        if request:
            product_id = request[0]
            if re.match(r'^https://steamcommunity\.com/tradeoffer/.*', text):
                c.execute('SELECT name, description, price, quantity, float_value, trade_ban, type FROM products WHERE id=?', (product_id,))
                prod = c.fetchone()
                if prod:
                    float_text = f"Float: {prod[4]:.4f}" if prod[4] is not None and prod[6] == 'weapon' else "Float: N/A"
                    ban_text = "Trade Ban: Да" if prod[5] else "Trade Ban: Нет"
                    type_text = "Тип: Оружие" if prod[6] == 'weapon' else "Тип: Агент"
                    user_link = f"@{username}" if message.from_user.username else f"https://t.me/+{user_id}"
                    admin_text = (f"🔔 Пользователь {user_link} отправил трейд-ссылку для товара!\n"
                                  f"📦 Товар: {prod[0]} (ID: {product_id})\n"
                                  f"📜 Описание: {prod[1]}\n"
                                  f"💰 Цена: {prod[2]}₽\n"
                                  f"📦 Количество: {prod[3]}\n"
                                  f"🔢 {float_text}\n"
                                  f"🚫 {ban_text}\n"
                                  f"🎮 {type_text}\n"
                                  f"📊 Посмотреть в админ-панели: https://csgosaller-1.onrender.com/admin/product/{product_id}\n"
                                  f"🔗 Трейд-ссылка: {text}")
                    for admin_id in ADMIN_IDS:
                        try:
                            await bot.send_message(admin_id, admin_text)
                            logging.info(f"Трейд-ссылка отправлена админу ID{admin_id} для продукта {product_id}")
                        except Exception as e:
                            logging.error(f"Ошибка отправки трейд-ссылки админу ID{admin_id}: {e}")
                    await message.answer("✅ Ваша трейд-ссылка отправлена администратору! Ожидайте ответа.", reply_markup=main_kb(user_id))
                    c.execute('DELETE FROM pending_requests WHERE user_id=? AND product_id=?', (user_id, product_id))
                    conn.commit()
                else:
                    await message.answer("Товар не найден. Попробуйте снова.", reply_markup=main_kb(user_id))
                    c.execute('DELETE FROM pending_requests WHERE user_id=? AND product_id=?', (user_id, product_id))
                    conn.commit()
            else:
                await message.answer("❌ Пожалуйста, отправьте действительную трейд-ссылку (например, https://steamcommunity.com/tradeoffer/...).", reply_markup=main_kb(user_id))
            conn.close()
        else:
            conn.close()

    async def notify_admins_auction(lot_id, lot_name, price, winner_id, float_value, trade_ban, lot_type):
        float_text = f"🔢 Float: {float_value:.4f}" if float_value is not None and lot_type == 'weapon' else "🔢 Float: N/A"
        ban_text = "🚫 Trade Ban: Да" if trade_ban else "🚫 Trade Ban: Нет"
        type_text = "🎮 Тип: Оружие" if lot_type == 'weapon' else "🎮 Тип: Агент"
        winner_text = f"👤 Победитель: ID{winner_id}" if winner_id else "👤 Победитель: Нет ставок"
        text = (f"🏆 Аукцион завершён!\n"
                f"📦 Лот: {lot_name} (ID: {lot_id})\n"
                f"💰 Финальная цена: {price}₽\n"
                f"{winner_text}\n"
                f"{float_text}\n"
                f"{ban_text}\n"
                f"{type_text}")
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, text)
                logging.info(f"Уведомление об аукционе отправлено админу ID{admin_id}: {lot_name} (ID: {lot_id})")
            except Exception as e:
                logging.error(f"Ошибка отправки админу ID{admin_id}: {e}")

    # Запуск polling
    await dp.start_polling(bot)