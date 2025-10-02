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

# Translations dictionary
TRANSLATIONS = {
    'ru': {
        'title': 'CSGO Saller',
        'welcome_title': 'Добро пожаловать!',
        'welcome_message': 'Спасибо за посещение CSGO Saller! Здесь вы можете купить скины, участвовать в аукционах и наслаждаться безопасной торговлей.',
        'home': '🏠 Главная',
        'shop': '🛒 Магазин',
        'auction': '🏆 Аукцион',
        'admin_panel': '🔑 Админ-панель',
        'start': '🚀 Начать',
        'back': '⬅️ Назад',
        'shop_title': 'Магазин',
        'product_not_found': 'Товар не найден.',
        'product_id': 'Товар ID',
        'price': '💰 Цена',
        'quantity': '📦 Количество',
        'float': '🔢 Float',
        'trade_ban': '🚫 Trade Ban',
        'type': '🎮 Тип',
        'product_link': '🔗 Ссылка на товар',
        'send_to_admin': '📋 Отправьте эту ссылку и вашу трейд-ссылку администратору в Telegram!',
        'contact_admin': '📩 Написать админу',
        'return_to_shop': '⬅️ Вернуться в магазин',
        'buy_error_no_id': 'Ошибка: ID товара не указан.',
        'buy_error_unavailable': 'Товар недоступен.',
        'buy_success': '✅ Заявка на покупку отправлена администратору!',
        'auction_title': 'Аукцион',
        'lot_unavailable': 'Лот недоступен.',
        'bid_too_low': 'Сумма слишком мала.',
        'current_bid': '💰 Текущая ставка',
        'time_left': '⏳ До конца',
        'bid_step': '🔼 Ставка +',
        'custom_bid': '💸 Ввести сумму',
        'bid_placeholder': 'Ваша ставка (₽)',
        'no_limit': 'Без ограничения',
        'weapon': 'Оружие',
        'agent': 'Агент',
        'yes': 'Да',
        'no': 'Нет',
        'na': 'N/A',
        'language': 'Язык',
        'russian': 'Русский',
        'uzbek': 'O‘zbek'
    },
    'uz': {
        'title': 'CSGO Saller',
        'welcome_title': 'Xush kelibsiz!',
        'welcome_message': 'CSGO Saller’ga tashrif buyurganingiz uchun rahmat! Bu yerda siz skinlarni sotib olishingiz, auktsionlarda ishtirok etishingiz va xavfsiz savdo qilishingiz mumkin.',
        'home': '🏠 Bosh sahifa',
        'shop': '🛒 Do‘kon',
        'auction': '🏆 Auktsion',
        'admin_panel': '🔑 Admin paneli',
        'start': '🚀 Boshlash',
        'back': '⬅️ Orqaga',
        'shop_title': 'Do‘kon',
        'product_not_found': 'Mahsulot topilmadi.',
        'product_id': 'Mahsulot ID',
        'price': '💰 Narx',
        'quantity': '📦 Soni',
        'float': '🔢 Float',
        'trade_ban': '🚫 Savdo taqiqlangan',
        'type': '🎮 Turi',
        'product_link': '🔗 Mahsulot havolasi',
        'send_to_admin': '📋 Ushbu havolani va savdo havolangizni Telegram orqali administratorga yuboring!',
        'contact_admin': '📩 Administratorga yozish',
        'return_to_shop': '⬅️ Do‘konga qaytish',
        'buy_error_no_id': 'Xato: Mahsulot ID kiritilmagan.',
        'buy_error_unavailable': 'Mahsulot mavjud emas.',
        'buy_success': '✅ Sotib olish so‘rovi administratorga yuborildi!',
        'auction_title': 'Auktsion',
        'lot_unavailable': 'Lot mavjud emas.',
        'bid_too_low': 'Summa juda past.',
        'current_bid': '💰 Joriy stavka',
        'time_left': '⏳ Tugash vaqti',
        'bid_step': '🔼 Stavka +',
        'custom_bid': '💸 Summa kiritish',
        'bid_placeholder': 'Sizning stavkangiz (₽)',
        'no_limit': 'Cheklovsiz',
        'weapon': 'Qurol',
        'agent': 'Agent',
        'yes': 'Ha',
        'no': 'Yo‘q',
        'na': 'Mavjud emas',
        'language': 'Til',
        'russian': 'Ruscha',
        'uzbek': 'O‘zbek'
    }
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    user_id = session.get('user_id', None)
    lang = request.args.get('lang', 'ru')
    logging.info(f"Login route: user_id={user_id}, lang={lang}")
    if user_id in ADMIN_IDS:
        logging.info("User is admin, redirecting to /admin/products")
        return redirect(url_for('admin_products', lang=lang))
    logging.info("User not admin, redirecting to /")
    return redirect(url_for('index', lang=lang))

@app.route('/')
def index():
    user_id = session.get('user_id', None)
    lang = request.args.get('lang', 'ru')
    if lang not in ['ru', 'uz']:
        lang = 'ru'
    logging.info(f"Index route: session user_id={user_id}, query user_id={request.args.get('user_id', None)}, lang={lang}")
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
    t = TRANSLATIONS[lang]
    html = TAILWIND + """
    <div class="container mx-auto pt-12 pb-10 px-4 text-center bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
      <header class="flex justify-between items-center mb-8">
        <h1 class="text-4xl md:text-5xl font-extrabold text-orange-500 animate-pulse">{}</h1>
        <div class="relative">
          <select onchange="window.location.href='/?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500">
            <option value="ru" {}>{}</option>
            <option value="uz" {}>{}</option>
          </select>
        </div>
      </header>
      <p class="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl mx-auto">{}</p>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10 max-w-4xl mx-auto">
        <button onclick="openModal('welcome', '{}', '{}', 0, 0, null, 0, 'welcome')" class="bg-orange-500 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-orange-600 transform hover:scale-105 transition duration-300 btn">{}</button>
        <a href="/shop?lang={}" class="bg-green-600 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-green-700 transform hover:scale-105 transition duration-300 btn">{}</a>
        <a href="/auction?lang={}" class="bg-blue-600 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-blue-700 transform hover:scale-105 transition duration-300 btn">{}</a>
      </div>
    """.format(
        t['title'],
        'selected' if lang == 'ru' else '',
        t['russian'],
        'selected' if lang == 'uz' else '',
        t['uzbek'],
        t['welcome_message'],
        t['welcome_title'],
        t['welcome_message'],
        t['start'],
        lang,
        t['shop'],
        lang,
        t['auction']
    )
    if user_id in ADMIN_IDS:
        html += '<a href="/admin/products?lang={}" class="bg-gray-700 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:bg-gray-600 transform hover:scale-105 transition duration-300 btn inline-block">{}</a>'.format(lang, t['admin_panel'])
    html += """
      <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div id="modalContent" class="max-w-md w-full"></div>
      </div>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
        <a href="/?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
        <a href="/shop?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
        <a href="/auction?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
      </div>
    </div>
    """.format(lang, t['home'], lang, t['shop'], lang, t['auction'])
    return html

@app.route('/shop')
def shop():
    user_id = session.get('user_id', None)
    lang = request.args.get('lang', 'ru')
    if lang not in ['ru', 'uz']:
        lang = 'ru'
    t = TRANSLATIONS[lang]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products WHERE sold=0 AND quantity>0')
    products = c.fetchall()
    conn.close()
    html = TAILWIND + """
    <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
      <header class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold text-green-500">{}</h2>
        <div class="relative">
          <select onchange="window.location.href='/shop?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
            <option value="ru" {}>{}</option>
            <option value="uz" {}>{}</option>
          </select>
        </div>
      </header>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
    """.format(
        t['shop_title'],
        'selected' if lang == 'ru' else '',
        t['russian'],
        'selected' if lang == 'uz' else '',
        t['uzbek']
    )
    for p in products:
        img_html = '<img src="/static/images/{}" class="mb-4 w-full rounded-lg object-cover shadow-md animate-fade-in" style="max-height:180px;" alt="{}">'.format(p[6], p[1]) if p[6] else ""
        float_text = "{}: {:.4f}".format(t['float'], p[7]) if p[7] is not None and p[9] == 'weapon' else "{}: {}".format(t['float'], t['na'])
        ban_text = "{}: {}".format(t['trade_ban'], t['yes'] if p[8] else t['no'])
        type_text = "{}: {}".format(t['type'], t['weapon'] if p[9] == 'weapon' else t['agent'])
        product_link = f"https://csgosaller-1.onrender.com/product/{p[0]}"
        escaped_name = p[1].replace("'", "\\'")
        escaped_desc = p[2].replace("'", "\\'")
        html += """
        <div class="bg-gray-800 rounded-lg p-4 card shadow-lg hover:shadow-xl transition duration-300 animate-fade-in">
          {}
          <h5 class="text-xl font-bold text-green-500 mb-2">{}</h5>
          <p class="text-gray-300 text-sm mb-2">{}</p>
          <p class="text-sm text-gray-400 mb-2">{}: {}</p>
          <p class="mt-2"><span class="bg-yellow-500 text-black px-2 py-1 rounded">{}: {}₽</span> <span class="bg-blue-500 text-white px-2 py-1 rounded ml-2">{}: {}</span></p>
          <p class="mt-2 text-sm text-gray-400">{} | {} | {}</p>
          <button onclick="openModal({}, '{}', '{}', {}, {}, {}, {}, '{}')" class="bg-green-600 text-white w-full py-2 rounded-lg hover:bg-green-700 transform hover:scale-105 transition duration-300 btn mt-4 text-sm">{}</button>
        </div>
        """.format(
            img_html,
            p[1],
            p[2],
            t['product_id'],
            p[0],
            t['price'],
            p[3],
            t['quantity'],
            p[4],
            float_text,
            ban_text,
            type_text,
            p[0],
            escaped_name,
            escaped_desc,
            p[3],
            p[4],
            p[7] if p[7] is not None else 'null',
            p[8],
            p[9],
            t['contact_admin']
        )
    html += """
      </div>
      <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div id="modalContent" class="max-w-md w-full"></div>
      </div>
      <hr class="border-gray-700 my-8">
      <a href="/?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn w-full text-center">{}</a>
      <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
        <a href="/?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
        <a href="/auction?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
      </div>
    </div>
    """.format(lang, t['back'], lang, t['home'], lang, t['auction'])
    return html

@app.route('/product/<int:product_id>')
def product(product_id):
    lang = request.args.get('lang', 'ru')
    if lang not in ['ru', 'uz']:
        lang = 'ru'
    t = TRANSLATIONS[lang]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, quantity, sold, image, float_value, trade_ban, type FROM products WHERE id=?', (product_id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        return TAILWIND + """
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
            <header class="flex justify-between items-center mb-8">
              <h2 class="text-3xl font-bold text-red-500">{}</h2>
              <div class="relative">
                <select onchange="window.location.href='/shop?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                  <option value="ru" {}>{}</option>
                  <option value="uz" {}>{}</option>
                </select>
              </div>
            </header>
            <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">{}</div>
            <a href="/shop?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
        </div>
        """.format(
            t['shop_title'],
            'selected' if lang == 'ru' else '',
            t['russian'],
            'selected' if lang == 'uz' else '',
            t['uzbek'],
            t['product_not_found'],
            lang,
            t['return_to_shop']
        )
    
    float_text = "{}: {:.4f}".format(t['float'], product[7]) if product[7] is not None and product[9] == 'weapon' else "{}: {}".format(t['float'], t['na'])
    ban_text = "{}: {}".format(t['trade_ban'], t['yes'] if product[8] else t['no'])
    type_text = "{}: {}".format(t['type'], t['weapon'] if product[9] == 'weapon' else t['agent'])
    img_html = '<img src="/static/images/{}" class="w-full rounded-lg object-cover mb-4 shadow-md animate-fade-in" style="max-height:300px;" alt="{}">'.format(product[6], product[1]) if product[6] else ""
    product_link = f"https://csgosaller-1.onrender.com/product/{product[0]}"
    admin_url = f"https://t.me/{ADMIN_USERNAME}" if not ADMIN_USERNAME.startswith('+') else f"https://t.me/{ADMIN_USERNAME}"
    
    html = TAILWIND + """
    <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
        <header class="flex justify-between items-center mb-8">
          <h2 class="text-3xl font-bold text-green-500">{}: {}</h2>
          <div class="relative">
            <select onchange="window.location.href='/product/{}?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
              <option value="ru" {}>{}</option>
              <option value="uz" {}>{}</option>
            </select>
          </div>
        </header>
        <div class="bg-gray-800 rounded-lg p-6 card shadow-lg hover:shadow-xl transition duration-300 animate-fade-in">
            {}
            <h3 class="text-2xl font-bold text-green-500 mb-2">{}</h3>
            <p class="text-gray-300 text-sm mb-2">{}</p>
            <p class="text-gray-300 text-sm mb-2">{}: {}₽</p>
            <p class="text-gray-300 text-sm mb-2">{}: {}</p>
            <p class="text-gray-300 text-sm mb-2">{}</p>
            <p class="text-gray-300 text-sm mb-2">{}</p>
            <p class="text-gray-300 text-sm mb-3">{}</p>
            <p class="text-gray-300 text-sm mb-3">{}: <a href="{}" class="text-blue-500 hover:underline">{}</a></p>
            <p class="text-gray-300 text-sm mb-3">{}</p>
            <a href="{}" class="bg-green-600 text-white w-full py-2 rounded-lg hover:bg-green-700 transform hover:scale-105 transition duration-300 btn text-center block text-sm">{}</a>
            <a href="/shop?lang={}" class="bg-gray-800 text-white w-full py-2 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-2 text-sm text-center">{}</a>
        </div>
        <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
            <a href="/shop?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
            <a href="/auction?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
        </div>
    </div>
    """.format(
        t['product_id'],
        product[0],
        product[0],
        'selected' if lang == 'ru' else '',
        t['russian'],
        'selected' if lang == 'uz' else '',
        t['uzbek'],
        img_html,
        product[1],
        product[2],
        t['price'],
        product[3],
        t['quantity'],
        product[4],
        float_text,
        ban_text,
        type_text,
        t['product_link'],
        product_link,
        product_link,
        t['send_to_admin'],
        admin_url,
        t['contact_admin'],
        lang,
        t['return_to_shop'],
        lang,
        t['shop'],
        lang,
        t['auction']
    )
    return html

@app.route('/buy', methods=['POST'])
def buy():
    lang = request.args.get('lang', 'ru')
    if lang not in ['ru', 'uz']:
        lang = 'ru'
    t = TRANSLATIONS[lang]
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
            return TAILWIND + """
            <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
                <header class="flex justify-between items-center mb-8">
                  <div></div>
                  <div class="relative">
                    <select onchange="window.location.href='/shop?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                      <option value="ru" {}>{}</option>
                      <option value="uz" {}>{}</option>
                    </select>
                  </div>
                </header>
                <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">{}</div>
                <a href="/shop?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
            </div>
            """.format(
                'selected' if lang == 'ru' else '',
                t['russian'],
                'selected' if lang == 'uz' else '',
                t['uzbek'],
                t['buy_error_no_id'],
                lang,
                t['back']
            )
        
        pid = int(product_id)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT name, description, price, quantity, float_value, trade_ban, type FROM products WHERE id=? AND sold=0 AND quantity>0', (pid,))
        prod = c.fetchone()
        logging.info(f"Результат запроса к products: {prod}")
        
        if not prod:
            conn.close()
            logging.error(f"Товар недоступен: id={pid}, prod={prod}")
            return TAILWIND + """
            <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
                <header class="flex justify-between items-center mb-8">
                  <div></div>
                  <div class="relative">
                    <select onchange="window.location.href='/shop?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                      <option value="ru" {}>{}</option>
                      <option value="uz" {}>{}</option>
                    </select>
                  </div>
                </header>
                <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">{}</div>
                <a href="/shop?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
            </div>
            """.format(
                'selected' if lang == 'ru' else '',
                t['russian'],
                'selected' if lang == 'uz' else '',
                t['uzbek'],
                t['buy_error_unavailable'],
                lang,
                t['back']
            )
        
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
        return TAILWIND + """
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
            <header class="flex justify-between items-center mb-8">
              <div></div>
              <div class="relative">
                <select onchange="window.location.href='/shop?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500">
                  <option value="ru" {}>{}</option>
                  <option value="uz" {}>{}</option>
                </select>
              </div>
            </header>
            <div class="bg-green-600 text-white p-4 rounded-lg shadow-lg">{}</div>
            <a href="/?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
        </div>
        """.format(
            'selected' if lang == 'ru' else '',
            t['russian'],
            'selected' if lang == 'uz' else '',
            t['uzbek'],
            t['buy_success'],
            lang,
            t['back']
        )
    
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"Ошибка в /buy: {str(e)}")
        return TAILWIND + """
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
            <header class="flex justify-between items-center mb-8">
              <div></div>
              <div class="relative">
                <select onchange="window.location.href='/shop?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                  <option value="ru" {}>{}</option>
                  <option value="uz" {}>{}</option>
                </select>
              </div>
            </header>
            <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">{}: {}</div>
            <a href="/shop?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
        </div>
        """.format(
            'selected' if lang == 'ru' else '',
            t['russian'],
            'selected' if lang == 'uz' else '',
            t['uzbek'],
            t['buy_error_unavailable'],
            str(e),
            lang,
            t['back']
        )

@app.route('/auction', methods=['GET'])
def auction():
    lang = request.args.get('lang', 'ru')
    if lang not in ['ru', 'uz']:
        lang = 'ru'
    t = TRANSLATIONS[lang]
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
          <header class="flex justify-between items-center mb-8">
            <h2 class="text-3xl font-bold text-blue-500">{}</h2>
            <div class="relative">
              <select onchange="window.location.href='/auction?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="ru" {}>{}</option>
                <option value="uz" {}>{}</option>
              </select>
            </div>
          </header>
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        """.format(
            t['auction_title'],
            'selected' if lang == 'ru' else '',
            t['russian'],
            'selected' if lang == 'uz' else '',
            t['uzbek']
        )
        for l in lots:
            time_left = t['no_limit'] if l[4] is None else "{} {} {} {}".format(max(0, l[4] - int(time.time()))//60, t['time_left'].split(' ')[1], max(0, l[4] - int(time.time()))%60, t['time_left'].split(' ')[3])
            img_html = '<img src="/static/images/{}" class="mb-4 w-full rounded-lg object-cover shadow-md animate-fade-in" style="max-height:180px;" alt="{}">'.format(l[7], l[1]) if l[7] else ""
            float_text = "{}: {:.4f}".format(t['float'], l[8]) if l[8] is not None and l[10] == 'weapon' else "{}: {}".format(t['float'], t['na'])
            ban_text = "{}: {}".format(t['trade_ban'], t['yes'] if l[9] else t['no'])
            type_text = "{}: {}".format(t['type'], t['weapon'] if l[10] == 'weapon' else t['agent'])
            html += """
            <div class="bg-gray-800 rounded-lg p-4 card shadow-lg hover:shadow-xl transition duration-300 animate-fade-in">
              {}
              <h5 class="text-xl font-bold text-blue-500 mb-2">{}</h5>
              <p class="text-gray-300 text-sm mb-2">{}</p>
              <p class="mt-2"><span class="bg-yellow-500 text-black px-2 py-1 rounded">{}: {}₽</span></p>
              <p class="mt-2"><span class="bg-gray-600 text-white px-2 py-1 rounded">{}: {}</span></p>
              <p class="mt-2 text-sm text-gray-400">{} | {} | {}</p>
              <form method="post" action="/bid" class="mt-4">
                <input type="hidden" name="lot_id" value="{}">
                <input type="hidden" name="step" value="{}">
                <input type="hidden" name="lang" value="{}">
                <button type="submit" class="bg-yellow-500 text-black w-full py-2 rounded-lg hover:bg-yellow-600 transform hover:scale-105 transition duration-300 btn">{} {}₽</button>
              </form>
              <form method="post" action="/bid_custom" class="mt-2">
                <input type="hidden" name="lot_id" value="{}">
                <input type="hidden" name="lang" value="{}">
                <input type="number" name="amount" class="bg-gray-700 text-white w-full p-2 rounded border border-gray-600 mb-2" placeholder="{}" min="{}" required>
                <button type="submit" class="bg-blue-600 text-white w-full py-2 rounded-lg hover:bg-blue-700 transform hover:scale-105 transition duration-300 btn">{}</button>
              </form>
            </div>
            """.format(
                img_html,
                l[1],
                l[2],
                t['current_bid'],
                l[3],
                t['time_left'],
                time_left,
                float_text,
                ban_text,
                type_text,
                l[0],
                l[5],
                lang,
                t['bid_step'],
                l[5],
                l[0],
                lang,
                t['bid_placeholder'],
                l[3]+l[5],
                t['custom_bid']
            )
        html += """
          </div>
          <hr class="border-gray-700 my-8">
          <a href="/?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn w-full text-center">{}</a>
          <div class="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 flex justify-around py-4 md:hidden">
            <a href="/?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
            <a href="/shop?lang={}" class="text-gray-300 hover:text-orange-500 text-sm font-medium">{}</a>
          </div>
        </div>
        """.format(lang, t['back'], lang, t['home'], lang, t['shop'])
        return html
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"Ошибка в /auction: {str(e)}")
        return TAILWIND + """
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
            <header class="flex justify-between items-center mb-8">
              <div></div>
              <div class="relative">
                <select onchange="window.location.href='/auction?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                  <option value="ru" {}>{}</option>
                  <option value="uz" {}>{}</option>
                </select>
              </div>
            </header>
            <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">{}: {}</div>
            <a href="/?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
        </div>
        """.format(
            'selected' if lang == 'ru' else '',
            t['russian'],
            'selected' if lang == 'uz' else '',
            t['uzbek'],
            t['buy_error_unavailable'],
            str(e),
            lang,
            t['back']
        )

@app.route('/bid', methods=['POST'])
def bid():
    lang = request.form.get('lang', 'ru')
    if lang not in ['ru', 'uz']:
        lang = 'ru'
    t = TRANSLATIONS[lang]
    user_id = session.get('user_id', None)
    if not user_id:
        return redirect(url_for('login', lang=lang))
    lot_id = int(request.form['lot_id'])
    step = int(request.form['step'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT current_price, end_time FROM lots WHERE id=? AND active=1', (lot_id,))
    lot = c.fetchone()
    if not lot:
        conn.close()
        return TAILWIND + """
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
            <header class="flex justify-between items-center mb-8">
              <div></div>
              <div class="relative">
                <select onchange="window.location.href='/auction?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                  <option value="ru" {}>{}</option>
                  <option value="uz" {}>{}</option>
                </select>
              </div>
            </header>
            <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">{}</div>
            <a href="/auction?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
        </div>
        """.format(
            'selected' if lang == 'ru' else '',
            t['russian'],
            'selected' if lang == 'uz' else '',
            t['uzbek'],
            t['lot_unavailable'],
            lang,
            t['back']
        )
    new_price = lot[0] + step
    c.execute('UPDATE lots SET current_price=? WHERE id=?', (new_price, lot_id))
    c.execute('INSERT INTO bids (lot_id, user_id, amount, time) VALUES (?, ?, ?, ?)', (lot_id, user_id, new_price, int(time.time())))
    conn.commit()
    conn.close()
    logging.info(f"Ставка: Лот {lot_id}, {new_price}, {user_id}")
    return redirect(url_for('auction', lang=lang))

@app.route('/bid_custom', methods=['POST'])
def bid_custom():
    lang = request.form.get('lang', 'ru')
    if lang not in ['ru', 'uz']:
        lang = 'ru'
    t = TRANSLATIONS[lang]
    user_id = session.get('user_id', None)
    if not user_id:
        return redirect(url_for('login', lang=lang))
    lot_id = int(request.form['lot_id'])
    amount = int(request.form['amount'])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT current_price, end_time, step FROM lots WHERE id=? AND active=1', (lot_id,))
    lot = c.fetchone()
    if not lot or amount < lot[0] + lot[2]:
        conn.close()
        return TAILWIND + """
        <div class="container mx-auto pt-12 pb-10 px-4 bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
            <header class="flex justify-between items-center mb-8">
              <div></div>
              <div class="relative">
                <select onchange="window.location.href='/auction?lang='+this.value" class="bg-gray-700 text-white p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500">
                  <option value="ru" {}>{}</option>
                  <option value="uz" {}>{}</option>
                </select>
              </div>
            </header>
            <div class="bg-red-600 text-white p-4 rounded-lg shadow-lg">{}</div>
            <a href="/auction?lang={}" class="bg-gray-800 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transform hover:scale-105 transition duration-300 btn mt-4 block text-center">{}</a>
        </div>
        """.format(
            'selected' if lang == 'ru' else '',
            t['russian'],
            'selected' if lang == 'uz' else '',
            t['uzbek'],
            t['bid_too_low'],
            lang,
            t['back']
        )
    c.execute('UPDATE lots SET current_price=? WHERE id=?', (amount, lot_id))
    c.execute('INSERT INTO bids (lot_id, user_id, amount, time) VALUES (?, ?, ?, ?)', (lot_id, user_id, amount, int(time.time())))
    conn.commit()
    conn.close()
    logging.info(f"Ставка: Лот {lot_id}, {amount}, {user_id}")
    return redirect(url_for('auction', lang=lang))