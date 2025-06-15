from flask import Flask, jsonify
import threading
import os
import time
import sys
import asyncio

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
        
        # Проверяем, что файл bot.py существует
        if not os.path.exists('bot.py'):
            print("ERROR: bot.py not found!")
            return
            
        print("bot.py found, trying to import...")
        
        # Пробуем импортировать модули по отдельности
        try:
            import config
            print("config imported successfully")
        except Exception as e:
            print(f"Error importing config: {e}")
            return
            
        try:
            import json
            print("json imported successfully")
        except Exception as e:
            print(f"Error importing json: {e}")
            return
            
        # Импортируем бота
        try:
            from bot import main as bot_main
            print("Bot imported successfully")
        except Exception as e:
            print(f"Error importing bot: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        print("Starting asyncio event loop...")
        loop.run_until_complete(bot_main())
        
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
