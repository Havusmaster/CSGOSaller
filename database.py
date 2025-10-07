# database.py
"""
SQLite: хранение пользователей, товаров, аукционов и ставок.
Автоинициализация базы при импорте.
"""

import sqlite3
import time
from contextlib import closing
from config import DB_PATH, DEFAULT_LANG, DEFAULT_THEME

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        # users: настройки языка и темы
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT ?,
            theme TEXT DEFAULT ?,
            updated_at INTEGER
        )
        """, (DEFAULT_LANG, DEFAULT_THEME))
        # products
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            type TEXT NOT NULL,
            float_value REAL,
            link TEXT,
            sold INTEGER DEFAULT 0,
            created_at INTEGER
        )
        """)
        # auctions
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
        # bids
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auction_id INTEGER NOT NULL,
            bidder_identifier TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at INTEGER,
            FOREIGN KEY(auction_id) REFERENCES auctions(id)
        )
        """)
        conn.commit()

# --- Пользователи ---
def set_user_pref(tg_id: int, lang: str = None, theme: str = None):
    ts = int(time.time())
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        # если есть запись, обновим нужные поля
        cur.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
        if cur.fetchone():
            if lang:
                cur.execute("UPDATE users SET lang=?, updated_at=? WHERE tg_id=?", (lang, ts, tg_id))
            if theme:
                cur.execute("UPDATE users SET theme=?, updated_at=? WHERE tg_id=?", (theme, ts, tg_id))
        else:
            # вставим с явными значениями (если None — используем defaults)
            cur.execute("INSERT INTO users (tg_id, lang, theme, updated_at) VALUES (?, ?, ?, ?)",
                        (tg_id, lang or DEFAULT_LANG, theme or DEFAULT_THEME, ts))
        conn.commit()

def get_user_pref(tg_id: int):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
        row = cur.fetchone()
        if not row:
            # вернуть дефолт
            return {"tg_id": tg_id, "lang": DEFAULT_LANG, "theme": DEFAULT_THEME}
        return dict(row)

# === CRUD для товаров/аукционов/ставок (как раньше) ===
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
        return [dict(r) for r in cur.fetchall()]

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

# auctions / bids (те же функции, как в предыдущем варианте)
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
        return [dict(r) for r in cur.fetchall()]

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
        return [dict(r) for r in cur.fetchall()]

def get_highest_bid(auction_id):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM bids WHERE auction_id=? ORDER BY amount DESC, created_at ASC LIMIT 1", (auction_id,))
        row = cur.fetchone()
        return dict(row) if row else None

# автоинициализация
init_db()
