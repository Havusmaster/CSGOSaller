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

"""

# =====================
# Конфиг
# =====================
BOT_TOKEN = "7504123410:AAEznGqRafbyrBx2e34HzsxztWV201HRMxE"  # Замените на реальный токен
ADMIN_IDS = [1939282952, 5266027747]

# =====================
# Импорт библиотек
# =====================
import os
import sqlite3
import logging
import time
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram import Router
from aiogram.filters import Command
import asyncio
import multiprocessing
import werkzeug

# =====================
# Логирование
# =====================
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

# =====================
# Инициализация базы данных (добавлено поле image)
# =====================
DB_PATH = "auction_shop.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price INTEGER,
        quantity INTEGER,
        sold INTEGER DEFAULT 0,
        image TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        start_price INTEGER,
        step INTEGER,
        end_time INTEGER,
        current_price INTEGER,
        winner_id INTEGER,
        active INTEGER DEFAULT 1,
        image TEXT
    )""")
    # Таблица ставок
    c.execute("""
    CREATE TABLE IF NOT EXISTS bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER,
        user_id INTEGER,
        amount INTEGER,
        time INTEGER
    )""")
    conn.commit()
    conn.close()
init_db()

# =====================
# Flask WebApp: добавлена поддержка фото
# =====================
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['DEBUG'] = True
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Bootstrap шаблон
BOOTSTRAP = """
<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css' rel='stylesheet'>
<script src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js'></script>
"""

# =====================
# Telegram Bot
# =====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

def main_kb():
    return types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(text="🛒 Открыть магазин/аукцион", web_app=types.WebAppInfo(url="https://csgosaller-1.onrender.com/"))]
    ])

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать!", reply_markup=main_kb())

dp.include_router(router)

# =====================
# Уведомление админам о покупке
# =====================
def notify_admins_purchase(product, price, buyer):
    text = f"\n🛒 Новая заявка на покупку!\n📦 Товар: {product}\n💰 Цена: {price}\n👤 Покупатель: {buyer}"
    for admin_id in ADMIN_IDS:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(bot.send_message(admin_id, text))
            else:
                loop.run_until_complete(bot.send_message(admin_id, text))
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    logging.info(f"Покупка: {product}, {price}, {buyer}")

# =====================
# Уведомление админам о завершении аукциона
# =====================
def notify_admins_auction(lot, price, winner):
    text = f"\n🏆 Аукцион завершён!\n📦 Лот: {lot}\n💰 Цена: {price}\n👤 Победитель: {winner}"
    for admin_id in ADMIN_IDS:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(bot.send_message(admin_id, text))
            else:
                loop.run_until_complete(bot.send_message(admin_id, text))
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    logging.info(f"Аукцион: {lot}, {price}, {winner}")

# =====================
# Flask маршруты
# =====================
import os
import sqlite3
import logging
import time
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from threading import Thread
import threading
import asyncio

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
    # Таблица товаров
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price INTEGER,
        quantity INTEGER,
        sold INTEGER DEFAULT 0,
        image TEXT
    )""")
    # Таблица лотов
    c.execute("""
    CREATE TABLE IF NOT EXISTS lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        start_price INTEGER,
        step INTEGER,
        end_time INTEGER,
        current_price INTEGER,
        winner_id INTEGER,
        active INTEGER DEFAULT 1,
        image TEXT
    )""")
    # Таблица ставок
    c.execute("""
    CREATE TABLE IF NOT EXISTS bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER,
        user_id INTEGER,
        amount INTEGER,
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
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = 'static/images/'  # <-- добавьте эту строку

@app.errorhandler(Exception)
def handle_error(e):
    import traceback
    error_text = f"<h3 style='color:red'>Ошибка сервера:</h3><pre>{traceback.format_exc()}</pre>"
    logging.error(traceback.format_exc())
    return HEADER + f"<div class='container'>{error_text}</div>", 500

