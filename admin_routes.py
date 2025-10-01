import sqlite3
import time
import werkzeug
from flask import session, redirect, url_for, request
from templates import TAILWIND
from config import ADMIN_IDS
from database import DB_PATH
from telegram_bot import notify_admins_auction
import logging
import asyncio

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

def is_admin():
    user_id = session.get('user_id')
    logging.info(f"Checking is_admin for user_id: {user_id}, ADMIN_IDS: {ADMIN_IDS}")
    return user_id in ADMIN_IDS

def admin_product():
    from webapp import app
    @app.route('/admin/product/<int:product_id>')
    def admin_product(product_id):
        if not is_admin():
            return redirect('/login')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products WHERE id=?', (product_id,))
        product = c.fetchone()
        conn.close()
        if not product:
            return TAILWIND + '<div class="container mx-auto pt-10 pb-10 px-4"><div class="bg-red-600 text-white p-4 rounded-lg">Товар не найден.</div><a href="/admin/products" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn mt-4 block text-center">Назад</a></div>'
        
        status = '✅ Продан' if product[5] else '🟢 В продаже'
        float_text = f"{product[7]:.4f}" if product[7] is not None and product[9] == 'weapon' else "N/A"
        ban_text = 'Да' if product[8] else 'Нет'
        type_text = 'Оружие' if product[9] == 'weapon' else 'Агент'
        img_html = f'<img src="/static/images/{product[6]}" class="w-full rounded-lg object-cover mb-4" style="max-height:300px;" alt="{product[1]}">' if product[6] else ""
        
        html = TAILWIND + f"""
        <div class="container mx-auto pt-10 pb-10 px-4">
          <h2 class="text-3xl font-bold text-purple-500 mb-6">📦 Товар ID: {product[0]}</h2>
          <div class="bg-gray-800 rounded-lg p-6 card">
            {img_html}
            <h3 class="text-2xl font-bold text-green-500 mb-2">{product[1]}</h3>
            <p class="text-gray-300 mb-2">{product[2]}</p>
            <p class="text-gray-300 mb-2">💰 Цена: {product[3]}₽</p>
            <p class="text-gray-300 mb-2">📦 Количество: {product[4]}</p>
            <p class="text-gray-300 mb-2">🔢 Float: {float_text}</p>
            <p class="text-gray-300 mb-2">🚫 Trade Ban: {ban_text}</p>
            <p class="text-gray-300 mb-2">🎮 Тип: {type_text}</p>
            <p class="text-gray-300 mb-4">📊 Статус: {status}</p>
            <div class="flex flex-col gap-2">
              {'' if product[5] else f'<form method="post" action="/mark_sold"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 btn">✅ Отметить как продан</button></form>'}
              {'' if not product[5] else f'<form method="post" action="/mark_unsold"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-yellow-500 text-black px-4 py-2 rounded-lg hover:bg-yellow-600 btn">❌ Отметить как не продан</button></form>'}
              <form method="post" action="/delete_product"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 btn">🗑️ Удалить</button></form>
            </div>
          </div>
          <hr class="border-gray-700 my-6">
          <a href="/admin/products" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn w-full text-center">⬅️ Назад</a>
          <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
            <a href="/admin/products" class="text-gray-300 hover:text-orange-500">📦 Товары</a>
            <a href="/admin/all_products" class="text-gray-300 hover:text-orange-500">📋 Все товары</a>
            <a href="/admin/lots" class="text-gray-300 hover:text-orange-500">🏆 Лоты</a>
          </div>
        </div>
        """
        return html
    return admin_product

