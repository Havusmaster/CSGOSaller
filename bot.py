import os
import threading
from webapp import app
from telegram_bot import run_bot
import asyncio


def run_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())


if __name__ == '__main__':
    # Запуск Telegram-бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()

    # Запуск Flask (для Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
