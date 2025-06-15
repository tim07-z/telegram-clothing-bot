from flask import Flask, jsonify
import threading
import subprocess
import os
import signal
import time

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "Bot is running", "service": "Telegram Clothing Bot"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_bot():
    """Запуск бота как отдельный процесс"""
    try:
        print("Starting bot process...")
        # Запускаем бота как отдельный процесс
        process = subprocess.Popen(['python', 'bot.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        print(f"Bot process started with PID: {process.pid}")
        
        # Ждем завершения процесса
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Bot process failed with return code: {process.returncode}")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
        else:
            print("Bot process completed successfully")
            
    except Exception as e:
        print(f"Error running bot: {e}")

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
    time.sleep(2)
    
    # Запуск веб-сервера
    run_web_server() 