# Bootstrap шаблон
BOOTSTRAP = """
<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css' rel='stylesheet'>
<script src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js'></script>
"""

# =====================
# Telegram Bot
# =====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

def main_kb():
    return types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(text="🛒 Открыть магазин/аукцион", web_app=types.WebAppInfo(url="https://csgosaller-1.onrender.com/"))]
    ])

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать!", reply_markup=main_kb())

dp.include_router(router)

# =====================
# Уведомление админам о покупке
# =====================
def notify_admins_purchase(product, price, buyer):
    text = f"\n🛒 Новая заявка на покупку!\n📦 Товар: {product}\n💰 Цена: {price}\n👤 Покупатель: {buyer}"
    for admin_id in ADMIN_IDS:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(bot.send_message(admin_id, text))
            else:
                loop.run_until_complete(bot.send_message(admin_id, text))
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    logging.info(f"Покупка: {product}, {price}, {buyer}")

# =====================
# Уведомление админам о завершении аукциона
# =====================
def notify_admins_auction(lot, price, winner):
    text = f"\n🏆 Аукцион завершён!\n📦 Лот: {lot}\n💰 Цена: {price}\n👤 Победитель: {winner}"
    for admin_id in ADMIN_IDS:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(bot.send_message(admin_id, text))
            else:
                loop.run_until_complete(bot.send_message(admin_id, text))
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    logging.info(f"Аукцион: {lot}, {price}, {winner}")

# =====================
# Flask маршруты
# =====================
# ...дальнейший код...

import threading
import os

# =====================
# HTML-шаблоны
# =====================
HEADER = BOOTSTRAP + """
<nav class='navbar navbar-expand-lg navbar-dark bg-dark shadow-lg mb-4'>
  <div class='container-fluid'>
    <span class='navbar-brand mb-0 h1 display-6'>🛒 <b>CSGO2 Магазин & Аукцион</b></span>
  </div>
</nav>
<style>
body { background: #111 !important; color: #eee !important; min-height:100vh; }
.card { background: #181818 !important; box-shadow: 0 4px 24px rgba(0,0,0,0.25); border-radius: 1rem; border: none; }
.btn { font-size: 1.1em; font-weight: 500; border-radius: 0.7em; }
.card-title { font-size: 1.3em; font-weight: bold; color: #fff; }
hr { border-top: 2px solid #222; }
.table { background: #181818 !important; color: #eee !important; }
.table th, .table td { vertical-align: middle; border-color: #222 !important; }
.table-striped > tbody > tr:nth-of-type(odd) { background-color: #222 !important; }
input, select, textarea { background: #222 !important; color: #eee !important; border: 1px solid #333 !important; }
.form-control:focus { background: #222 !important; color: #fff !important; border-color: #444 !important; }
.navbar, .navbar-brand { background: #111 !important; }
.badge { border-radius: 0.5em; }
</style>
"""

# =====================
# Авторизация
# =====================
def is_admin():
    return session.get('user_id') in ADMIN_IDS

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = int(request.form.get('user_id', 0))
        session['user_id'] = user_id
        return redirect(url_for('admin')) if user_id in ADMIN_IDS else redirect(url_for('index'))
    return HEADER + """
    <div class='container'>
      <h3>Вход по ID</h3>
      <form method='post'>
        <input type='number' name='user_id' class='form-control mb-2' placeholder='Ваш Telegram ID' required>
        <button class='btn btn-primary'>Войти</button>
      </form>
    </div>
    """