def admin_all_products():
    from webapp import app
    @app.route('/admin/all_products')
    def admin_all_products():
        if not is_admin():
            return redirect('/login')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products ORDER BY id DESC')
        products = c.fetchall()
        conn.close()

        html = TAILWIND + """
        <div class="container mx-auto pt-10 pb-10 px-4">
          <h2 class="text-3xl font-bold text-purple-500 mb-6">📋 Все товары</h2>
          <div class="mb-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <input id="searchInput" type="text" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Поиск по ID, названию или описанию" onkeyup="searchItems('allItemsTable')">
            <select id="typeFilter" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" onchange="filterItemsByType('allItemsTable')">
              <option value="all">Все</option>
              <option value="weapon">Оружия</option>
              <option value="agent">Агенты</option>
            </select>
          </div>
          <div class="overflow-x-auto">
            <table id="allItemsTable" class="w-full bg-gray-800 text-gray-300 rounded-lg">
              <thead><tr class="bg-gray-900"><th class="p-3">ID</th><th class="p-3">Фото</th><th class="p-3">Название</th><th class="p-3">Описание</th><th class="p-3">Цена</th><th class="p-3">Кол-во</th><th class="p-3">Float</th><th class="p-3">Trade Ban</th><th class="p-3">Тип</th><th class="p-3">Статус</th><th class="p-3">Действия</th></tr></thead>
              <tbody>
        """
        
        if products:
            for product in products:
                status = '✅ Продан' if product[5] else '🟢 В продаже'
                float_text = f"{product[7]:.4f}" if product[7] is not None and product[9] == 'weapon' else "N/A"
                ban_text = 'Да' if product[8] else 'Нет'
                type_text = 'Оружие' if product[9] == 'weapon' else 'Агент'
                img_html = f'<img src="/static/images/{product[6]}" class="w-16 h-16 rounded-lg object-cover" alt="{product[1]}">' if product[6] else ""
                html += f"""
                <tr class="border-b border-gray-700">
                  <td class="p-3"><a href="/admin/product/{product[0]}" class="text-blue-500 hover:underline">{product[0]}</a></td>
                  <td class="p-3">{img_html}</td>
                  <td class="p-3">{product[1]}</td>
                  <td class="p-3">{product[2]}</td>
                  <td class="p-3">{product[3]}₽</td>
                  <td class="p-3">{product[4]}</td>
                  <td class="p-3">{float_text}</td>
                  <td class="p-3">{ban_text}</td>
                  <td class="p-3">{type_text}</td>
                  <td class="p-3">{status}</td>
                  <td class="p-3">
                    <div class="flex flex-col gap-2">
                      {'' if product[5] else f'<form method="post" action="/mark_sold"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 btn text-sm">✅ Продан</button></form>'}
                      {'' if not product[5] else f'<form method="post" action="/mark_unsold"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-yellow-500 text-black px-3 py-1 rounded hover:bg-yellow-600 btn text-sm">❌ Не продан</button></form>'}
                      <form method="post" action="/delete_product"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 btn text-sm">🗑️ Удалить</button></form>
                    </div>
                  </td>
                </tr>
                """
        else:
            html += """
            <tr>
              <td colspan="11" class="p-3 text-center text-gray-400">Нет товаров</td>
            </tr>
            """
        
        html += """
              </tbody>
            </table>
          </div>
          <hr class="border-gray-700 my-6">
          <a href="/" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 btn w-full text-center">⬅️ Назад</a>
          <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-3 md:hidden">
            <a href="/admin/products" class="text-gray-300 hover:text-orange-500">📦 Товары</a>
            <a href="/admin/all_products" class="text-gray-300 hover:text-orange-500">📋 Все товары</a>
            <a href="/admin/lots" class="text-gray-300 hover:text-orange-500">🏆 Лоты</a>
          </div>
        </div>
        """
        return html
    return admin_all_products

