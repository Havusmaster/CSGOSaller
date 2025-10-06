import sqlite3
import os

# 🛠 Путь к базе данных (Render разрешает писать только в /opt/render/project/src/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "database.db"))

def init_db():
    # Создаём директорию для базы, если её нет
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Таблица товаров (магазин)
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

    # Таблица аукционов
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

    # Таблица ставок
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

    # Таблица ожидания заявок
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_requests (
            user_id INTEGER,
            product_id INTEGER,
            timestamp INTEGER,
            PRIMARY KEY (user_id, product_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Проверка и добавление недостающих колонок
    def ensure_column_exists(table_name, column_name, column_type):
        c.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in c.fetchall()]
        if column_name not in columns:
            c.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')

    ensure_column_exists('products', 'float_value', 'REAL')
    ensure_column_exists('lots', 'float_value', 'REAL')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print(f"✅ База данных успешно инициализирована по пути: {DB_PATH}")
