# database.py
"""
Модуль работы с SQLite.
Автоинициализация базы данных при импорте.
Хранит: товары (products), аукционы (auctions), ставки (bids).
"""

import sqlite3
from contextlib import closing
import time
from config import DB_PATH

# Создаём подключение при каждом вызове функции (простая и надёжная схема)
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создаёт таблицы, если их нет."""
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        # Таблица товаров
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            type TEXT NOT NULL, -- 'agent' или 'weapon'
            float_value REAL, -- nullable, только для оружия
            link TEXT,
            sold INTEGER DEFAULT 0,
            created_at INTEGER
        )
        """)
        # Таблица аукционов
        cur.execute("""
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_price REAL NOT NULL,
            step REAL NOT NULL,
            end_timestamp INTEGER NOT NULL,
            finished INTEGER DEFAULT 0,
            created_at INTEGER
        )
        """)
        # Таблица ставок
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auction_id INTEGER NOT NULL,
            bidder_identifier TEXT NOT NULL, -- @username or Telegram ID or any identifier from webapp
            amount REAL NOT NULL,
            created_at INTEGER,
            FOREIGN KEY(auction_id) REFERENCES auctions(id)
        )
        """)
        conn.commit()

# ----- Products -----
def add_product(name, description, price, type_, float_value=None, link=None):
    ts = int(time.time())
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO products (name, description, price, type, float_value, link, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price, type_, float_value, link, ts))
        conn.commit()
        return cur.lastrowid

def get_products(only_available=True):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        if only_available:
            cur.execute("SELECT * FROM products WHERE sold=0 ORDER BY id DESC")
        else:
            cur.execute("SELECT * FROM products ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]

def get_product(product_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def mark_product_sold(product_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE products SET sold=1 WHERE id=?", (product_id,))
        conn.commit()

def delete_product(product_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()

# ----- Auctions -----
def create_auction(title, description, start_price, step, end_timestamp):
    ts = int(time.time())
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO auctions (title, description, start_price, step, end_timestamp, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (title, description, start_price, step, end_timestamp, ts))
        conn.commit()
        return cur.lastrowid

def get_auctions(only_active=True):
    now = int(time.time())
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        if only_active:
            cur.execute("SELECT * FROM auctions WHERE finished=0 AND end_timestamp>? ORDER BY end_timestamp ASC", (now,))
        else:
            cur.execute("SELECT * FROM auctions ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]

def get_auction(auction_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM auctions WHERE id=?", (auction_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def finish_auction(auction_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE auctions SET finished=1 WHERE id=?", (auction_id,))
        conn.commit()

# ----- Bids -----
def place_bid(auction_id, bidder_identifier, amount):
    ts = int(time.time())
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO bids (auction_id, bidder_identifier, amount, created_at)
        VALUES (?, ?, ?, ?)
        """, (auction_id, bidder_identifier, amount, ts))
        conn.commit()
        return cur.lastrowid

def get_bids_for_auction(auction_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM bids WHERE auction_id=? ORDER BY amount DESC, created_at ASC", (auction_id,))
        return [dict(row) for row in cur.fetchall()]

def get_highest_bid(auction_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM bids WHERE auction_id=? ORDER BY amount DESC, created_at ASC LIMIT 1", (auction_id,))
        row = cur.fetchone()
        return dict(row) if row else None

# Инициализация базы при импортировании
init_db()