def admin_products():
    from webapp import app
    @app.route('/admin/products')
    def admin_products():
        if not is_admin():
            return redirect('/login')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products ORDER BY id DESC LIMIT 1')
        product = c.fetchone()
        conn.close()
        html = TAILWIND + """
        <div class="container mx-auto pt-10 pb-10 px-4">
          <h2 class="text-3xl font-bold text-gray-300 mb-6">📦 Последний товар</h2>
          <div class="overflow-x-auto">
            <table id="productsTable" class="w-full bg-gray-800 text-gray-300 rounded-lg">
              <thead><tr class="bg-gray-900"><th class="p-3">ID</th><th class="p-3">Фото</th><th class="p-3">Название</th><th class="p-3">Описание</th><th class="p-3">Цена</th><th class="p-3">Кол-во</th><th class="p-3">Float</th><th class="p-3">Trade Ban</th><th class="p-3">Тип</th><th class="p-3">Статус</th><th class="p-3">Действия</th></tr></thead>
              <tbody>
        """
        if product:
            status = '✅ Продан' if product[5] else '🟢 В продаже'
            float_text = f"{product[7]:.4f}" if product[7] is not None and product[9] == 'weapon' else "N/A"
            ban_text = 'Да' if product[8] else 'Нет'
            type_text = 'Оружие' if product[9] == 'weapon' else 'Агент'
            img_html = f'<img src="/static/images/{product[6]}" class="w-16 h-16 rounded-lg object-cover" alt="{product[1]}">' if product[6] else ""
            html += f"""
            <tr class="border-b border-gray-700">
              <td class="p-3"><a href="/admin/product/{product[0]}" class="text-blue-500 hover:underline">{product[0]}</a></td>
              <td class="p-3">{img_html}</td>
              <td class="p-3">{product[1]}</td>
              <td class="p-3">{product[2]}</td>
              <td class="p-3">{product[3]}₽</td>
              <td class="p-3">{product[4]}</td>
              <td class="p-3">{float_text}</td>
              <td class="p-3">{ban_text}</td>
              <td class="p-3">{type_text}</td>
              <td class="p-3">{status}</td>
              <td class="p-3">
                <div class="flex flex-col gap-2">
                  {'' if product[5] else f'<form method="post" action="/mark_sold"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 btn text-sm">✅ Продан</button></form>'}
                  {'' if not product[5] else f'<form method="post" action="/mark_unsold"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-yellow-500 text-black px-3 py-1 rounded hover:bg-yellow-600 btn text-sm">❌ Не продан</button></form>'}
                  <form method="post" action="/delete_product"><input type="hidden" name="product_id" value="{product[0]}"><button class="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 btn text-sm">🗑️ Удалить</button></form>
                </div>
              </td>
            </tr>
            """
        else:
            html += """
            <tr>
              <td colspan="11" class="p-3 text-center text-gray-400">Нет товаров</td>
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
            <a href="/admin/all_products" class="text-gray-300 hover:text-orange-500">📋 Все товары</a>
            <a href="/admin/lots" class="text-gray-300 hover:text-orange-500">🏆 Лоты</a>
          </div>
        </div>
        """
        return html
    return admin_products

def admin_lots():
    from webapp import app
    @app.route('/admin/lots')
    def admin_lots():
        if not is_admin():
            return redirect('/login')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, description, current_price, end_time, step, active, image, float_value, trade_ban, type FROM lots ORDER BY id DESC LIMIT 1')
        lot = c.fetchone()
        conn.close()
        html = TAILWIND + """
        <div class="container mx-auto pt-10 pb-10 px-4">
          <h2 class="text-3xl font-bold text-blue-500 mb-6">🏆 Последний лот</h2>
          <div class="overflow-x-auto">
            <table class="w-full bg-gray-800 text-gray-300 rounded-lg">
              <thead><tr class="bg-gray-900"><th class="p-3">Фото</th><th class="p-3">Название</th><th class="p-3">Описание</th><th class="p-3">Ставка</th><th class="p-3">До конца</th><th class="p-3">Float</th><th class="p-3">TradeheBan</th><th class="p-3">Тип</th><th class="p-3">Статус</th><th class="p-3">Действия</th></tr></thead>
              <tbody>
        """
        if lot:
            time_left = "Без ограничения" if lot[4] is None else f"{max(0, lot[4] - int(time.time()))//60} мин {max(0, lot[4] - int(time.time()))%60} сек"
            status = '🟢 Активен' if lot[6] else '⛔ Остановлен'
            float_text = f"{lot[8]:.4f}" if lot[8] is not None and lot[10] == 'weapon' else "N/A"
            ban_text = 'Да' if lot[9] else 'Нет'
            type_text = 'Оружие' if lot[10] == 'weapon' else 'Агент'
            img_html = f'<img src="/static/images/{lot[7]}" class="w-16 h-16 rounded-lg object-cover" alt="{lot[1]}">' if lot[7] else ""
            html += f"""
            <tr class="border-b border-gray-700">
              <td class="p-3">{img_html}</td>
              <td class="p-3">{lot[1]}</td>
              <td class="p-3">{lot[2]}</td>
              <td class="p-3">{lot[3]}₽</td>
              <td class="p-3">{time_left}</td>
              <td class="p-3">{float_text}</td>
              <td class="p-3">{ban_text}</td>
              <td class="p-3">{type_text}</td>
              <td class="p-3">{status}</td>
              <td class="p-3">
                <div class="flex flex-col gap-2">
                  {'' if not lot[6] else f'<form method="post" action="/stop_lot"><input type="hidden" name="lot_id" value="{lot[0]}"><button class="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 btn text-sm">⛔ Остановить</button></form>'}
                  <form method="post" action="/delete_lot"><input type="hidden" name="lot_id" value="{lot[0]}"><button class="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700 btn text-sm">🗑️ Удалить</button></form>
                </div>
              </td>
            </tr>
            """
        else:
            html += """
            <tr>
              <td colspan="10" class="p-3 text-center text-gray-400">Нет лотов</td>
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
              <input name="minutes" type="number" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600" placeholder="Время аукциона (минуты, оставьте пустым для бесконечного)">
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
            <a href="/admin/all_products" class="text-gray-300 hover:text-orange-500">📋 Все товары</a>
            <a href="/admin/lots" class="text-gray-300 hover:text-orange-500">🏆 Лоты</a>
          </div>
        </div>
        """
        return html
    return admin_lots

