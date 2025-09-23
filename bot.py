# -*- coding: utf-8 -*-
"""
README
=======

Требования:
- Python 3.10+
- pip install aiogram flask

Запуск:
- python bot.py

WebApp:
- Откройте Telegram-бота, нажмите кнопку "Открыть магазин/аукцион".

Конфиг:
- BOT_TOKEN = "ВАШ_ТОКЕН"
- ADMIN_IDS = [id1, id2]
- ADMIN_USERNAME = "ВАШ_АДМИН_ИМЯ"
- BOT_USERNAME = "ВАШ_БОТ_ИМЯ"

"""

# =====================
# Конфиг
# =====================
BOT_TOKEN = "7504123410:AAEznGqRafbyrBx2e34HzsxztWV201HRMxE"  # Замените на реальный токен
ADMIN_IDS = [1939282952, 5266027747]
ADMIN_USERNAME = "@sarv4you"  # Замените на реальное имя администратора без @ (например, AdminUser для @AdminUser)
BOT_USERNAME = "CSGOSallerBot"  # Замените на реальное имя бота без @ (например, CSGOSallerBot)

# =====================
# Импорт библиотек
# =====================
import os
import sqlite3
import logging
import time
from flask import Flask, render_template_string, request, redirect, url_for, session
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
import multiprocessing
import werkzeug
from threading import Thread

# =====================
# Логирование
# =====================
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

