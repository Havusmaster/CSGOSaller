import asyncio
import logging
import time
import re
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppData
from config import BOT_TOKEN, ADMIN_IDS, ADMIN_USERNAME, BOT_USERNAME
from database import DB_PATH
import sqlite3

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def main_kb(user_id=None):
    if user_id in ADMIN_IDS:
        return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [
                KeyboardButton(
                    text="🛒 Магазин",
                    web_app=WebAppInfo(url=f"https://csgosaller-1.onrender.com/?user_id={user_id}")
                )
            ]
        ])
    else:
        return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [
                KeyboardButton(
                    text="🛒 Магазин",
                    web_app=WebAppInfo(url="https://csgosaller-1.onrender.com/")
                )
            ]
        ])

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
                product_link = f"https://csgosaller-1.onrender.com/product/{product_id}"
                text = (f"📦 Товар: {prod[0]}\n"
                        f"📜 Описание: {prod[1]}\n"
                        f"💰 Цена: {prod[2]}₽\n"
                        f"📦 Количество: {prod[3]}\n"
                        f"🔢 {float_text}\n"
                        f"🚫 {ban_text}\n"
                        f"🎮 {type_text}\n"
                        f"🔗 Ссылка на товар: {product_link}\n\n"
                        f"Пожалуйста, отправьте вашу трейд-ссылку для покупки!")
                admin_url = f"https://t.me/{ADMIN_USERNAME}" if not ADMIN_USERNAME.startswith('+') else f"https://t.me/{ADMIN_USERNAME}"
                await message.answer(text, reply_markup=ReplyKeyboardMarkup(
                    resize_keyboard=True,
                    keyboard=[
                        [KeyboardButton(text="🛒 Вернуться в магазин", web_app=WebAppInfo(url="https://csgosaller-1.onrender.com/shop"))]
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
                              f"📊 Админ-панель: https://csgosaller-1.onrender.com/admin/product/{product_id}\n"
                              f"🔗 Трейд-ссылка: Ожидается...")
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
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"ID{user_id}"
    
    if message.web_app_data:
        try:
            data = json.loads(message.web_app_data.data)
            action = data.get('action')
            product_id = data.get('product_id')
            logging.info(f"Получены данные WebApp от user_id: {user_id}, username: {username}, action: {action}, product_id: {product_id}")
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            if action == 'buy':
                product_link = data.get('product_link')
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
                            f"🎮 {type_text}\n"
                            f"🔗 Ссылка на товар: {product_link}\n\n"
                            f"Пожалуйста, отправьте вашу трейд-ссылку для покупки!")
                    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
                        resize_keyboard=True,
                        keyboard=[
                            [KeyboardButton(text="🛒 Вернуться в магазин", web_app=WebAppInfo(url="https://csgosaller-1.onrender.com/shop"))]
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
                                  f"📊 Админ-панель: https://csgosaller-1.onrender.com/admin/product/{product_id}\n"
                                  f"🔗 Трейд-ссылка: Ожидается...")
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
                return
            
            conn.close()
            await message.answer("Неизвестное действие.", reply_markup=main_kb(user_id))
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            logging.error(f"Ошибка обработки WebApp данных: {str(e)}")
            await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=main_kb(user_id))
        return

    text = message.text.strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT product_id FROM pending_requests WHERE user_id=? AND timestamp>?', (user_id, int(time.time()) - 300))
    request = c.fetchone()
    if request:
        product_id = request[0]
        product_link_match = re.search(r'https://csgosaller-1\.onrender\.com/product/\d+', text)
        trade_link_match = re.search(r'https://steamcommunity\.com/tradeoffer/.*', text)
        product_link = product_link_match.group(0) if product_link_match else None
        trade_link = trade_link_match.group(0) if trade_link_match else None
        c.execute('SELECT name, description, price, quantity, float_value, trade_ban, type FROM products WHERE id=?', (product_id,))
        prod = c.fetchone()
        if prod:
            float_text = f"Float: {prod[4]:.4f}" if prod[4] is not None and prod[6] == 'weapon' else "Float: N/A"
            ban_text = "Trade Ban: Да" if prod[5] else "Trade Ban: Нет"
            type_text = "Тип: Оружие" if prod[6] == 'weapon' else "Тип: Агент"
            user_link = f"@{username}" if message.from_user.username else f"https://t.me/+{user_id}"
            user_text = (f"✅ Вы отправили трейд-ссылку для товара:\n"
                         f"📦 Товар: {prod[0]} (ID: {product_id})\n"
                         f"📜 Описание: {prod[1]}\n"
                         f"💰 Цена: {prod[2]}₽\n"
                         f"📦 Количество: {prod[3]}\n"
                         f"🔢 {float_text}\n"
                         f"🚫 {ban_text}\n"
                         f"🎮 {type_text}\n"
                         f"🔗 Трейд-ссылка: {trade_link if trade_link else 'Не предоставлена'}\n"
                         f"🔗 Ссылка на товар: {product_link if product_link else 'Не предоставлена'}\n\n"
                         f"Ожидайте ответа администратора!")
            await message.answer(user_text, reply_markup=main_kb(user_id))
            admin_text = (f"🔔 Пользователь {user_link} отправил трейд-ссылку для товара!\n"
                          f"📦 Товар: {prod[0]} (ID: {product_id})\n"
                          f"📜 Описание: {prod[1]}\n"
                          f"💰 Цена: {prod[2]}₽\n"
                          f"📦 Количество: {prod[3]}\n"
                          f"🔢 {float_text}\n"
                          f"🚫 {ban_text}\n"
                          f"🎮 {type_text}\n"
                          f"📊 Админ-панель: https://csgosaller-1.onrender.com/admin/product/{product_id}\n"
                          f"🔗 Трейд-ссылка: {trade_link if trade_link else 'Не предоставлена'}\n"
                          f"🔗 Ссылка на товар: {product_link if product_link else 'Не предоставлена'}")
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, admin_text)
                    logging.info(f"Трейд-ссылка и ссылка на товар отправлены админу ID{admin_id} для продукта {product_id}")
                except Exception as e:
                    logging.error(f"Ошибка отправки админу ID{admin_id}: {e}")
            c.execute('DELETE FROM pending_requests WHERE user_id=? AND product_id=?', (user_id, product_id))
            conn.commit()
        else:
            await message.answer("Товар не найден. Попробуйте снова.", reply_markup=main_kb(user_id))
            c.execute('DELETE FROM pending_requests WHERE user_id=? AND product_id=?', (user_id, product_id))
            conn.commit()
    else:
        await message.answer("❌ Пожалуйста, отправьте действительную трейд-ссылку (например, https://steamcommunity.com/tradeoffer/...) и ссылку на товар (https://csgosaller-1.onrender.com/product/...).", reply_markup=main_kb(user_id))
    conn.close()

