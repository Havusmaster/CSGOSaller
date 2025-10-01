import sqlite3
import os

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
    CREATE TABLE IF NOT EXISTS pending_requests (
        user_id INTEGER,
        product_id INTEGER,
        timestamp INTEGER,
        PRIMARY KEY (user_id, product_id)
    )""")
    conn.commit()
    conn.close()