# =====================
# Главная страница (Магазин и Аукцион)
# =====================
@app.route('/')
def index():
    user_id = session.get('user_id', None)
    html = HEADER + """
    <div class='container text-center'>
      <h2 class='text-light mb-4'><span class='badge bg-dark fs-4'>Добро пожаловать!</span></h2>
      <div class='row justify-content-center mb-5'>
        <div class='col-md-6'>
          <a href='/shop' class='btn btn-success btn-lg w-100 mb-3 shadow-sm' style='font-size:1.5em;'>🛒 Магазин</a>
        </div>
        <div class='col-md-6'>
          <a href='/auction' class='btn btn-primary btn-lg w-100 mb-3 shadow-sm' style='font-size:1.5em;'>🏆 Аукцион</a>
        </div>
      </div>
    """
    if user_id in ADMIN_IDS:
        html += "<a href='/admin' class='btn btn-dark w-100 fs-5 shadow-sm'>🔑 Админ-панель</a>"
    else:
        html += "<a href='/login' class='btn btn-secondary w-100 fs-5 shadow-sm'>Войти как админ</a>"
    html += "</div>"
    return html

@app.route('/shop')
def shop():
    user_id = session.get('user_id', None)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image FROM products WHERE sold=0 AND quantity>0')
    products = c.fetchall()
    conn.close()
    html = HEADER + """
    <div class='container'>
      <h2 class='text-light mb-4'><span class='badge bg-success fs-4'>🛒 Магазин</span></h2>
      <div class='row g-4'>
    """
    for p in products:
        img_html = f"<img src='/static/images/{p[6]}' class='mb-2 w-100 rounded shadow-sm' style='max-height:180px;object-fit:cover;'>" if p[6] else ""
        html += f"""
        <div class='col-md-4'>
          <div class='card border-success h-100'>
            <div class='card-body'>
              {img_html}
              <h5 class='card-title text-success'>🏷 {p[1]}</h5>
              <p class='card-text text-light'>📜 {p[2]}</p>
              <p class='mb-2'><span class='badge bg-warning text-dark'>💰 {p[3]}₽</span> <span class='badge bg-info text-dark'>📦 Осталось: {p[4]}</span></p>
              <form method='post' action='/buy'>
                <input type='hidden' name='product_id' value='{p[0]}'>
                <button class='btn btn-success w-100 shadow-sm'>🛒 Купить</button>
              </form>
            </div>
          </div>
        </div>
        """
    html += "</div><hr>"
    html += """
      <div class='row mt-4'>
        <div class='col-md-6'>
          <a href='/auction' class='btn btn-primary w-100 fs-5 shadow-sm'>🏆 Перейти к аукциону</a>
        </div>
        <div class='col-md-6'>
          <a href='/' class='btn btn-dark w-100 fs-5 shadow-sm'>⬅️ Назад</a>
        </div>
      </div>
    </div>
    """
    return html

@app.route('/auction')
def auction():
    user_id = session.get('user_id', None)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, current_price, end_time, step, active, image FROM lots WHERE active=1')
    lots = c.fetchall()
    conn.close()
    html = HEADER + """
    <div class='container'>
      <h2 class='text-light mb-4'><span class='badge bg-primary fs-4'>🏆 Аукцион</span></h2>
      <div class='row g-4'>
    """
    for l in lots:
        time_left = max(0, l[4] - int(time.time()))
        img_html = f"<img src='/static/images/{l[7]}' class='mb-2 w-100 rounded shadow-sm' style='max-height:180px;object-fit:cover;'>" if l[7] else ""
        html += f"""
        <div class='col-md-6'>
          <div class='card border-primary h-100'>
            <div class='card-body'>
              {img_html}
              <h5 class='card-title text-primary'>🏆 {l[1]}</h5>
              <p class='card-text text-light'>📜 {l[2]}</p>
              <p class='mb-2'><span class='badge bg-warning text-dark'>💰 Текущая ставка: {l[3]}₽</span></p>
              <p class='mb-2'><span class='badge bg-secondary'>⏳ До конца: {time_left//60} мин {time_left%60} сек</span></p>
              <form method='post' action='/bid'>
                <input type='hidden' name='lot_id' value='{l[0]}'>
                <input type='hidden' name='step' value='{l[5]}'>
                <button class='btn btn-warning w-100 shadow-sm'>🔼 Ставка +{l[5]}₽</button>
              </form>
              <form method='post' action='/bid_custom' class='mt-2'>
                <input type='hidden' name='lot_id' value='{l[0]}'>
                <input type='number' name='amount' class='form-control mb-2' placeholder='Ввести сумму' min='{l[3]+l[5]}' required>
                <button class='btn btn-info w-100 shadow-sm'>💸 Ввести сумму</button>
              </form>
            </div>
          </div>
        </div>
        """
    html += "</div><hr>"
    html += """
      <div class='row mt-4'>
        <div class='col-md-6'>
          <a href='/shop' class='btn btn-success w-100 fs-5 shadow-sm'>🛒 Перейти в магазин</a>
        </div>
        <div class='col-md-6'>
          <a href='/' class='btn btn-dark w-100 fs-5 shadow-sm'>⬅️ Назад</a>
        </div>
      </div>
    </div>
    """
    return html

