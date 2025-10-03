import asyncio
import threading
from telegram_bot import run_bot
from webapp import app

def run_flask():
    """Run the Flask web app in a separate thread."""
    app.run(host='0.0.0.0', port=5000)

async def main():
    """Run the Telegram bot and Flask web app concurrently."""
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start the Telegram bot
    await run_bot()

if __name__ == '__main__':
    asyncio.run(main())