# =====================
# Инициализация базы данных
# =====================
DB_PATH = "auction_shop.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price INTEGER NOT NULL,
        quantity INTEGER,
        sold INTEGER DEFAULT 0,
        image TEXT,
        float_value REAL,
        trade_ban INTEGER DEFAULT 0,
        type TEXT NOT NULL
    )""")
    try:
        c.execute("ALTER TABLE products ADD COLUMN float_value REAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN trade_ban INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN type TEXT NOT NULL DEFAULT 'weapon'")
    except sqlite3.OperationalError:
        pass
    c.execute("""
    CREATE TABLE IF NOT EXISTS lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        start_price INTEGER NOT NULL,
        step INTEGER,
        end_time INTEGER,
        current_price INTEGER,
        winner_id INTEGER,
        active INTEGER DEFAULT 1,
        image TEXT,
        float_value REAL,
        trade_ban INTEGER DEFAULT 0,
        type TEXT NOT NULL DEFAULT 'weapon'
    )""")
    try:
        c.execute("ALTER TABLE lots ADD COLUMN float_value REAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE lots ADD COLUMN trade_ban INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE lots ADD COLUMN type TEXT NOT NULL DEFAULT 'weapon'")
    except sqlite3.OperationalError:
        pass
    c.execute("""
    CREATE TABLE IF NOT EXISTS bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER,
        user_id INTEGER,
        amount INTEGER,
        time INTEGER
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        name TEXT,
        price INTEGER,
        buyer TEXT,
        time INTEGER
    )""")
    conn.commit()
    conn.close()
init_db()

# =====================
# Flask WebApp
# =====================
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['DEBUG'] = True
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Tailwind CSS и JavaScript
TAILWIND = """
<script src="https://cdn.tailwindcss.com"></script>
<style>
body { background: linear-gradient(135deg, #1a1a1a, #2a2a2a); min-height: 100vh; }
.card { transition: transform 0.3s ease, box-shadow 0.3s ease; }
.card:hover { transform: scale(1.03); box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
.btn { transition: all 0.2s ease; }
.btn:hover { transform: scale(1.05); }
input, select, textarea { transition: border-color 0.3s ease; }
input:focus, select:focus, textarea:focus { border-color: #f97316 !important; outline: none; }
</style>
<script>
function toggleFloatField(selectId, floatId) {
  const select = document.getElementById(selectId);
  const floatField = document.getElementById(floatId);
  floatField.style.display = select.value === 'weapon' ? 'block' : 'none';
}
</script>
"""

# =====================
# Telegram Bot
# =====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("product_"):
        try:
            product_id = int(args[1].replace("product_", ""))
            logging.info(f"Обработка /start product_{product_id} для user_id: {user_id}")
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT name, description, price, quantity, float_value, trade_ban, type FROM products WHERE id=? AND sold=0 AND quantity>0', (product_id,))
            prod = c.fetchone()
            conn.close()
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
                        f"Напишите администратору для покупки!")
                await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
                    resize_keyboard=True,
                    keyboard=[
                        [types.KeyboardButton(text="📩 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")],
                        [types.KeyboardButton(text="🛒 Вернуться в магазин", web_app=types.WebAppInfo(url="https://csgosaller-1.onrender.com/shop"))]
                    ]
                ))
                # Уведомляем админов
                admin_text = (f"🔔 Пользователь ID{user_id} заинтересован в товаре!\n"
                              f"📦 Товар: {prod[0]}\n"
                              f"📜 Описание: {prod[1]}\n"
                              f"💰 Цена: {prod[2]}₽\n"
                              f"📦 Количество: {prod[3]}\n"
                              f"🔢 {float_text}\n"
                              f"🚫 {ban_text}\n"
                              f"🎮 {type_text}")
                for admin_id in ADMIN_IDS:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(bot.send_message(admin_id, admin_text))
                        loop.close()
                    except Exception as e:
                        logging.error(f"Ошибка отправки админу {admin_id}: {e}")
                logging.info(f"Пользователь ID{user_id} запросил продукт {product_id}: {prod[0]}")
            else:
                await message.answer("Товар не найден или недоступен.", reply_markup=main_kb(user_id))
        except Exception as e:
            logging.error(f"Ошибка обработки /start product_{product_id}: {str(e)}")
            await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=main_kb(user_id))
    else:
        await message.answer("Добро пожаловать!", reply_markup=main_kb(user_id))

# =====================
# Уведомления админам
# =====================
def notify_admins_purchase(product, price, buyer, description, quantity, float_value, trade_ban, item_type):
    float_text = f"Float: {float_value:.4f}" if float_value is not None and item_type == 'weapon' else "Float: N/A"
    ban_text = "Trade Ban: Да" if trade_ban else "Trade Ban: Нет"
    type_text = "Тип: Оружие" if item_type == 'weapon' else "Тип: Агент"
    text = f"\n🛒 Новая заявка на покупку!\n📦 Товар: {product}\n📜 Описание: {description}\n💰 Цена: {price}₽\n📦 Количество: {quantity}\n🔢 {float_text}\n🚫 {ban_text}\n🎮 {type_text}\n👤 Покупатель: {buyer}"
    for admin_id in ADMIN_IDS:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot.send_message(admin_id, text))
            loop.close()
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    logging.info(f"Покупка: {product}, {price}, {buyer}, {description}, {quantity}, {float_text}, {ban_text}, {type_text}")

def notify_admins_auction(lot, price, winner):
    text = f"\n🏆 Аукцион завершён!\n📦 Лот: {lot}\n💰 Цена: {price}\n👤 Победитель: {winner}"
    for admin_id in ADMIN_IDS:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot.send_message(admin_id, text))
            loop.close()
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    logging.info(f"Аукцион: {lot}, {price}, {winner}")

# =====================
# Flask маршруты
# =====================
def is_admin():
    user_id = session.get('user_id')
    logging.info(f"Checking is_admin for user_id: {user_id}, ADMIN_IDS: {ADMIN_IDS}")
    return user_id in ADMIN_IDS

@app.route('/login', methods=['GET', 'POST'])
def login():
    user_id = session.get('user_id', None)
    logging.info(f"Login route: user_id={user_id}")
    if user_id in ADMIN_IDS:
        logging.info("User is admin, redirecting to /admin/products")
        return redirect(url_for('admin_products'))
    logging.info("User not admin, redirecting to /")
    return redirect(url_for('index'))

@app.route('/')
def index():
    user_id = session.get('user_id', None)
    logging.info(f"Index route: session user_id={user_id}, query user_id={request.args.get('user_id', None)}")
    if not user_id:
        user_id = request.args.get('user_id', None)
        if user_id:
            try:
                user_id = int(user_id)
                session['user_id'] = user_id
                logging.info(f"Set session user_id: {user_id}")
            except:
                user_id = None
                logging.error("Failed to parse user_id from query")
    html = TAILWIND + """
    <div class="container mx-auto pt-10 pb-10 px-4 text-center">
      <h2 class="text-3xl font-bold text-orange-500 mb-6">Добро пожаловать!</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <a href="/shop" class="bg-green-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-green-700 btn">🛒 Магазин</a>
        <a href="/auction" class="bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 btn">🏆 Аукцион</a>
      </div>
    """
    if user_id in ADMIN_IDS:
        html += '<a href="/admin/products" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn">🔑 Админ-панель</a>'
    html += """
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
        <a href="/shop" class="text-gray-300 hover:text-orange-500">🛒 Магазин</a>
        <a href="/auction" class="text-gray-300 hover:text-orange-500">🏆 Аукцион</a>
      </div>
    </div>
    """
    return html

@app.route('/shop')
def shop():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products WHERE sold=0 AND quantity>0')
    products = c.fetchall()
    conn.close()
    html = TAILWIND + """
    <div class="container mx-auto pt-10 pb-10 px-4">
      <h2 class="text-3xl font-bold text-green-500 mb-6">🛒 Магазин</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
    """
    for p in products:
        img_html = f'<img src="/static/images/{p[6]}" class="mb-4 w-full rounded-lg object-cover" style="max-height:180px;" alt="{p[1]}">' if p[6] else ""
        float_text = f"Float: {p[7]:.4f}" if p[7] is not None and p[9] == 'weapon' else ""
        ban_text = "Trade Ban: Да" if p[8] else "Trade Ban: Нет"
        type_text = "Тип: Оружие" if p[9] == 'weapon' else "Тип: Агент"
        html += f"""
        <div class="bg-gray-800 rounded-lg p-4 card">
          {img_html}
          <h5 class="text-xl font-bold text-green-500">{p[1]}</h5>
          <p class="text-gray-300">{p[2]}</p>
          <p class="mt-2"><span class="bg-yellow-500 text-black px-2 py-1 rounded">💰 {p[3]}₽</span> <span class="bg-blue-500 text-white px-2 py-1 rounded">📦 Осталось: {p[4]}</span></p>
          <p class="mt-2 text-sm text-gray-400">{float_text} {'' if not float_text else ' | '}{ban_text} | {type_text}</p>
          <a href="https://t.me/{BOT_USERNAME}?start=product_{p[0]}" class="bg-green-600 text-white w-full py-2 rounded-lg hover:bg-green-700 btn mt-4 block text-center">📩 Написать админу</a>
        </div>
        """
    html += """
      </div>
      <hr class="border-gray-700 my-6">
      <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn w-full text-center">⬅️ Назад</a>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
        <a href="/" class="text-gray-300 hover:text-orange-500">🏠 Главная</a>
        <a href="/auction" class="text-gray-300 hover:text-orange-500">🏆 Аукцион</a>
      </div>
    </div>
    """
    return html

@app.route('/buy', methods=['POST'])
def buy():
    logging.info("Маршрут /buy вызван")
    user_id = session.get('user_id', None)
    buyer = "Гость" if not user_id else f"ID{user_id}"
    logging.info(f"Покупатель: {buyer}, user_id: {user_id}")
    
    try:
        product_id = request.form.get('product_id')
        logging.info(f"Получен product_id: {product_id}")
        if not product_id:
            logging.error("product_id отсутствует в форме")
            return TAILWIND + '<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-red-600 text-white p-4 rounded-lg">Ошибка: ID товара не указан.</div><a href="/shop" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'
        
        pid = int(product_id)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT name, price, quantity, description, float_value, trade_ban, type FROM products WHERE id=? AND sold=0', (pid,))
        prod = c.fetchone()
        logging.info(f"Результат запроса к products: {prod}")
        
        if not prod or prod[2] < 1:
            conn.close()
            logging.error(f"Товар недоступен: id={pid}, prod={prod}")
            return TAILWIND + '<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-red-600 text-white p-4 rounded-lg">Товар недоступен.</div><a href="/shop" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'
        
        c.execute('UPDATE products SET quantity=quantity-1 WHERE id=?', (pid,))
        if prod[2] == 1:
            c.execute('UPDATE products SET sold=1 WHERE id=?', (pid,))
        c.execute('INSERT INTO purchases (product_id, name, price, buyer, time) VALUES (?, ?, ?, ?, ?)',
                  (pid, prod[0], prod[1], buyer, int(time.time())))
        conn.commit()
        conn.close()
        notify_admins_purchase(prod[0], prod[1], buyer, prod[3], prod[2], prod[4], prod[5], prod[6])
        logging.info(f"Покупка успешна: {prod[0]}, {prod[1]}, {buyer}, {prod[3]}, {prod[2]}, Float: {prod[4]}, Trade Ban: {prod[5]}, Type: {prod[6]}")
        return TAILWIND + '<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-green-600 text-white p-4 rounded-lg">✅ Заявка на покупку отправлена администратору!</div><a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'
    
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"Ошибка в /buy: {str(e)}")
        return TAILWIND + f'<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-red-600 text-white p-4 rounded-lg">Ошибка: {str(e)}</div><a href="/shop" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'

@app.route('/auction', methods=['GET'])
@app.route('/auction/', methods=['GET'])
def auction():
    logging.info("Маршрут /auction вызван")
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info(f"Подключение к базе данных: {DB_PATH}")
        c = conn.cursor()
        c.execute('SELECT id, name, description, current_price, end_time, step, active, image, float_value, trade_ban, type FROM lots WHERE active=1')
        lots = c.fetchall()
        logging.info(f"Получено лотов: {len(lots)}")
        conn.close()
        html = TAILWIND + """
        <div class="container mx-auto pt-10 pb-10 px-4">
          <h2 class="text-3xl font-bold text-blue-500 mb-6">🏆 Аукцион</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
        """
        for l in lots:
            time_left = max(0, l[4] - int(time.time()))
            img_html = f'<img src="/static/images/{l[7]}" class="mb-4 w-full rounded-lg object-cover" style="max-height:180px;" alt="{l[1]}">' if l[7] else ""
            float_text = f"Float: {l[8]:.4f}" if l[8] is not None and l[10] == 'weapon' else ""
            ban_text = "Trade Ban: Да" if l[9] else "Trade Ban: Нет"
            type_text = "Тип: Оружие" if l[10] == 'weapon' else "Тип: Агент"
            html += f"""
            <div class="bg-gray-800 rounded-lg p-4 card">
              {img_html}
              <h5 class="text-xl font-bold text-blue-500">{l[1]}</h5>
              <p class="text-gray-300">{l[2]}</p>
              <p class="mt-2"><span class="bg-yellow-500 text-black px-2 py-1 rounded">💰 Текущая ставка: {l[3]}₽</span></p>
              <p class="mt-2"><span class="bg-gray-600 text-white px-2 py-1 rounded">⏳ До конца: {time_left//60} мин {time_left%60} сек</span></p>
              <p class="mt-2 text-sm text-gray-400">{float_text} {'' if not float_text else ' | '}{ban_text} | {type_text}</p>
              <form method="post" action="/bid" class="mt-4">
                <input type="hidden" name="lot_id" value="{l[0]}">
                <input type="hidden" name="step" value="{l[5]}">
                <button type="submit" class="bg-yellow-500 text-black w-full py-2 rounded-lg hover:bg-yellow-600 btn">🔼 Ставка +{l[5]}₽</button>
              </form>
              <form method="post" action="/bid_custom" class="mt-2">
                <input type="hidden" name="lot_id" value="{l[0]}">
                <input type="number" name="amount" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600 mb-2" placeholder="Ваша ставка (₽)" min="{l[3]+l[5]}" required>
                <button type="submit" class="bg-blue-600 text-white w-full py-2 rounded-lg hover:bg-blue-700 btn">💸 Ввести сумму</button>
              </form>
            </div>
            """
        html += """
          </div>
          <hr class="border-gray-700 my-6">
          <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn w-full text-center">⬅️ Назад</a>
          <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
            <a href="/" class="text-gray-300 hover:text-orange-500">🏠 Главная</a>
            <a href="/shop" class="text-gray-300 hover:text-orange-500">🛒 Магазин</a>
          </div>
        </div>
        """
        return html
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"Ошибка в /auction: {str(e)}")
        return TAILWIND + f'<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-red-600 text-white p-4 rounded-lg">Ошибка: {str(e)}</div><a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'

@app.route('/bid', methods=['POST'])
def bid():
    user_id = session.get('user_id', None)
    if not user_id:
        return redirect('/login')
    lot_id = int(request.form['lot_id'])
    step = int(request.form['step'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT current_price, end_time FROM lots WHERE id=? AND active=1', (lot_id,))
    lot = c.fetchone()
    if not lot:
        conn.close()
        return TAILWIND + '<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-red-600 text-white p-4 rounded-lg">Лот недоступен.</div><a href="/auction" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'
    new_price = lot[0] + step
    c.execute('UPDATE lots SET current_price=? WHERE id=?', (new_price, lot_id))
    c.execute('INSERT INTO bids (lot_id, user_id, amount, time) VALUES (?, ?, ?, ?)', (lot_id, user_id, new_price, int(time.time())))
    conn.commit()
    conn.close()
    logging.info(f"Ставка: Лот {lot_id}, {new_price}, {user_id}")
    return redirect('/auction')

@app.route('/bid_custom', methods=['POST'])
def bid_custom():
    user_id = session.get('user_id', None)
    if not user_id:
        return redirect('/login')
    lot_id = int(request.form['lot_id'])
    amount = int(request.form['amount'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT current_price, end_time, step FROM lots WHERE id=? AND active=1', (lot_id,))
    lot = c.fetchone()
    if not lot or amount < lot[0] + lot[2]:
        conn.close()
        return TAILWIND + '<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-red-600 text-white p-4 rounded-lg">Сумма слишком мала.</div><a href="/auction" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'
    c.execute('UPDATE lots SET current_price=? WHERE id=?', (amount, lot_id))
    c.execute('INSERT INTO bids (lot_id, user_id, amount, time) VALUES (?, ?, ?, ?)', (lot_id, user_id, amount, int(time.time())))
    conn.commit()
    conn.close()
    logging.info(f"Ставка: Лот {lot_id}, {amount}, {user_id}")
    return redirect('/auction')

@app.route('/admin/products')
def admin_products():
    if not is_admin():
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products')
    products = c.fetchall()
    conn.close()
    html = TAILWIND + """
    <div class="container mx-auto pt-10 pb-10 px-4">
      <h2 class="text-3xl font-bold text-gray-300 mb-6">📦 Товары</h2>
      <div class="overflow-x-auto">
        <table class="w-full bg-gray-800 text-gray-300 rounded-lg">
          <thead><tr class="bg-gray-900"><th class="p-3">Фото</th><th class="p-3">Название</th><th class="p-3">Описание</th><th class="p-3">Цена</th><th class="p-3">Кол-во</th><th class="p-3">Float</th><th class="p-3">Trade Ban</th><th class="p-3">Тип</th><th class="p-3">Статус</th><th class="p-3">Действия</th></tr></thead>
          <tbody>
    """
    for p in products:
        status = '✅ Продан' if p[5] else '🟢 В продаже'
        float_text = f"{p[7]:.4f}" if p[7] is not None and p[9] == 'weapon' else "N/A"
        ban_text = 'Да' if p[8] else 'Нет'
        type_text = 'Оружие' if p[9] == 'weapon' else 'Агент'
        img_html = f'<img src="/static/images/{p[6]}" class="w-16 h-16 rounded-lg object-cover" alt="{p[1]}">' if p[6] else ""
        html += f"""
        <tr class="border-b border-gray-700">
          <td class="p-3">{img_html}</td>
          <td class="p-3">{p[1]}</td>
          <td class="p-3">{p[2]}</td>
          <td class="p-3">{p[3]}₽</td>
          <td class="p-3">{p[4]}</td>
          <td class="p-3">{float_text}</td>
          <td class="p-3">{ban_text}</td>
          <td class="p-3">{type_text}</td>
          <td class="p-3">{status}</td>
          <td class="p-3">
            <div class="flex flex-col gap-2">
              {'' if p[5] else f'<form method="post" action="/mark_sold"><input type="hidden" name="product_id" value="{p[0]}"><button class="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 btn text-sm">✅ Продан</button></form>'}
              {'' if not p[5] else f'<form method="post" action="/mark_unsold"><input type="hidden" name="product_id" value="{p[0]}"><button class="bg-yellow-500 text-black px-3 py-1 rounded hover:bg-yellow-600 btn text-sm">❌ Не продан</button></form>'}
              <form method="post" action="/delete_product"><input type="hidden" name="product_id" value="{p[0]}"><button class="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 btn text-sm">🗑️ Удалить</button></form>
            </div>
          </td>
        </tr>
        """
    html += """
          </tbody>
        </table>
      </div>
      <hr class="border-gray-700 my-6">
      <h2 class="text-3xl font-bold text-green-500 mb-6">➕ Добавить товар</h2>
      <form method="post" action="/add_product" class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4" enctype="multipart/form-data">
        <div>
          <input name="name" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Название оружия или агента" required>
        </div>
        <div>
          <textarea name="description" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Описание (например, скин, редкость)" rows="3" required></textarea>
        </div>
        <div>
          <input name="price" type="number" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Цена в рублях" required>
        </div>
        <div>
          <input name="quantity" type="number" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Количество" required>
        </div>
        <div>
          <select name="type" id="product_type" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" onchange="toggleFloatField('product_type', 'product_float')" required>
            <option value="weapon">Оружие</option>
            <option value="agent">Агент</option>
          </select>
        </div>
        <div id="product_float">
          <input name="float_value" type="number" step="0.001" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Float (0.00-1.00, опционально)" min="0" max="1">
        </div>
        <div>
          <label class="flex items-center gap-2">
            <input type="checkbox" name="trade_ban" class="h-5 w-5 text-orange-500 bg-gray-700 border-gray-600 rounded">
            <span class="text-gray-300">Trade Ban</span>
          </label>
        </div>
        <div>
          <input name="image" type="file" accept="image/*" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Изображение">
        </div>
        <div class="md:col-span-2">
          <button class="bg-green-600 text-white w-full py-2 rounded-lg hover:bg-green-700 btn">➕ Добавить товар</button>
        </div>
      </form>
      <hr class="border-gray-700 my-6">
      <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn w-full text-center">⬅️ Назад</a>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
        <a href="/admin/products" class="text-gray-300 hover:text-orange-500">📦 Товары</a>
        <a href="/admin/lots" class="text-gray-300 hover:text-orange-500">🏆 Лоты</a>
        <a href="/admin/purchases" class="text-gray-300 hover:text-orange-500">🛒 Покупки</a>
      </div>
    </div>
    """
    return html

@app.route('/admin/lots')
def admin_lots():
    if not is_admin():
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, current_price, end_time, step, active, image, float_value, trade_ban, type FROM lots')
    lots = c.fetchall()
    conn.close()
    html = TAILWIND + """
    <div class="container mx-auto pt-10 pb-10 px-4">
      <h2 class="text-3xl font-bold text-blue-500 mb-6">🏆 Лоты</h2>
      <div class="overflow-x-auto">
        <table class="w-full bg-gray-800 text-gray-300 rounded-lg">
          <thead><tr class="bg-gray-900"><th class="p-3">Фото</th><th class="p-3">Название</th><th class="p-3">Описание</th><th class="p-3">Ставка</th><th class="p-3">До конца</th><th class="p-3">Float</th><th class="p-3">Trade Ban</th><th class="p-3">Тип</th><th class="p-3">Статус</th><th class="p-3">Действия</th></tr></thead>
          <tbody>
    """
    for l in lots:
        time_left = max(0, l[4] - int(time.time()))
        status = '🟢 Активен' if l[6] else '⛔ Остановлен'
        float_text = f"{l[8]:.4f}" if l[8] is not None and l[10] == 'weapon' else "N/A"
        ban_text = 'Да' if l[9] else 'Нет'
        type_text = 'Оружие' if l[10] == 'weapon' else 'Агент'
        img_html = f'<img src="/static/images/{l[7]}" class="w-16 h-16 rounded-lg object-cover" alt="{l[1]}">' if l[7] else ""
        html += f"""
        <tr class="border-b border-gray-700">
          <td class="p-3">{img_html}</td>
          <td class="p-3">{l[1]}</td>
          <td class="p-3">{l[2]}</td>
          <td class="p-3">{l[3]}₽</td>
          <td class="p-3">{time_left//60} мин {time_left%60} сек</td>
          <td class="p-3">{float_text}</td>
          <td class="p-3">{ban_text}</td>
          <td class="p-3">{type_text}</td>
          <td class="p-3">{status}</td>
          <td class="p-3">
            <div class="flex flex-col gap-2">
              {'' if not l[6] else f'<form method="post" action="/stop_lot"><input type="hidden" name="lot_id" value="{l[0]}"><button class="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 btn text-sm">⛔ Остановить</button></form>'}
              <form method="post" action="/delete_lot"><input type="hidden" name="lot_id" value="{l[0]}"><button class="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700 btn text-sm">🗑️ Удалить</button></form>
            </div>
          </td>
        </tr>
        """
    html += """
          </tbody>
        </table>
      </div>
      <hr class="border-gray-700 my-6">
      <h2 class="text-3xl font-bold text-blue-500 mb-6">➕ Добавить лот</h2>
      <form method="post" action="/add_lot" class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4" enctype="multipart/form-data">
        <div>
          <input name="name" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Название оружия или агента" required>
        </div>
        <div>
          <textarea name="description" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Описание (например, скин, редкость)" rows="3" required></textarea>
        </div>
        <div>
          <input name="start_price" type="number" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Стартовая цена (₽)" required>
        </div>
        <div>
          <input name="step" type="number" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Шаг ставки (₽)" required>
        </div>
        <div>
          <input name="minutes" type="number" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Время аукциона (минуты)" required>
        </div>
        <div>
          <select name="type" id="lot_type" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" onchange="toggleFloatField('lot_type', 'lot_float')" required>
            <option value="weapon">Оружие</option>
            <option value="agent">Агент</option>
          </select>
        </div>
        <div id="lot_float">
          <input name="float_value" type="number" step="0.001" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Float (0.00-1.00, опционально)" min="0" max="1">
        </div>
        <div>
          <label class="flex items-center gap-2">
            <input type="checkbox" name="trade_ban" class="h-5 w-5 text-orange-500 bg-gray-700 border-gray-600 rounded">
            <span class="text-gray-300">Trade Ban</span>
          </label>
        </div>
        <div>
          <input name="image" type="file" accept="image/*" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Изображение">
        </div>
        <div class="md:col-span-2">
          <button class="bg-blue-600 text-white w-full py-2 rounded-lg hover:bg-blue-700 btn">➕ Добавить лот</button>
        </div>
      </form>
      <hr class="border-gray-700 my-6">
      <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn w-full text-center">⬅️ Назад</a>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
        <a href="/admin/products" class="text-gray-300 hover:text-orange-500">📦 Товары</a>
        <a href="/admin/lots" class="text-gray-300 hover:text-orange-500">🏆 Лоты</a>
        <a href="/admin/purchases" class="text-gray-300 hover:text-orange-500">🛒 Покупки</a>
      </div>
    </div>
    """
    return html

@app.route('/admin/purchases')
def admin_purchases():
    if not is_admin():
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, product_id, name, price, buyer, time FROM purchases ORDER BY time DESC LIMIT 20')
    purchases = c.fetchall()
    conn.close()
    html = TAILWIND + """
    <div class="container mx-auto pt-10 pb-10 px-4">
      <h2 class="text-3xl font-bold text-yellow-500 mb-6">🛒 Последние покупки</h2>
      <div class="overflow-x-auto">
        <table class="w-full bg-gray-800 text-gray-300 rounded-lg">
          <thead><tr class="bg-gray-900"><th class="p-3">ID</th><th class="p-3">Товар</th><th class="p-3">Цена</th><th class="p-3">Покупатель</th><th class="p-3">Время</th></tr></thead>
          <tbody>
    """
    for pur in purchases:
        dt = time.strftime('%d.%m.%Y %H:%M', time.localtime(pur[5]))
        html += f'<tr class="border-b border-gray-700"><td class="p-3">{pur[0]}</td><td class="p-3">{pur[2]}</td><td class="p-3">{pur[3]}₽</td><td class="p-3">{pur[4]}</td><td class="p-3">{dt}</td></tr>'
    html += """
          </tbody>
        </table>
      </div>
      <hr class="border-gray-700 my-6">
      <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn w-full text-center">⬅️ Назад</a>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
        <a href="/admin/products" class="text-gray-300 hover:text-orange-500">📦 Товары</a>
        <a href="/admin/lots" class="text-gray-300 hover:text-orange-500">🏆 Лоты</a>
        <a href="/admin/purchases" class="text-gray-300 hover:text-orange-500">🛒 Покупки</a>
      </div>
    </div>
    """
    return html

@app.route('/add_product', methods=['POST'])
def add_product():
    if not is_admin(): return redirect('/login')
    name = request.form['name']
    desc = request.form['description']
    price = int(request.form['price'])
    qty = int(request.form['quantity'])
    item_type = request.form['type']
    float_value = float(request.form.get('float_value', None)) if request.form.get('float_value') and item_type == 'weapon' else None
    trade_ban = 1 if request.form.get('trade_ban') else 0
    image_file = request.files.get('image')
    image_name = None
    if image_file and image_file.filename:
        image_name = werkzeug.utils.secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO products (name, description, price, quantity, image, float_value, trade_ban, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
              (name, desc, price, qty, image_name, float_value, trade_ban, item_type))
    conn.commit()
    conn.close()
    logging.info(f"Добавлен товар: {name}, {price}, {qty}, Type: {item_type}, Float: {float_value}, Trade Ban: {trade_ban}, Image: {image_name}")
    return redirect('/admin/products')

@app.route('/add_lot', methods=['POST'])
def add_lot():
    if not is_admin(): return redirect('/login')
    name = request.form['name']
    desc = request.form['description']
    start_price = int(request.form['start_price'])
    step = int(request.form['step'])
    minutes = int(request.form['minutes'])
    item_type = request.form['type']
    float_value = float(request.form.get('float_value', None)) if request.form.get('float_value') and item_type == 'weapon' else None
    trade_ban = 1 if request.form.get('trade_ban') else 0
    image_file = request.files.get('image')
    image_name = None
    if image_file and image_file.filename:
        image_name = werkzeug.utils.secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
    end_time = int(time.time()) + minutes * 60
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO lots (name, description, start_price, step, end_time, current_price, image, float_value, trade_ban, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
              (name, desc, start_price, step, end_time, start_price, image_name, float_value, trade_ban, item_type))
    conn.commit()
    conn.close()
    logging.info(f"Создан лот: {name}, {start_price}, {step}, {minutes} мин, Type: {item_type}, Float: {float_value}, Trade Ban: {trade_ban}, Image: {image_name}")
    return redirect('/admin/lots')

@app.route('/mark_sold', methods=['POST'])
def mark_sold():
    if not is_admin(): return redirect('/login')
    pid = int(request.form['product_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE products SET sold=1 WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return redirect('/admin/products')

@app.route('/mark_unsold', methods=['POST'])
def mark_unsold():
    if not is_admin(): return redirect('/login')
    pid = int(request.form['product_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE products SET sold=0 WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return redirect('/admin/products')

@app.route('/delete_product', methods=['POST'])
def delete_product():
    if not is_admin(): return redirect('/login')
    pid = int(request.form['product_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return redirect('/admin/products')

@app.route('/stop_lot', methods=['POST'])
def stop_lot():
    if not is_admin(): return redirect('/login')
    lot_id = int(request.form['lot_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE lots SET active=0 WHERE id=?', (lot_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/lots')

@app.route('/delete_lot', methods=['POST'])
def delete_lot():
    if not is_admin(): return redirect('/login')
    lot_id = int(request.form['lot_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM lots WHERE id=?', (lot_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/lots')

@app.errorhandler(Exception)
def handle_error(e):
    import traceback
    error_text = f'<h3 class="text-red-500">Ошибка сервера:</h3><pre class="text-gray-300">{traceback.format_exc()}</pre>'
    logging.error(traceback.format_exc())
    return TAILWIND + f'<div class="container mx-auto pt-10 pb-10 px-4">{error_text}<a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>', 500

# =====================
# Фоновая задача: завершение аукционов
# =====================
def auction_watcher():
    while True:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = int(time.time())
        c.execute('SELECT id, name, current_price, end_time, active FROM lots WHERE active=1')
        for lot in c.fetchall():
            if now >= lot[3]:
                c.execute('SELECT user_id FROM bids WHERE lot_id=? ORDER BY amount DESC LIMIT 1', (lot[0],))
                winner = c.fetchone()
                winner_id = winner[0] if winner else None
                c.execute('UPDATE lots SET active=0, winner_id=? WHERE id=?', (winner_id, lot[0]))
                conn.commit()
                notify_admins_auction(lot[1], lot[2], winner_id or 'Нет победителя')
                if winner_id:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(bot.send_message(winner_id, f"🎉 Поздравляем! Вы выиграли аукцион: {lot[1]} за {lot[2]}₽"))
                        loop.close()
                    except Exception as e:
                        logging.error(f"Ошибка уведомления победителя: {e}")
        conn.close()
        time.sleep(5)

Thread(target=auction_watcher, daemon=True).start()

# =====================
# Запуск Flask и Telegram-бота
# =====================
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_aiogram():
    asyncio.run(dp.start_polling(bot))

if __name__ == '__main__':
    flask_process = multiprocessing.Process(target=run_flask)
    flask_process.start()
    run_aiogram()