# =====================
# Покупка товара
# =====================
@app.route('/buy', methods=['POST'])
def buy():
    user_id = session.get('user_id', 'Гость')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pid = int(request.form['product_id'])
    c.execute('SELECT name, price, quantity FROM products WHERE id=? AND sold=0', (pid,))
    prod = c.fetchone()
    if not prod or prod[2] < 1:
        conn.close()
        return HEADER + "<div class='container'><div class='alert alert-danger'>Товар недоступен.</div></div>"
    c.execute('UPDATE products SET quantity=quantity-1 WHERE id=?', (pid,))
    if prod[2] == 1:
        c.execute('UPDATE products SET sold=1 WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    notify_admins_purchase(prod[0], prod[1], user_id)
    logging.info(f"Покупка: {prod[0]}, {prod[1]}, {user_id}")
    return HEADER + "<div class='container'><div class='alert alert-success'>✅ Заявка на покупку отправлена администратору!</div><a href='/' class='btn btn-primary mt-2'>Назад</a></div>"

# =====================
# Ставка +Шаг
# =====================
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
        return HEADER + "<div class='container'><div class='alert alert-danger'>Лот недоступен.</div></div>"
    new_price = lot[0] + step
    c.execute('UPDATE lots SET current_price=? WHERE id=?', (new_price, lot_id))
    c.execute('INSERT INTO bids (lot_id, user_id, amount, time) VALUES (?, ?, ?, ?)', (lot_id, user_id, new_price, int(time.time())))
    conn.commit()
    conn.close()
    logging.info(f"Ставка: Лот {lot_id}, {new_price}, {user_id}")
    return redirect('/')

# =====================
# Ставка вручную
# =====================
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
        return HEADER + "<div class='container'><div class='alert alert-danger'>Сумма слишком мала.</div></div>"
    c.execute('UPDATE lots SET current_price=? WHERE id=?', (amount, lot_id))
    c.execute('INSERT INTO bids (lot_id, user_id, amount, time) VALUES (?, ?, ?, ?)', (lot_id, user_id, amount, int(time.time())))
    conn.commit()
    conn.close()
    logging.info(f"Ставка: Лот {lot_id}, {amount}, {user_id}")
    return redirect('/')

# =====================
# Админ-панель
# =====================
@app.route('/admin')
def admin():
    if not is_admin():
        return redirect('/login')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image FROM products')
    products = c.fetchall()
    c.execute('SELECT id, name, description, current_price, end_time, step, active, image FROM lots')
    lots = c.fetchall()
    conn.close()
    html = HEADER + """
    <div class='container'>
      <h2 class='text-light mb-4'><span class='badge bg-dark fs-4'>📦 Управление товарами</span></h2>
      <table class='table table-dark table-striped table-bordered rounded shadow-sm'>
        <tr><th>Фото</th><th>Название</th><th>Описание</th><th>Цена</th><th>Кол-во</th><th>Статус</th><th>Действия</th></tr>
    """
    for p in products:
        status = '✅ Продан' if p[5] else '🟢 В продаже'
        img_html = f"<img src='/static/images/{p[6]}' style='max-width:60px;max-height:60px;border-radius:8px;'>" if p[6] else ""
        html += f"<tr><td>{img_html}</td><td>{p[1]}</td><td>{p[2]}</td><td>{p[3]}</td><td>{p[4]}</td><td>{status}</td><td>"
        if not p[5]:
            html += f"<form method='post' action='/mark_sold'><input type='hidden' name='product_id' value='{p[0]}'><button class='btn btn-success btn-sm mb-1'>✅ Продан</button></form>"
        else:
            html += f"<form method='post' action='/mark_unsold'><input type='hidden' name='product_id' value='{p[0]}'><button class='btn btn-warning btn-sm mb-1'>❌ Не продан</button></form>"
        html += f"<form method='post' action='/delete_product'><input type='hidden' name='product_id' value='{p[0]}'><button class='btn btn-danger btn-sm mb-1'>🗑️ Удалить</button></form></td></tr>"
    html += "</table><hr><h2 class='text-light mb-4'><span class='badge bg-success fs-4'>➕ Добавить товар</span></h2>"
    html += """
      <form method='post' action='/add_product' class='mb-4' enctype='multipart/form-data'>
        <input name='name' class='form-control mb-2' placeholder='Название' required>
        <input name='description' class='form-control mb-2' placeholder='Описание' required>
        <input name='price' type='number' class='form-control mb-2' placeholder='Цена' required>
        <input name='quantity' type='number' class='form-control mb-2' placeholder='Количество' required>
        <input name='image' type='file' accept='image/*' class='form-control mb-2'>
        <button class='btn btn-primary w-100 shadow-sm'>➕ Добавить</button>
      </form>
      <hr><h2 class='text-light mb-4'><span class='badge bg-primary fs-4'>🏆 Управление лотами</span></h2>
      <table class='table table-dark table-striped table-bordered rounded shadow-sm'>
        <tr><th>Фото</th><th>Название</th><th>Описание</th><th>Ставка</th><th>До конца</th><th>Статус</th><th>Действия</th></tr>
    """
    for l in lots:
        time_left = max(0, l[4] - int(time.time()))
        status = '🟢 Активен' if l[6] else '⛔ Остановлен'
        img_html = f"<img src='/static/images/{l[7]}' style='max-width:60px;max-height:60px;border-radius:8px;'>" if l[7] else ""
        html += f"<tr><td>{img_html}</td><td>{l[1]}</td><td>{l[2]}</td><td>{l[3]}</td><td>{time_left//60} мин {time_left%60} сек</td><td>{status}</td><td>"
        if l[6]:
            html += f"<form method='post' action='/stop_lot'><input type='hidden' name='lot_id' value='{l[0]}'><button class='btn btn-danger btn-sm mb-1'>⛔ Остановить</button></form>"
        html += f"<form method='post' action='/delete_lot'><input type='hidden' name='lot_id' value='{l[0]}'><button class='btn btn-secondary btn-sm mb-1'>🗑️ Удалить</button></form></td></tr>"
    html += "</table><hr><h2 class='text-light mb-4'><span class='badge bg-warning fs-4'>🏆 Создать лот</span></h2>"
    html += """
      <form method='post' action='/add_lot' class='mb-4' enctype='multipart/form-data'>
        <input name='name' class='form-control mb-2' placeholder='Название' required>
        <input name='description' class='form-control mb-2' placeholder='Описание' required>
        <input name='start_price' type='number' class='form-control mb-2' placeholder='Стартовая цена' required>
        <input name='step' type='number' class='form-control mb-2' placeholder='Шаг' required>
        <input name='minutes' type='number' class='form-control mb-2' placeholder='Время (мин)' required>
        <input name='image' type='file' accept='image/*' class='form-control mb-2'>
        <button class='btn btn-primary w-100 shadow-sm'>🏆 Создать</button>
      </form>
      <hr><a href='/' class='btn btn-dark w-100 fs-5 shadow-sm'>⬅️ Назад</a>
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
    image_file = request.files.get('image')
    image_name = None
    if image_file and image_file.filename:
        image_name = werkzeug.utils.secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO products (name, description, price, quantity, image) VALUES (?, ?, ?, ?, ?)', (name, desc, price, qty, image_name))
    conn.commit()
    conn.close()
    logging.info(f"Добавлен товар: {name}, {price}, {qty}, {image_name}")
    return redirect('/admin')

@app.route('/mark_sold', methods=['POST'])
def mark_sold():
    if not is_admin(): return redirect('/login')
    pid = int(request.form['product_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE products SET sold=1 WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/mark_unsold', methods=['POST'])
def mark_unsold():
    if not is_admin(): return redirect('/login')
    pid = int(request.form['product_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE products SET sold=0 WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/delete_product', methods=['POST'])
def delete_product():
    if not is_admin(): return redirect('/login')
    pid = int(request.form['product_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/add_lot', methods=['POST'])
def add_lot():
    if not is_admin(): return redirect('/login')
    name = request.form['name']
    desc = request.form['description']
    start_price = int(request.form['start_price'])
    step = int(request.form['step'])
    minutes = int(request.form['minutes'])
    image_file = request.files.get('image')
    image_name = None
    if image_file and image_file.filename:
        image_name = werkzeug.utils.secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
    end_time = int(time.time()) + minutes * 60
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO lots (name, description, start_price, step, end_time, current_price, image) VALUES (?, ?, ?, ?, ?, ?, ?)', (name, desc, start_price, step, end_time, start_price, image_name))
    conn.commit()
    conn.close()
    logging.info(f"Создан лот: {name}, {start_price}, {step}, {minutes} мин, {image_name}")
    return redirect('/admin')

@app.route('/stop_lot', methods=['POST'])
def stop_lot():
    if not is_admin(): return redirect('/login')
    lot_id = int(request.form['lot_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE lots SET active=0 WHERE id=?', (lot_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/delete_lot', methods=['POST'])
def delete_lot():
    if not is_admin(): return redirect('/login')
    lot_id = int(request.form['lot_id'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM lots WHERE id=?', (lot_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

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
                # Завершить лот
                c.execute('SELECT user_id FROM bids WHERE lot_id=? ORDER BY amount DESC LIMIT 1', (lot[0],))
                winner = c.fetchone()
                winner_id = winner[0] if winner else None
                c.execute('UPDATE lots SET active=0, winner_id=? WHERE id=?', (winner_id, lot[0]))
                conn.commit()
                notify_admins_auction(lot[1], lot[2], winner_id or 'Нет победителя')
                if winner_id:
                    try:
                        import asyncio
                        loop = asyncio.get_event_loop()
                        msg = f"🎉 Поздравляем! Вы выиграли аукцион: {lot[1]} за {lot[2]}₽"
                        if loop.is_running():
                            asyncio.ensure_future(bot.send_message(winner_id, msg))
                        else:
                            loop.run_until_complete(bot.send_message(winner_id, msg))
                    except Exception as e:
                        logging.error(f"Ошибка уведомления победителя: {e}")
        conn.close()
        time.sleep(5)

threading.Thread(target=auction_watcher, daemon=True).start()

# =====================
# Запуск Flask и Telegram-бота
# =====================
def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def run_aiogram():
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())

if __name__ == '__main__':
    flask_process = multiprocessing.Process(target=run_flask)
    flask_process.start()
    run_aiogram()
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())

if __name__ == '__main__':
    flask_process = multiprocessing.Process(target=run_flask)
    flask_process.start()
    run_aiogram()
