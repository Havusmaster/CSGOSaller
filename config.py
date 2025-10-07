# config.py
"""
Конфигурация проекта: пути, дефолты и загрузка переводов.
"""

import os
import yaml

# ===== Настройки окружения =====
TOKEN = os.getenv("BOT_TOKEN", "7504123410:AAEznGqRafbyrBx2e34HzsxztWV201HRMxE")  # Telegram bot token (обязательно задать в Render/Replit env)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()] or [1939282952, 5266027747]  # список админов

APP_URL = os.getenv("APP_URL", "https://csgosaller-1.onrender.com/")  # публичный URL приложения (можно задать в env)
DB_PATH = os.getenv("DB_PATH", "cs_saler.db")  # sqlite файл

# По умолчанию — узбекский и тёмная тема
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "uz")
DEFAULT_THEME = os.getenv("DEFAULT_THEME", "dark")  # "dark" или "light"

# Параметры Flask
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_SECRET = os.getenv("FLASK_SECRET", "change-me-secret")

# Загрузим переводы из YAML
TRANSLATIONS_FILE = os.path.join(os.path.dirname(__file__), "translations.yaml")
try:
    with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
        _TRANSLATIONS = yaml.safe_load(f) or {}
except Exception:
    _TRANSLATIONS = {}

def t(lang, key):
    """
    Удобный доступ к переводам.
    key: 'bot.start' или 'web.welcome'
    """
    parts = key.split(".")
    d = _TRANSLATIONS.get(lang, {})
    for p in parts:
        if isinstance(d, dict):
            d = d.get(p, {})
        else:
            d = {}
    if not d:
        # fallback to DEFAULT_LANG, then to key itself
        d = _TRANSLATIONS.get(DEFAULT_LANG, {})
        for p in parts:
            if isinstance(d, dict):
                d = d.get(p, {})
            else:
                d = {}
        if not d:
            return key
    return d