def add_product():
    from webapp import app
    @app.route('/add_product', methods=['POST'])
    def add_product():
        if not is_admin(): 
            return redirect('/login')
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
    return add_product

def add_lot():
    from webapp import app
    @app.route('/add_lot', methods=['POST'])
    def add_lot():
        if not is_admin(): 
            return redirect('/login')
        name = request.form['name']
        desc = request.form['description']
        start_price = int(request.form['start_price'])
        step = int(request.form['step'])
        minutes = request.form.get('minutes')
        end_time = int(time.time() + int(minutes) * 60) if minutes else None
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
        c.execute('INSERT INTO lots (name, description, start_price, step, end_time, current_price, image, float_value, trade_ban, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                  (name, desc, start_price, step, end_time, start_price, image_name, float_value, trade_ban, item_type))
        conn.commit()
        conn.close()
        logging.info(f"Добавлен лот: {name}, {start_price}, {step}, Type: {item_type}, Float: {float_value}, Trade Ban: {trade_ban}, Image: {image_name}")
        return redirect('/admin/lots')
    return add_lot

def mark_sold():
    from webapp import app
    @app.route('/mark_sold', methods=['POST'])
    def mark_sold():
        if not is_admin():
            return redirect('/login')
        product_id = int(request.form['product_id'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE products SET sold=1, quantity=0 WHERE id=?', (product_id,))
        conn.commit()
        conn.close()
        logging.info(f"Товар помечен как продан: ID {product_id}")
        return redirect('/admin/products')
    return mark_sold

def mark_unsold():
    from webapp import app
    @app.route('/mark_unsold', methods=['POST'])
    def mark_unsold():
        if not is_admin():
            return redirect('/login')
        product_id = int(request.form['product_id'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE products SET sold=0, quantity=1 WHERE id=?', (product_id,))
        conn.commit()
        conn.close()
        logging.info(f"Товар помечен как не продан: ID {product_id}")
        return redirect('/admin/products')
    return mark_unsold

def delete_product():
    from webapp import app
    @app.route('/delete_product', methods=['POST'])
    def delete_product():
        if not is_admin():
            return redirect('/login')
        product_id = int(request.form['product_id'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
        conn.close()
        logging.info(f"Товар удален: ID {product_id}")
        return redirect('/admin/products')
    return delete_product

def stop_lot():
    from webapp import app
    @app.route('/stop_lot', methods=['POST'])
    def stop_lot():
        if not is_admin():
            return redirect('/login')
        lot_id = int(request.form['lot_id'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT name, current_price, winner_id, float_value, trade_ban, type FROM lots WHERE id=?', (lot_id,))
        lot = c.fetchone()
        c.execute('UPDATE lots SET active=0 WHERE id=?', (lot_id,))
        conn.commit()
        conn.close()
        if lot:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(notify_admins_auction(lot_id, lot[0], lot[1], lot[2], lot[3], lot[4], lot[5]))
            loop.close()
        logging.info(f"Лот остановлен: ID {lot_id}")
        return redirect('/admin/lots')
    return stop_lot

def delete_lot():
    from webapp import app
    @app.route('/delete_lot', methods=['POST'])
    def delete_lot():
        if not is_admin():
            return redirect('/login')
        lot_id = int(request.form['lot_id'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM lots WHERE id=?', (lot_id,))
        conn.commit()
        conn.close()
        logging.info(f"Лот удален: ID {lot_id}")
        return redirect('/admin/lots')
    return delete_lot

admin_product()
admin_all_products()
admin_products()
add_product()
add_lot()
mark_sold()
mark_unsold()
delete_product()
stop_lot()
delete_lot()