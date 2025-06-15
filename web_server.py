from flask import Flask, jsonify
import threading
import os
from bot import main as bot_main

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "Bot is running", "service": "Telegram Clothing Bot"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_bot():
    """Запуск бота в отдельном потоке"""
    bot_main()

def run_web_server():
    """Запуск веб-сервера"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запуск веб-сервера
    run_web_server()
