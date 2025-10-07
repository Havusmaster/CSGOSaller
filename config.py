# config.py
"""
Конфигурация проекта.
Отредактируйте значения: BOT_TOKEN и ADMIN_IDS.
APP_URL — URL вашего веб-приложения (Replit URL или локально http://127.0.0.1:5000).
"""

import os

# Токен бота Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "7504123410:AAEznGqRafbyrBx2e34HzsxztWV201HRMxE")

# Список admin Telegram ID (integers). Пример: [123456789, 987654321]
ADMIN_IDS = os.getenv("ADMIN_IDS", [1939282952, 5266027747]).split(",")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS if x.strip()]

# URL веб-приложения — нужно указать публичный адрес Replit или оставить локальный.
# Пример для Replit: "https://your-repl-name.your-username.repl.co"
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")

# Путь к базе данных SQLite
DB_PATH = os.getenv("DB_PATH", "cs_saler.db")

# Порт Flask (Replit обычно использует 5000)
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Хранилище сессий Flask (секретный ключ)
FLASK_SECRET = os.getenv("FLASK_SECRET", "super-secret-key-change-me")
