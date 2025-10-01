import os
import logging
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session
from templates import TAILWIND
from config import ADMIN_IDS, BOT_USERNAME, ADMIN_USERNAME
from database import DB_PATH
from telegram_bot import notify_admins_product, bot
import asyncio
import time

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['DEBUG'] = True
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    <div class="container mx-auto pt-12 pb-10 px-4 text-center bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
      <h1 class="text-4xl md:text-5xl font-extrabold text-orange-500 mb-4 animate-pulse">CSGO Saller</h1>
      <p class="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl mx-auto">Покупайте и продавайте скины CSGO быстро и безопасно! Присоединяйтесь к нашему сообществу и участвуйте в аукционах!</p>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10 max-w-4xl mx-auto">
        <button onclick="openModal('welcome', 'Добро пожаловать!', 'Спасибо за посещение CSGO Saller! Здесь вы можете купить скины, участвовать в аукционах и наслаждаться безопасной торговлей.', 0, 0, null, 0, 'welcome')" class="bg-orange-500 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-orange-600 transform hover:scale-105 transition duration-300 btn">🚀 Начать</button>
        <a href="/shop" class="bg-green-600 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-green-700 transform hover:scale-105 transition duration-300 btn">🛒 Магазин</a>
        <a href="/auction" class="bg-blue-600 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-blue-700 transform hover:scale-105 transition duration-300 btn">🏆 Аукцион</a>
      </div>
    """
    if user_id in ADMIN_IDS:
        html += '<a href="/admin/products" class="bg-gray-700 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-gray-600 transform hover:scale-105 transition duration-300 btn inline-block">🔑 Админ-панель</a>'
    html += """
      <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div id="modalContent" class="max-w-md w-full"></div>
      </div>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
        <a href="/shop" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🛒 Магазин</a>
        <a href="/auction" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🏆 Аукцион</a>
      </div>
    </div>
    """
    return html

@app.route('/shop')
def shop():
    user_id = session.get('user_id', None)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products WHERE sold=0 AND quantity>0')
    products = c.fetchall()
    conn.close()
    html = TAILWIND + """
    <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
      <h2 class="text-3xl font-bold text-green-500 mb-8 text-center">🛒 Магазин</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
    """
    for p in products:
        img_html = f'<img src="/static/images/{p[6]}" class="mb-4 w-full rounded-lg object-cover shadow-md" style="max-height:180px;" alt="{p[1]}">' if p[6] else ""
        float_text = f"Float: {p[7]:.4f}" if p[7] is not None and p[9] == 'weapon' else ""
        ban_text = "Trade Ban: Да" if p[8] else "Trade Ban: Нет"
        type_text = "Тип: Оружие" if p[9] == 'weapon' else "Тип: Агент"
        product_link = f"https://csgosaller-1.onrender.com/product/{p[0]}"
        escaped_name = p[1].replace("'", "\\'")
        escaped_desc = p[2].replace("'", "\\'")
        html += f"""
        <div class="bg-gray-800 rounded-lg p-4 card shadow-lg hover:shadow-xl transition duration-300">
          {img_html}
          <h5 class="text-xl font-bold text-green-500 mb-2">{p[1]}</h5>
          <p class="text-gray-300 text-sm mb-2">{p[2]}</p>
          <p class="text-sm text-gray-400 mb-2">ID: {p[0]}</p>
          <p class="mt-2"><span class="bg-yellow-500 text-black px-2 py-1 rounded">💰 {p[3]}₽</span> <span class="bg-blue-500 text-white px-2 py-1 rounded ml-2">📦 Осталось: {p[4]}</span></p>
          <p class="mt-2 text-sm text-gray-400">{float_text} {'' if not float_text else ' | '}{ban_text} | {type_text}</p>
          <button onclick="openModal({p[0]}, '{escaped_name}', '{escaped_desc}', {p[3]}, {p[4]}, {p[7] if p[7] is not None else 'null'}, {p[8]}, '{p[9]}')" class="bg-green-600 text-white w-full py-2 rounded-lg hover:bg-green-700 transform hover:scale-105 transition duration-300 btn mt-4 text-sm">📩 Написать админу</button>
        </div>
        """
    html += """
      </div>
      <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div id="modalContent" class="max-w-md w-full"></div>
      </div>
      <hr class="border-gray-700 my-8">
      <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn w-full text-center">⬅️ Назад</a>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
        <a href="/" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🏠 Главная</a>
        <a href="/auction" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🏆 Аукцион</a>
      </div>
    </div>
    """
    return html

@app.route('/product/<int:product_id>')
def product(product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products WHERE id=?', (product_id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        return TAILWIND + '''
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
            <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">Товар не найден.</div>
            <a href="/shop" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">⬅️ Вернуться в магазин</a>
        </div>
        '''
    
    float_text = f"{product[7]:.4f}" if product[7] is not None and product[9] == 'weapon' else "N/A"
    ban_text = 'Да' if product[8] else 'Нет'
    type_text = 'Оружие' if product[9] == 'weapon' else 'Агент'
    img_html = f'<img src="/static/images/{product[6]}" class="w-full rounded-lg object-cover mb-4 shadow-md" style="max-height:300px;" alt="{product[1]}">' if product[6] else ""
    product_link = f"https://csgosaller-1.onrender.com/product/{product[0]}"
    admin_url = f"https://t.me/{ADMIN_USERNAME}" if not ADMIN_USERNAME.startswith('+') else f"https://t.me/{ADMIN_USERNAME}"
    
    html = TAILWIND + f'''
    <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
        <h2 class="text-3xl font-bold text-green-500 mb-8 text-center">📦 Товар ID: {product[0]}</h2>
        <div class="bg-gray-800 rounded-lg p-6 card shadow-lg hover:shadow-xl transition duration-300">
            {img_html}
            <h3 class="text-2xl font-bold text-green-500 mb-2">{product[1]}</h3>
            <p class="text-gray-300 text-sm mb-2">{product[2]}</p>
            <p class="text-gray-300 text-sm mb-2">💰 Цена: {product[3]}₽</p>
            <p class="text-gray-300 text-sm mb-2">📦 Количество: {product[4]}</p>
            <p class="text-gray-300 text-sm mb-2">🔢 Float: {float_text}</p>
            <p class="text-gray-300 text-sm mb-2">🚫 Trade Ban: {ban_text}</p>
            <p class="text-gray-300 text-sm mb-3">🎮 Тип: {type_text}</p>
            <p class="text-gray-300 text-sm mb-3">🔗 Ссылка на товар: <a href="{product_link}" class="text-blue-500 hover:underline">{product_link}</a></p>
            <p class="text-gray-300 text-sm mb-3">📋 Отправьте эту ссылку и вашу трейд-ссылку администратору в Telegram!</p>
            <a href="{admin_url}" class="bg-green-600 text-white w-full py-2 rounded-lg hover:bg-green-700 transform hover:scale-105 transition duration-300 btn text-center block text-sm">📩 Написать админу</a>
            <a href="/shop" class="bg-gray-800 text-white w-full py-2 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-2 text-sm text-center">⬅️ Вернуться в магазин</a>
        </div>
        <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
            <a href="/shop" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🛒 Магазин</a>
            <a href="/auction" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🏆 Аукцион</a>
        </div>
    </div>
    '''
    return html

@app.route('/buy', methods=['POST'])
def buy():
    logging.info("Маршрут /buy вызван")
    user_id = session.get('user_id', None)
    buyer = "Гость" if not user_id else f"ID{user_id}"
    logging.info(f"Покупатель: {buyer}, user_id: {user_id}")
    
    try:
        product_id = request.form.get('product_id')
        trade_link = request.form.get('trade_link')
        product_link = f"https://csgosaller-1.onrender.com/product/{product_id}" if product_id else None
        logging.info(f"Получен product_id: {product_id}, trade_link: {trade_link}, product_link: {product_link}")
        if not product_id:
            logging.error("product_id отсутствует в форме")
            return TAILWIND + '<div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen"><div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">Ошибка: ID товара не указан.</div><a href="/shop" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">Назад</a></div>'
        
        pid = int(product_id)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT name, description, price, quantity, float_value, trade_ban, type FROM products WHERE id=? AND sold=0 AND quantity>0', (pid,))
        prod = c.fetchone()
        logging.info(f"Результат запроса к products: {prod}")
        
        if not prod:
            conn.close()
            logging.error(f"Товар недоступен: id={pid}, prod={prod}")
            return TAILWIND + '<div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen"><div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">Товар недоступен.</div><a href="/shop" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">Назад</a></div>'
        
        c.execute('UPDATE products SET quantity=quantity-1 WHERE id=?', (pid,))
        if prod[3] == 1:
            c.execute('UPDATE products SET sold=1 WHERE id=?', (pid,))
        
        if user_id:
            c.execute('INSERT OR REPLACE INTO pending_requests (user_id, product_id, timestamp) VALUES (?, ?, ?)',
                      (user_id, pid, int(time.time())))
        
        conn.commit()
        conn.close()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(notify_admins_product(
            product_id=pid,
            product_name=prod[0],
            description=prod[1],
            price=prod[2],
            quantity=prod[3],
            float_value=prod[4],
            trade_ban=prod[5],
            product_type=prod[6],
            user_id=user_id or 0,
            trade_link=trade_link,
            product_link=product_link
        ))
        loop.close()
        
        logging.info(f"Покупка успешна: {prod[0]}, {prod[2]}, {buyer}, {prod[1]}, {prod[3]}, Float: {prod[4]}, Trade Ban: {prod[5]}, Type: {prod[6]}")
        return TAILWIND + '<div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen"><div class="bg-green-600 text-white p-4 rounded-lg shadow-lg">✅ Заявка на покупку отправлена администратору!</div><a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">Назад</a></div>'
    
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"Ошибка в /buy: {str(e)}")
        return TAILWIND + f'<div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen"><div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">Ошибка: {str(e)}</div><a href="/shop" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">Назад</a></div>'

@app.route('/auction', methods=['GET'])
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
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
          <h2 class="text-3xl font-bold text-blue-500 mb-8 text-center">🏆 Аукцион</h2>
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        """
        for l in lots:
            time_left = "Без ограничения" if l[4] is None else f"{max(0, l[4] - int(time.time()))//60} мин {max(0, l[4] - int(time.time()))%60} сек"
            img_html = f'<img src="/static/images/{l[7]}" class="mb-4 w-full rounded-lg object-cover shadow-md" style="max-height:180px;" alt="{l[1]}">' if l[7] else ""
            float_text = f"Float: {l[8]:.4f}" if l[8] is not None and l[10] == 'weapon' else ""
            ban_text = "Trade Ban: Да" if l[9] else "Trade Ban: Нет"
            type_text = "Тип: Оружие" if l[10] == 'weapon' else "Тип: Агент"
            html += f"""
            <div class="bg-gray-800 rounded-lg p-4 card shadow-lg hover:shadow-xl transition duration-300">
              {img_html}
              <h5 class="text-xl font-bold text-blue-500 mb-2">{l[1]}</h5>
              <p class="text-gray-300 text-sm mb-2">{l[2]}</p>
              <p class="mt-2"><span class="bg-yellow-500 text-black px-2 py-1 rounded">💰 Текущая ставка: {l[3]}₽</span></p>
              <p class="mt-2"><span class="bg-gray-600 text-white px-2 py-1 rounded">⏳ До конца: {time_left}</span></p>
              <p class="mt-2 text-sm text-gray-400">{float_text} {'' if not float_text else ' | '}{ban_text} | {type_text}</p>
              <form method="post" action="/bid" class="mt-4">
                <input type="hidden" name="lot_id" value="{l[0]}">
                <input type="hidden" name="step" value="{l[5]}">
                <button type="submit" class="bg-yellow-500 text-black w-full py-2 rounded-lg hover:bg-yellow-600 transform hover:scale-105 transition duration-300 btn">🔼 Ставка +{l[5]}₽</button>
              </form>
              <form method="post" action="/bid_custom" class="mt-2">
                <input type="hidden" name="lot_id" value="{l[0]}">
                <input type="number" name="amount" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600 mb-2" placeholder="Ваша ставка (₽)" min="{l[3]+l[5]}" required>
                <button type="submit" class="bg-blue-600 text-white w-full py-2 rounded-lg hover:bg-blue-700 transform hover:scale-105 transition duration-300 btn">💸 Ввести сумму</button>
              </form>
            </div>
            """
        html += """
          </div>
          <hr class="border-gray-700 my-8">
          <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn w-full text-center">⬅️ Назад</a>
          <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
            <a href="/" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🏠 Главная</a>
            <a href="/shop" class="text-gray-300 hover:text-orange-500 text-sm font-medium">🛒 Магазин</a>
          </div>
        </div>
        """
        return html
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"Ошибка в /auction: {str(e)}")
        return TAILWIND + f'<div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen"><div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">Ошибка: {str(e)}</div><a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">Назад</a></div>'

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
        return TAILWIND + '<div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen"><div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">Лот недоступен.</div><a href="/auction" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">Назад</a></div>'
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
        return TAILWIND + '<div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen"><div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">Сумма слишком мала.</div><a href="/auction" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">Назад</a></div>'
    c.execute('UPDATE lots SET current_price=? WHERE id=?', (amount, lot_id))
    c.execute('INSERT INTO bids (lot_id, user_id, amount, time) VALUES (?, ?, ?, ?)', (lot_id, user_id, amount, int(time.time())))
    conn.commit()
    conn.close()
    logging.info(f"Ставка: Лот {lot_id}, {amount}, {user_id}")
    return redirect('/auction')