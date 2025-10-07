import sqlite3
from config import DB_PATH, DEFAULT_LANG, DEFAULT_THEME

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        lang TEXT DEFAULT '{DEFAULT_LANG}',
        theme TEXT DEFAULT '{DEFAULT_THEME}'
        )
    """)
    conn.commit()
    conn.close()

def get_user_pref(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lang, theme FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, lang, theme) VALUES (?, ?, ?)", (user_id, DEFAULT_LANG, DEFAULT_THEME))
        conn.commit()
        result = {"lang": DEFAULT_LANG, "theme": DEFAULT_THEME}
    else:
        result = {"lang": row[0], "theme": row[1]}
    conn.close()
    return result

def set_user_pref(user_id: int, lang=None, theme=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if lang:
        c.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    if theme:
        c.execute("UPDATE users SET theme = ? WHERE user_id = ?", (theme, user_id))
    conn.commit()
    conn.close()

init_db()
