import os
import threading
import asyncio
from webapp import app
from telegram_bot import run_bot
from database import init_db  # Добавлено: импорт функции init_db

def run_bot_thread():
    """Запуск Telegram-бота в отдельном потоке с новой event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot())
    except Exception as e:
        print(f"[ERROR] Ошибка при запуске бота: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    print("[INFO] Запуск Telegram-бота и веб-сервера...")

    init_db()  # Добавлено: инициализация db перед всем (создаст таблицы, если нет)

    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()

    # Получаем порт (Render автоматически задаёт его через переменную окружения)
    port = int(os.environ.get("PORT", 5000))

    # Запускаем Flask в основном потоке
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        print(f"[ERROR] Ошибка при запуске Flask: {e}")