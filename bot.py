import os
import multiprocessing
from telegram_bot import run_bot
from webapp import app
from admin_routes import *
from database import init_db

if __name__ == '__main__':
    init_db()
    def start_bot():
        run_bot()

    bot_process = multiprocessing.Process(target=start_bot)
    bot_process.start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))