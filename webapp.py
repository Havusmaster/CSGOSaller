import os
import logging
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session
from templates import TAILWIND
from config import ADMIN_IDS, BOT_USERNAME, ADMIN_USERNAME
from database import DB_PATH
from telegram_bot import bot
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
    show_welcome = request.args.get('show_welcome', 'false') == 'true'
    html = TAILWIND + """
    <div class="container mx-auto pt-12 pb-10 px-4 text-center bg-gradient-to-b from-gray-900 to-gray-800 min-h-screen">
      <header class="flex justify-between items-center mb-8">
        <h1 class="text-4xl md:text-5xl font-extrabold text-orange-500 animate-pulse">{}</h1>
        <div class="relative">
          <select ...(truncated 25280 characters)... html
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

# Вот изменения: добавил persistent disk в render.yaml (чтобы db не стиралась), изменил DB_PATH в database.py, добавил вызов init_db() в bot.py (чтобы таблицы создавались на старте). В webapp.py расширил except в /shop, чтобы ловить ошибки и показывать их, а не 500.
# Остальные файлы (admin_routes.py, config.py, telegram_bot.py, templates.py) не менял, они как в твоих документах.
# Тести локально: python bot.py, зайди на /shop. Если ок — push на Render и redeploy. Если logs покажут что-то — кинь.