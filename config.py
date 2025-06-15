import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение конфигурации из переменных окружения
TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "duganit")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@scinhedstyle")

# Проверка наличия обязательных переменных
if not TOKEN:
    raise ValueError("TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")