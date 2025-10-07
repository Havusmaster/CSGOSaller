# config.py
"""
Конфигурация проекта CSsaler.
Редактируйте переменные окружения или прямо здесь (не рекомендуется в проде).
"""

import os

# Telegram token: установите переменную окружения BOT_TOKEN или впишите сюда.
TOKEN = os.getenv("BOT_TOKEN", "7504123410:AAEznGqRafbyrBx2e34HzsxztWV201HRMxE")

# Список admin ID через запятую или в env ADMIN_IDS (пример: "123456789,987654321")
_ADMIN_IDS_ENV = os.getenv("ADMIN_IDS", "")
if _ADMIN_IDS_ENV:
    try:
        ADMIN_IDS = [int(x.strip()) for x in _ADMIN_IDS_ENV.split(",") if x.strip()]
    except Exception:
        ADMIN_IDS = []
else:
    # если не указано в env — можно вписать сюда админов вручную
    ADMIN_IDS = [1939282952, 5266027747]

# Публичный адрес веб-приложения (Replit / Render). Используется в шаблонах.
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")

# Путь к sqlite базе
DB_PATH = os.getenv("DB_PATH", "cs_saler.db")

# Flask настройки
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_SECRET = os.getenv("FLASK_SECRET", "change-me-secret")

# Для удобства — тайм-аут проверки аукционов (сек)
AUCTION_CHECK_INTERVAL = int(os.getenv("AUCTION_CHECK_INTERVAL", "30"))