async def notify_admins_product(product_id, product_name, description, price, quantity, float_value, trade_ban, product_type, user_id, trade_link=None, product_link=None):
    float_text = f"🔢 Float: {float_value:.4f}" if float_value is not None and product_type == 'weapon' else "🔢 Float: N/A"
    ban_text = "🚫 Trade Ban: Да" if trade_ban else "🚫 Trade Ban: Нет"
    type_text = "🎮 Тип: Оружие" if product_type == 'weapon' else "🎮 Тип: Агент"
    user_link = f"ID{user_id}"
    trade_text = f"🔗 Трейд-ссылка: {trade_link}" if trade_link else "🔗 Трейд-ссылка: Ожидается"
    product_link_text = f"🔗 Ссылка на товар: {product_link}" if product_link else "🔗 Ссылка на товар: Ожидается"
    admin_text = (f"🔔 Пользователь {user_link} хочет купить товар!\n"
                  f"📦 Товар: {product_name} (ID: {product_id})\n"
                  f"📜 Описание: {description}\n"
                  f"💰 Цена: {price}₽\n"
                  f"📦 Количество: {quantity}\n"
                  f"🔢 {float_text}\n"
                  f"🚫 {ban_text}\n"
                  f"🎮 {type_text}\n"
                  f"📊 Админ-панель: https://csgosaller-1.onrender.com/admin/product/{product_id}\n"
                  f"{trade_text}\n"
                  f"{product_link_text}")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
            logging.info(f"Уведомление о покупке отправлено админу ID{admin_id}: {product_name} (ID: {product_id})")
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления о покупке админу ID{admin_id}: {e}")

def notify_admins_auction(lot_id, lot_name, price, winner_id, float_value, trade_ban, lot_type):
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot.send_message(admin_id, text))
            loop.close()
            logging.info(f"Уведомление об аукционе отправлено админу ID{admin_id}: {lot_name} (ID: {lot_id})")
        except Exception as e:
            logging.error(f"Ошибка отправки админу ID{admin_id}: {e}")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    dp.run_polling(bot)