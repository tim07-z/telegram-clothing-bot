from flask import Flask, jsonify
import threading
import os
import time
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "Bot is running", "service": "Telegram Clothing Bot"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_bot():
    """Запуск бота в отдельном потоке"""
    try:
        print("Starting bot...")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        
        # Проверяем, что файл bot.py существует
        if not os.path.exists('bot.py'):
            print("ERROR: bot.py not found!")
            return
            
        # Импортируем и запускаем бота
        from bot import main as bot_main
        print("Bot imported successfully")
        
        import asyncio
        print("Starting asyncio event loop...")
        asyncio.run(bot_main())
        
    except Exception as e:
        print(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

def run_web_server():
    """Запуск веб-сервера"""
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    print("Application starting...")
    print(f"Environment variables: PORT={os.environ.get('PORT', 'Not set')}")
    
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("Bot thread started")
    
    # Небольшая задержка
    time.sleep(3)
    
    # Запуск веб-сервера
    run_web_server()
