import os
import sqlite3
import logging
import asyncio
from threading import Thread
from telegram_bot import start_bot
from web_app import app

# Конфигурация
BOT_TOKEN = "7504123410:AAEznGqRafbyrBx2e34HzsxztWV201HRMxE"  # Замените на реальный токен
BOT_USERNAME = "UzSaler"  # Имя бота без @
ADMIN_IDS = [5266027747]  # Список ID админов
DB_PATH = "auction_shop.db"

# Логирование
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(message)s")

# Инициализация базы данных
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
    CREATE TABLE IF NOT EXISTS pending_requests (
        user_id INTEGER,
        product_id INTEGER,
        timestamp INTEGER,
        PRIMARY KEY (user_id, product_id)
    )""")
    conn.commit()
    conn.close()

# Запуск Flask в отдельном потоке
def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

async def main():
    # Инициализация базы данных
    init_db()
    logging.info("База данных инициализирована")

    # Запуск Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logging.info("Flask-приложение запущено")

    # Запуск Telegram-бота
    await start_bot(BOT_TOKEN)
    logging.info("Telegram-бот запущен")

if __name__ == "__main__":
    asyncio.run(main())