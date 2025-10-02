import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            sold INTEGER DEFAULT 0,
            image TEXT,
            float_value REAL,
            trade_ban INTEGER DEFAULT 0,
            type TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_price INTEGER NOT NULL,
            current_price INTEGER NOT NULL,
            step INTEGER NOT NULL,
            end_time INTEGER,
            active INTEGER DEFAULT 1,
            image TEXT,
            float_value REAL,
            trade_ban INTEGER DEFAULT 0,
            type TEXT NOT NULL,
            winner_id INTEGER
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER,
            user_id INTEGER,
            amount INTEGER,
            time INTEGER,
            FOREIGN KEY (lot_id) REFERENCES lots(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_requests (
            user_id INTEGER,
            product_id INTEGER,
            timestamp INTEGER,
            PRIMARY KEY (user_id, product_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    c.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in c.fetchall()]
    if 'float_value' not in columns:
        c.execute('ALTER TABLE products ADD COLUMN float_value REAL')

    c.execute("PRAGMA table_info(lots)")
    columns = [col[1] for col in c.fetchall()]
    if 'float_value' not in columns:
        c.execute('ALTER TABLE lots ADD COLUMN float_value REAL')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()