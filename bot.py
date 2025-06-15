import logging
import json
import os
from openai import OpenAI
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN, OPENAI_API_KEY, ADMIN_USERNAME
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import re
import aiohttp

# Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Загрузка/сохранение данных
CONFIG_FILE = "clothing_config.json"
ORDERS_FILE = "orders.json"
USER_DATA_FILE = "user_data.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "prompt": """Ты - консультант магазина модной одежды. Твои задачи:
1. Помогать с выбором одежды через воронку продаж
2. Задавать уточняющие вопросы
3. Подбирать размеры
4. Давать стилистические советы
5. Сообщать об акциях и скидках
6. Рекомендовать сочетания вещей
7. В конце консультации предлагать оформить заказ
8. При рекомендации товаров обязательно указывай бренд, название, цену, материал и размеры""",
            "knowledge_base": {
                "categories": {
                    "футболки": {
                        "description": "Классические и стильные футболки из качественных материалов",
                        "items": [
                            {
                                "brand": "Nike",
                                "name": "Nike Dri-FIT Training",
                                "price": 2500,
                                "material": "100% полиэстер с технологией Dri-FIT",
                                "sizes": ["S", "M", "L", "XL", "XXL"],
                                "colors": ["черный", "белый", "серый", "синий"],
                                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
                                "description": "Спортивная футболка с технологией отвода влаги"
                            },
                            {
                                "brand": "Adidas",
                                "name": "Adidas Originals Trefoil",
                                "price": 2200,
                                "material": "100% хлопок",
                                "sizes": ["XS", "S", "M", "L", "XL"],
                                "colors": ["белый", "черный", "красный"],
                                "image_url": "https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400",
                                "description": "Классическая футболка с логотипом Trefoil"
                            },
                            {
                                "brand": "Uniqlo",
                                "name": "Uniqlo U Crew Neck",
                                "price": 1900,
                                "material": "100% хлопок",
                                "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
                                "colors": ["белый", "черный", "синий", "зеленый", "красный"],
                                "image_url": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400",
                                "description": "Базовая футболка премиального качества"
                            }
                        ]
                    },
                    "джинсы": {
                        "description": "Стильные джинсы для любого случая",
                        "items": [
                            {
                                "brand": "Levi's",
                                "name": "Levi's 501 Original Fit",
                                "price": 4500,
                                "material": "100% хлопок деним",
                                "sizes": ["28", "30", "32", "34", "36", "38", "40"],
                                "colors": ["синий", "темно-синий", "черный"],
                                "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400",
                                "description": "Классические джинсы прямого кроя"
                            },
                            {
                                "brand": "Wrangler",
                                "name": "Wrangler Retro Slim Fit",
                                "price": 3800,
                                "material": "98% хлопок, 2% эластан",
                                "sizes": ["28", "30", "32", "34", "36", "38"],
                                "colors": ["синий", "светло-синий", "серый"],
                                "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400",
                                "description": "Современные джинсы облегающего кроя"
                            }
                        ]
                    },
                    "платья": {
                        "description": "Элегантные платья для любого случая",
                        "items": [
                            {
                                "brand": "Zara",
                                "name": "Zara Midi Dress",
                                "price": 5500,
                                "material": "100% хлопок",
                                "sizes": ["XS", "S", "M", "L", "XL"],
                                "colors": ["черный", "белый", "синий", "красный"],
                                "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
                                "description": "Элегантное платье миди длины"
                            },
                            {
                                "brand": "H&M",
                                "name": "H&M Summer Dress",
                                "price": 4200,
                                "material": "95% хлопок, 5% эластан",
                                "sizes": ["36", "38", "40", "42", "44", "46"],
                                "colors": ["белый", "голубой", "розовый"],
                                "image_url": "https://images.unsplash.com/photo-1572804013427-4d7ca7268217?w=400",
                                "description": "Легкое летнее платье"
                            }
                        ]
                    },
                    "куртки": {
                        "description": "Стильные куртки для любого сезона",
                        "items": [
                            {
                                "brand": "The North Face",
                                "name": "The North Face Venture 2",
                                "price": 8500,
                                "material": "100% нейлон с мембраной DryVent",
                                "sizes": ["S", "M", "L", "XL", "XXL"],
                                "colors": ["черный", "синий", "красный"],
                                "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400",
                                "description": "Водостойкая куртка для активного отдыха"
                            },
                            {
                                "brand": "Columbia",
                                "name": "Columbia Powder Lite",
                                "price": 7200,
                                "material": "100% нейлон с утеплителем",
                                "sizes": ["S", "M", "L", "XL"],
                                "colors": ["черный", "серый", "синий"],
                                "image_url": "https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=400",
                                "description": "Теплая куртка для холодной погоды"
                            }
                        ]
                    }
                },
                "promotions": [
                    "🎁 2 вещи → скидка 10%",
                    "🎁 3 вещи → скидка 15%", 
                    "🎁 Постоянным клиентам → дополнительно 5%",
                    "🔥 Товары недели: джинсы Levi's -25%"
                ]
            },
            "temperature": 0.7,
            "sales_funnel": [
                "Какой тип одежды вас интересует? (футболки, джинсы, платья, куртки)",
                "Какой стиль вы предпочитаете? (классика, спорт, кэжуал, вечерний)",
                "Какой цвет вы бы хотели?",
                "Какой у вас размер? (если не знаете - помогу определить)",
                "Какой ценовой диапазон рассматриваете?",
                "Нужна ли вам помощь в сочетании с другими вещами?"
            ]
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE) as f:
        return json.load(f)

def save_orders(orders):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

def load_user_data():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE) as f:
        return json.load(f)

def save_user_data(user_data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=2)

# Состояния
class ConsultantStates(StatesGroup):
    waiting_for_question = State()
    sales_funnel = State()

class OrderStates(StatesGroup):
    waiting_for_order_confirmation = State()
    waiting_for_order_details = State()
    waiting_for_color_choice = State()
    waiting_for_country = State()
    waiting_for_region = State()
    waiting_for_city = State()
    waiting_for_district = State()
    waiting_for_address = State()
    waiting_for_fake_payment = State()

class AdminStates(StatesGroup):
    editing_prompt = State()
    editing_knowledge = State()
    editing_temperature = State()

# Меню
def main_menu(is_admin=False):
    buttons = [
        [KeyboardButton(text="👕 Консультация по одежде")],
        [KeyboardButton(text="ℹ️ О консультанте")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Редактировать промт")],
            [KeyboardButton(text="📚 Изменить базу знаний")],
            [KeyboardButton(text="🌡 Изменить температуру")],
            [KeyboardButton(text="📊 Текущие настройки")],
            [KeyboardButton(text="📦 Посмотреть заказы")],
            [KeyboardButton(text="🔙 В меню")]
        ],
        resize_keyboard=True
    )

def order_confirmation_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, оформить заказ")],
            [KeyboardButton(text="❌ Нет, продолжить консультацию")],
            [KeyboardButton(text="🔙 В меню")]
        ],
        resize_keyboard=True
    )

def color_selection_menu(colors):
    """
    Создает клавиатуру для выбора цвета
    """
    keyboard = []
    # Размещаем цвета по 2 в ряд
    for i in range(0, len(colors), 2):
        row = [KeyboardButton(text=colors[i])]
        if i + 1 < len(colors):
            row.append(KeyboardButton(text=colors[i + 1]))
        keyboard.append(row)
    
    # Добавляем кнопку "Назад"
    keyboard.append([KeyboardButton(text="🔙 В меню")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def fake_payment_menu():
    """
    Создает клавиатуру для фейковой оплаты
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Оплатить заказ")],
            [KeyboardButton(text="❌ Отменить заказ")],
            [KeyboardButton(text="🔙 В меню")]
        ],
        resize_keyboard=True
    )

# OpenAI запрос
async def ask_openai(prompt: str, config: dict, user_data: dict = None) -> str:
    try:
        # Инициализируем клиент OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Форматируем базу знаний в читаемый вид
        knowledge_text = "БАЗА ЗНАНИЙ ИИ-АССИСТЕНТА:\n\n"
        
        if isinstance(config.get('knowledge_base'), dict):
            # Добавляем базу знаний ИИ-ассистента
            ai_knowledge = config['knowledge_base'].get('ai_assistant_knowledge', '')
            if ai_knowledge:
                knowledge_text += f"{ai_knowledge}\n\n"
            
            knowledge_text += "АССОРТИМЕНТ ТОВАРОВ:\n\n"
            
            # Новая структура с категориями
            for category, category_data in config['knowledge_base'].get('categories', {}).items():
                knowledge_text += f"📁 {category.upper()}: {category_data.get('description', '')}\n\n"
                
                for item in category_data.get('items', []):
                    knowledge_text += f"🏷 {item.get('brand', '')} - {item.get('name', '')}\n"
                    knowledge_text += f"💰 Цена: {item.get('price', '')}₸\n"
                    knowledge_text += f"🧵 Материал: {item.get('material', '')}\n"
                    knowledge_text += f"📏 Размеры: {', '.join(item.get('sizes', []))}\n"
                    knowledge_text += f"🎨 Цвета: {', '.join(item.get('colors', []))}\n"
                    knowledge_text += f"📝 Описание: {item.get('description', '')}\n"
                    knowledge_text += f"🖼 Фото: {item.get('image_url', '')}\n\n"
            
            # Добавляем акции
            promotions = config['knowledge_base'].get('promotions', [])
            if promotions:
                knowledge_text += "🔥 АКЦИИ И СКИДКИ:\n"
                for promotion in promotions:
                    knowledge_text += f"• {promotion}\n"
        else:
            # Старая структура (для обратной совместимости)
            knowledge_text += str(config.get('knowledge_base', ''))
        
        system_content = f"{config.get('prompt', '')}\n\n{knowledge_text}"
        
        messages = [{"role": "system", "content": system_content}]
        
        if user_data:
            messages.append({
                "role": "system", 
                "content": f"Информация о клиенте: {json.dumps(user_data, ensure_ascii=False)}"
            })
        
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=config.get('temperature', 0.7)
        )
        
        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            return "⚠️ Получен пустой ответ от ИИ. Попробуйте еще раз."
            
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        return f"⚠️ Произошла ошибка при обработке запроса: {str(e)[:100]}. Пожалуйста, попробуйте позже."

def extract_user_categories(user_answers: dict) -> list:
    """
    Извлекает выбранные пользователем категории товаров из его ответов
    """
    categories = []
    
    # Ищем ответ на первый вопрос воронки (тип одежды)
    for question, answer in user_answers.items():
        if "тип одежды" in question.lower() or "интересует" in question.lower():
            answer_lower = answer.lower()
            
            # Маппинг ответов на категории
            category_mapping = {
                "футболки": ["футболки", "футболка", "топы", "майки"],
                "джинсы": ["джинсы", "джинс", "брюки", "штаны", "низ"],
                "платья": ["платья", "платье", "платьица"],
                "куртки": ["куртки", "куртка", "пальто", "верхняя одежда"],
                "рубашки": ["рубашки", "рубашка", "сорочки"],
                "обувь": ["обувь", "туфли", "кроссовки", "ботинки", "сапоги"]
            }
            
            # Проверяем каждую категорию
            for category, keywords in category_mapping.items():
                if any(keyword in answer_lower for keyword in keywords):
                    categories.append(category)
            
            # Если ничего не найдено, добавляем все категории
            if not categories:
                categories = list(category_mapping.keys())
            
            break
    
    return categories

def parse_ai_response_for_products(response: str, config: dict, user_answers: dict = None) -> list:
    """
    Парсит ответ ИИ и извлекает информацию о товарах
    Фильтрует товары только по выбранным пользователем категориям
    """
    products = []
    
    # Извлекаем выбранные пользователем категории
    user_categories = []
    if user_answers:
        user_categories = extract_user_categories(user_answers)
    
    # Ищем упоминания брендов и названий товаров в ответе
    if isinstance(config.get('knowledge_base'), dict):
        knowledge_base = config['knowledge_base']
        response_lower = response.lower()
        
        # Проходим только по выбранным категориям
        categories_to_check = user_categories if user_categories else knowledge_base.get('categories', {}).keys()
        
        for category in categories_to_check:
            if category not in knowledge_base.get('categories', {}):
                continue
                
            category_data = knowledge_base['categories'][category]
            for item in category_data.get('items', []):
                brand = item.get('brand', '').lower()
                name = item.get('name', '').lower()
                
                # Более точный поиск: ищем точное совпадение бренда и названия
                # или полное название товара
                brand_found = brand in response_lower
                full_name_found = name in response_lower
                
                # Разбиваем название на части для поиска ключевых слов
                name_parts = [part for part in name.split() if len(part) > 2]
                
                # Ищем ключевые части названия (например, "Dri-FIT", "501", "Midi")
                key_parts_found = []
                for part in name_parts:
                    if part in response_lower:
                        key_parts_found.append(part)
                
                # Товар найден, если:
                # 1. Найден бренд И полное название, ИЛИ
                # 2. Найдено полное название товара, ИЛИ
                # 3. Найден бренд И хотя бы одна ключевая часть названия
                if ((brand_found and full_name_found) or 
                    full_name_found or 
                    (brand_found and len(key_parts_found) >= 1)):
                    
                    # Проверяем, что товар еще не добавлен (избегаем дубликатов)
                    existing_product = next((p for p in products if p['brand'] == item.get('brand', '') and p['name'] == item.get('name', '')), None)
                    if not existing_product:
                        products.append({
                            'category': category,
                            'brand': item.get('brand', ''),
                            'name': item.get('name', ''),
                            'price': item.get('price', ''),
                            'material': item.get('material', ''),
                            'sizes': item.get('sizes', []),
                            'colors': item.get('colors', []),
                            'description': item.get('description', ''),
                            'image_url': item.get('image_url', '')
                        })
    
    return products

# Функция для отправки товаров отдельными сообщениями
async def send_products_separately(message: types.Message, products: list, original_response: str):
    """
    Отправляет каждый товар отдельным сообщением с фотографией
    """
    if not products:
        # Если товары не найдены, отправляем обычный ответ
        await message.answer(
            f"🎉 Вот что мы подобрали для вас:\n\n{original_response}\n\n"
            "Хотите оформить заказ на один из вариантов?",
            reply_markup=order_confirmation_menu()
        )
        return
    
    # Отправляем вступительное сообщение
    await message.answer(
        "🎉 Вот что мы подобрали для вас:\n\n"
        f"{original_response}\n\n"
        "📦 Подробная информация о товарах:",
        reply_markup=order_confirmation_menu()
    )
    
    # Отправляем каждый товар отдельным сообщением
    for i, product in enumerate(products, 1):
        try:
            # Формируем описание товара
            product_text = (
                f"🛍 <b>Товар {i}</b>\n\n"
                f"🏷 <b>{product['brand']} - {product['name']}</b>\n"
                f"💰 Цена: {product['price']}₸\n"
                f"🧵 Материал: {product['material']}\n"
                f"📏 Размеры: {', '.join(product['sizes'])}\n"
                f"🎨 Цвета: {', '.join(product['colors'])}\n"
                f"📝 Описание: {product['description']}\n"
                f"📁 Категория: {product['category']}"
            )
            
            # Отправляем фотографию с описанием
            if product['image_url']:
                try:
                    await message.answer_photo(
                        photo=product['image_url'],
                        caption=product_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logging.error(f"Ошибка при отправке фото для товара {i}: {e}")
                    # Если не удалось отправить фото, отправляем только текст
                    await message.answer(product_text, parse_mode="HTML")
            else:
                # Если нет фото, отправляем только текст
                await message.answer(product_text, parse_mode="HTML")
                
        except Exception as e:
            logging.error(f"Ошибка при отправке товара {i}: {e}")
            continue

# Команды
@dp.message(Command("start"))
async def start(message: types.Message):
    is_admin = message.from_user.username == ADMIN_USERNAME
    await message.answer(
        "👋 Привет! Я ваш консультант по одежде. Помогу с выбором и оформлением заказа!",
        reply_markup=main_menu(is_admin)
    )

@dp.message(F.text == "🔙 В меню")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.username == ADMIN_USERNAME
    await message.answer("Главное меню:", reply_markup=main_menu(is_admin))

@dp.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: types.Message):
    if message.from_user.username == ADMIN_USERNAME:
        await message.answer("Админ-панель:", reply_markup=admin_menu())

# Пользовательские handlers
@dp.message(F.text == "👕 Консультация по одежде")
async def start_consultation(message: types.Message, state: FSMContext):
    await state.set_state(ConsultantStates.sales_funnel)
    config = load_config()
    
    # Проверяем наличие sales_funnel в конфиге
    if 'sales_funnel' not in config or not config['sales_funnel']:
        # Если воронки нет, используем стандартную
        config['sales_funnel'] = [
            "Какой тип одежды вас интересует? (верх, низ, обувь, аксессуары)",
            "Какой стиль вы предпочитаете? (классика, спорт, кэжуал, вечерний)",
            "Какой цвет вы бы хотели?",
            "Какой у вас размер? (если не знаете - помогу определить)",
            "Какой ценовой диапазон рассматриваете?",
            "Нужна ли вам помощь в сочетании с другими вещами?"
        ]
        save_config(config)  # Сохраняем обновленный конфиг
    
    await state.update_data(current_step=0, user_answers={})
    await message.answer(
        "🔍 Давайте подберем для вас идеальную одежду!\n\n" + 
        config['sales_funnel'][0],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(ConsultantStates.sales_funnel)
async def sales_funnel_step(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    data = await state.get_data()
    current_step = data['current_step']
    user_answers = data['user_answers']
    config = load_config()
    
    # Сохраняем ответ пользователя
    question = config['sales_funnel'][current_step]
    user_answers[question] = message.text
    
    # Переходим к следующему вопросу или завершаем воронку
    if current_step + 1 < len(config['sales_funnel']):
        await state.update_data(
            current_step=current_step + 1,
            user_answers=user_answers
        )
        await message.answer(config['sales_funnel'][current_step + 1])
    else:
        # Воронка завершена, предлагаем рекомендации
        await state.update_data(user_answers=user_answers)
        await state.set_state(ConsultantStates.waiting_for_question)
        
        # Сохраняем данные пользователя
        user_data = load_user_data()
        user_data[str(message.from_user.id)] = user_answers
        save_user_data(user_data)
        
        # Генерируем рекомендации
        await bot.send_chat_action(message.chat.id, "typing")
        
        # Формируем промт с акциями
        promotions_text = ""
        if isinstance(config['knowledge_base'], dict) and 'promotions' in config['knowledge_base']:
            promotions_text = "Акции: " + ", ".join(config['knowledge_base']['promotions'])
        else:
            promotions_text = "Акции: 🎁 2 вещи → скидка 10%, 🎁 3 вещи → скидка 15%"
        
        prompt = (
            f"На основе этих ответов предложи 3 варианта товаров:\n"
            f"{json.dumps(user_answers, ensure_ascii=False)}\n\n"
            f"Упомни акции: {promotions_text}\n\n"
            f"ВАЖНО: При рекомендации товаров обязательно указывай точное название бренда и модели товара из базы знаний. "
            f"Например: 'Nike Dri-FIT Training', 'Levi's 501 Original Fit', 'Zara Midi Dress' и т.д."
        )
        response = await ask_openai(prompt, config, user_answers)
        
        products = parse_ai_response_for_products(response, config, user_answers)
        await send_products_separately(message, products, response)

@dp.message(ConsultantStates.waiting_for_question)
async def handle_question(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    elif message.text == "✅ Да, оформить заказ":
        # Сначала запрашиваем цвет
        config = load_config()
        user_data = load_user_data().get(str(message.from_user.id), {})
        all_colors = set()
        
        # Извлекаем выбранные пользователем категории
        user_categories = extract_user_categories(user_data)
        
        # Собираем цвета только из выбранных категорий
        if isinstance(config.get('knowledge_base'), dict):
            categories_to_check = user_categories if user_categories else config['knowledge_base'].get('categories', {}).keys()
            
            for category in categories_to_check:
                if category in config['knowledge_base'].get('categories', {}):
                    category_data = config['knowledge_base']['categories'][category]
                    for item in category_data.get('items', []):
                        colors = item.get('colors', [])
                        all_colors.update(colors)
        
        # Если цвета не найдены, используем стандартные
        if not all_colors:
            all_colors = {"черный", "белый", "синий", "красный", "зеленый", "желтый", "розовый", "серый", "коричневый", "оранжевый"}
        
        colors_list = sorted(list(all_colors))
        
        await state.set_state(OrderStates.waiting_for_color_choice)
        await state.update_data(available_colors=colors_list)
        
        await message.answer(
            "🎨 Выберите цвет товара:",
            reply_markup=color_selection_menu(colors_list)
        )
        return
    elif message.text == "❌ Нет, продолжить консультацию":
        await message.answer(
            "Хорошо, продолжаем консультацию. Что вас еще интересует?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 В меню")]],
                resize_keyboard=True
            )
        )
        return
    
    try:
        config = load_config()
        user_data = load_user_data().get(str(message.from_user.id), {})
        
        await bot.send_chat_action(message.chat.id, "typing")
        response = await ask_openai(message.text, config, user_data)
        
        # Проверяем, что получили валидный ответ
        if not response or response.strip() == "":
            await message.answer(
                "⚠️ Не удалось получить ответ. Попробуйте переформулировать вопрос.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔙 В меню")]],
                    resize_keyboard=True
                )
            )
            return
        
        # Проверяем, не хочет ли ИИ предложить оформить заказ
        if "оформить заказ" in response.lower() or "заказать" in response.lower():
            await message.answer(
                response,
                reply_markup=order_confirmation_menu()
            )
        else:
            # Пытаемся найти товары в ответе и отправить их отдельными сообщениями
            products = parse_ai_response_for_products(response, config, user_data)
            
            if products:
                # Если найдены товары, отправляем их отдельными сообщениями
                await send_products_separately(message, products, response)
            else:
                # Если товары не найдены, отправляем обычный ответ
                await message.answer(
                    response,
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="🔙 В меню")]],
                        resize_keyboard=True
                    )
                )
    except Exception as e:
        logging.error(f"Ошибка в handle_question: {e}")
        await message.answer(
            f"⚠️ Произошла ошибка при обработке вашего вопроса: {str(e)[:100]}. Попробуйте еще раз.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 В меню")]],
                resize_keyboard=True
            )
        )

@dp.message(F.text == "ℹ️ О консультанте")
async def about_consultant(message: types.Message):
    await message.answer(
        "🤖 <b>О консультанте</b>\n\n"
        "Привет! Я ваш персональный AI-консультант по одежде. Я создан, чтобы помочь вам найти идеальную одежду и аксессуары.\n\n"
        "📋 <b>Что я умею:</b>\n"
        "• Помогаю с выбором одежды и стиля\n"
        "• Подбираю размеры и цветовые решения\n"
        "• Даю стилистические советы\n"
        "• Рекомендую сочетания вещей\n"
        "• Сообщаю об акциях и скидках\n"
        "• Помогаю оформить заказ\n\n"
        "🛍 <b>Я работаю с:</b>\n"
        "• Футболками, джинсами, платьями\n"
        "• Куртками, рубашками, обувью\n"
        "• Различными стилями и размерами\n"
        "• Разными ценовыми категориями\n\n"
        "💡 <b>Как это работает:</b>\n"
        "Я задам вам несколько вопросов о ваших предпочтениях и помогу найти именно то, что вам нужно!\n\n"
        "Готовы начать? Выберите '👕 Консультация по одежде' в меню!",
        reply_markup=main_menu(message.from_user.username == ADMIN_USERNAME)
    )

# Оформление заказа
@dp.message(OrderStates.waiting_for_color_choice)
async def process_color_choice(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    # Получаем данные состояния
    state_data = await state.get_data()
    available_colors = state_data.get('available_colors', [])
    
    # Проверяем, что выбранный цвет доступен
    if message.text not in available_colors:
        await message.answer(
            f"⚠️ Пожалуйста, выберите цвет из предложенных вариантов:",
            reply_markup=color_selection_menu(available_colors)
        )
        return
    
    # Сохраняем выбранный цвет и переходим к следующему шагу
    await state.update_data(selected_color=message.text)
    await state.set_state(OrderStates.waiting_for_order_details)
    
    await message.answer(
        f"🎨 Выбран цвет: <b>{message.text}</b>\n\n"
        "✍️ Теперь напишите:\n"
        "1. Название товара\n"
        "2. Размер (если отличается от указанного)\n"
        "3. Контакт для связи\n\n"
        "Пример: Футболка Nike Dri-FIT, L, @username или +79991234567",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(OrderStates.waiting_for_order_details)
async def process_order(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    # Сохраняем детали заказа и переходим к сбору адреса
    await state.update_data(order_details=message.text)
    await state.set_state(OrderStates.waiting_for_country)
    
    await message.answer(
        "🌍 Введите страну доставки:\n"
        "Например: Россия, Казахстан, Беларусь",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

# Обработчики сбора адреса доставки
@dp.message(OrderStates.waiting_for_country)
async def process_country(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    await state.update_data(country=message.text)
    await state.set_state(OrderStates.waiting_for_region)
    
    await message.answer(
        "🏛️ Введите область/регион:\n"
        "Например: Московская область, Алматинская область",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(OrderStates.waiting_for_region)
async def process_region(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    await state.update_data(region=message.text)
    await state.set_state(OrderStates.waiting_for_city)
    
    await message.answer(
        "🏙️ Введите город:\n"
        "Например: Москва, Алматы, Минск",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(OrderStates.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    await state.update_data(city=message.text)
    await state.set_state(OrderStates.waiting_for_district)
    
    await message.answer(
        "🏘️ Введите район (необязательно):\n"
        "Например: Центральный район, Ленинский район\n"
        "Или напишите 'пропустить' если район не нужен",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Пропустить")],
                [KeyboardButton(text="🔙 В меню")]
            ],
            resize_keyboard=True
        )
    )

@dp.message(OrderStates.waiting_for_district)
async def process_district(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    if message.text.lower() not in ["пропустить", "пропустить район"]:
        await state.update_data(district=message.text)
    else:
        await state.update_data(district="Не указан")
    
    await state.set_state(OrderStates.waiting_for_address)
    
    await message.answer(
        "📍 Введите точный адрес доставки:\n"
        "Например: ул. Ленина, д. 15, кв. 25\n"
        "Или: проспект Мира, 123, офис 456",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(OrderStates.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    # Получаем все данные заказа
    state_data = await state.get_data()
    user_data = load_user_data().get(str(message.from_user.id), {})
    
    # Формируем полный адрес
    country = state_data.get('country', 'Не указана')
    region = state_data.get('region', 'Не указан')
    city = state_data.get('city', 'Не указан')
    district = state_data.get('district', 'Не указан')
    address = message.text
    
    full_address = f"{country}, {region}, {city}"
    if district and district != "Не указан":
        full_address += f", {district}"
    full_address += f", {address}"
    
    # Показываем итог заказа и предлагаем оплату
    order_summary = (
        f"📋 <b>Итог заказа:</b>\n\n"
        f"🎨 Цвет: <b>{state_data.get('selected_color', 'Не указан')}</b>\n"
        f"📝 Товар: {state_data.get('order_details', 'Не указан')}\n"
        f"🌍 Адрес доставки:\n"
        f"   Страна: {country}\n"
        f"   Область: {region}\n"
        f"   Город: {city}\n"
        f"   Район: {district}\n"
        f"   Адрес: {address}\n\n"
        f"💳 Готовы к оплате?"
    )
    
    await state.update_data(full_address=full_address)
    await state.set_state(OrderStates.waiting_for_fake_payment)
    
    await message.answer(
        order_summary,
        reply_markup=fake_payment_menu()
    )

@dp.message(OrderStates.waiting_for_fake_payment)
async def process_fake_payment(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    elif message.text == "❌ Отменить заказ":
        await message.answer(
            "❌ Заказ отменен. Можете начать заново.",
            reply_markup=main_menu(message.from_user.username == ADMIN_USERNAME)
        )
        await state.clear()
        return
    elif message.text == "💳 Оплатить заказ":
        # Имитируем процесс оплаты
        await message.answer("💳 Обрабатываем оплату...")
        
        # Получаем все данные заказа
        state_data = await state.get_data()
        user_data = load_user_data().get(str(message.from_user.id), {})
        
        # Создаем заказ с полной информацией
        orders = load_orders()
        orders.append({
            "user_id": message.from_user.id,
            "username": message.from_user.username or "Нет username",
            "order_details": state_data.get('order_details', 'Не указан'),
            "selected_color": state_data.get('selected_color', 'Не указан'),
            "delivery_address": {
                "country": state_data.get('country', 'Не указана'),
                "region": state_data.get('region', 'Не указан'),
                "city": state_data.get('city', 'Не указан'),
                "district": state_data.get('district', 'Не указан'),
                "address": state_data.get('full_address', 'Не указан')
            },
            "user_data": user_data,
            "status": "Оплачен",
            "payment_method": "Тестовая оплата",
            "timestamp": str(message.date)
        })
        save_orders(orders)
        
        # Уведомление админа
        if ADMIN_USERNAME:
            try:
                await bot.send_message(
                    chat_id=ADMIN_USERNAME,
                    text=f"🛍 <b>Новый оплаченный заказ!</b>\n\n"
                         f"👤 Пользователь: @{message.from_user.username or 'нет'}\n"
                         f"🎨 Цвет: {state_data.get('selected_color', 'Не указан')}\n"
                         f"📝 Детали: {state_data.get('order_details', 'Не указан')}\n"
                         f"🌍 Адрес: {state_data.get('full_address', 'Не указан')}\n"
                         f"💳 Статус: Оплачен\n"
                         f"📊 Данные: {json.dumps(user_data, ensure_ascii=False)[:500]}...\n\n"
                         f"ID: {message.from_user.id}"
                )
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление админу: {e}")
        
        # Сообщение об успешной оплате
        await message.answer(
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"🎉 Ваш заказ принят и оплачен.\n\n"
            f"📋 <b>Детали заказа:</b>\n"
            f"🎨 Цвет: <b>{state_data.get('selected_color', 'Не указан')}</b>\n"
            f"📝 Товар: {state_data.get('order_details', 'Не указан')}\n"
            f"🌍 Адрес доставки: {state_data.get('full_address', 'Не указан')}\n\n"
            f"📞 Мы свяжемся с вами для уточнения деталей доставки.",
            reply_markup=main_menu(message.from_user.username == ADMIN_USERNAME)
        )
        await state.clear()
        return
    else:
        await message.answer(
            "Пожалуйста, выберите действие:",
            reply_markup=fake_payment_menu()
        )

# Админские handlers
@dp.message(F.text == "✏️ Редактировать промт")
async def edit_prompt(message: types.Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    
    config = load_config()
    await state.set_state(AdminStates.editing_prompt)
    await message.answer(
        f"📝 Текущий промт:\n\n{config['prompt']}\n\n"
        "Пришлите новый промт (или 'отмена' для отмены):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(AdminStates.editing_prompt)
async def save_prompt(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    config = load_config()
    config['prompt'] = message.text
    save_config(config)
    await message.answer("✅ Промт успешно обновлен!", reply_markup=admin_menu())
    await state.clear()

@dp.message(F.text == "📚 Изменить базу знаний")
async def edit_knowledge(message: types.Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    
    config = load_config()
    await state.set_state(AdminStates.editing_knowledge)
    
    # Форматируем базу знаний для отображения
    if isinstance(config['knowledge_base'], dict):
        knowledge_text = "📚 ТЕКУЩАЯ БАЗА ЗНАНИЙ:\n\n"
        
        # Показываем базу знаний ИИ-ассистента
        ai_knowledge = config['knowledge_base'].get('ai_assistant_knowledge', '')
        if ai_knowledge:
            knowledge_text += f"🤖 БАЗА ЗНАНИЙ ИИ-АССИСТЕНТА:\n{ai_knowledge[:300]}...\n\n"
        
        knowledge_text += "📦 ТОВАРЫ:\n"
        for category, category_data in config['knowledge_base'].get('categories', {}).items():
            knowledge_text += f"📁 {category.upper()}: {category_data.get('description', '')}\n"
            knowledge_text += f"Количество товаров: {len(category_data.get('items', []))}\n\n"
            
            for i, item in enumerate(category_data.get('items', []), 1):
                knowledge_text += f"  {i}. {item.get('brand', '')} - {item.get('name', '')} ({item.get('price', '')}₸)\n"
        
        if 'promotions' in config['knowledge_base']:
            knowledge_text += f"\n🔥 АКЦИИ ({len(config['knowledge_base']['promotions'])}):\n"
            for promotion in config['knowledge_base']['promotions']:
                knowledge_text += f"• {promotion}\n"
    else:
        knowledge_text = f"📚 Текущая база знаний:\n\n{config['knowledge_base']}"
    
    await message.answer(
        f"{knowledge_text}\n\n"
        "⚠️ ВНИМАНИЕ: База знаний имеет структурированный формат.\n"
        "Для изменения используйте JSON формат или обратитесь к разработчику.\n\n"
        "Для просмотра полной структуры нажмите '📊 Текущие настройки'",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(AdminStates.editing_knowledge)
async def save_knowledge(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    try:
        config = load_config()
        
        # Пытаемся распарсить JSON
        if message.text.strip().startswith('{'):
            try:
                new_knowledge = json.loads(message.text)
                config['knowledge_base'] = new_knowledge
                save_config(config)
                await message.answer(
                    "✅ База знаний успешно обновлена в JSON формате!", 
                    reply_markup=admin_menu()
                )
            except json.JSONDecodeError as e:
                await message.answer(
                    f"❌ Ошибка в JSON формате: {str(e)}\n\n"
                    "Пожалуйста, проверьте синтаксис JSON и попробуйте снова.",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="🔙 В меню")]],
                        resize_keyboard=True
                    )
                )
        else:
            # Если это не JSON, сохраняем как текст (для обратной совместимости)
            config['knowledge_base'] = message.text
            save_config(config)
            await message.answer(
                "✅ База знаний обновлена как текст!", 
                reply_markup=admin_menu()
            )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении: {str(e)}",
            reply_markup=admin_menu()
        )
    
    await state.clear()

@dp.message(F.text == "🌡 Изменить температуру")
async def edit_temperature(message: types.Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    
    config = load_config()
    await state.set_state(AdminStates.editing_temperature)
    await message.answer(
        f"🌡 Текущая температура: {config['temperature']}\n\n"
        "Пришлите новое значение (0.0-1.0, где 0 - строгий, 1 - креативный):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 В меню")]],
            resize_keyboard=True
        )
    )

@dp.message(AdminStates.editing_temperature)
async def save_temperature(message: types.Message, state: FSMContext):
    if message.text == "🔙 В меню":
        await back_to_menu(message, state)
        return
    
    try:
        temp = float(message.text)
        if 0 <= temp <= 1:
            config = load_config()
            config['temperature'] = temp
            save_config(config)
            await message.answer(f"✅ Температура изменена на {temp}!", reply_markup=admin_menu())
        else:
            await message.answer("❌ Значение должно быть от 0.0 до 1.0")
    except ValueError:
        await message.answer("❌ Введите число (например: 0.7)")
    
    await state.clear()

@dp.message(F.text == "📊 Текущие настройки")
async def show_settings(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        return
    
    config = load_config()
    
    # Форматируем базу знаний для отображения
    if isinstance(config['knowledge_base'], dict):
        knowledge_summary = "📚 СТРУКТУРИРОВАННАЯ БАЗА ЗНАНИЙ:\n\n"
        
        # База знаний ИИ-ассистента
        ai_knowledge = config['knowledge_base'].get('ai_assistant_knowledge', '')
        if ai_knowledge:
            knowledge_summary += f"🤖 БАЗА ЗНАНИЙ ИИ-АССИСТЕНТА:\n{ai_knowledge[:200]}...\n\n"
        
        # Товары
        total_items = 0
        knowledge_summary += "📦 ТОВАРЫ:\n"
        for category, category_data in config['knowledge_base'].get('categories', {}).items():
            items_count = len(category_data.get('items', []))
            total_items += items_count
            knowledge_summary += f"• {category}: {items_count} товаров\n"
        knowledge_summary += f"\nВсего товаров: {total_items}"
        
        if 'promotions' in config['knowledge_base']:
            knowledge_summary += f"\nАкций: {len(config['knowledge_base']['promotions'])}"
    else:
        knowledge_summary = f"📚 База знаний:\n{config['knowledge_base'][:200]}..."
    
    await message.answer(
        f"⚙️ <b>Текущие настройки:</b>\n\n"
        f"📝 <b>Промт:</b>\n{config['prompt'][:200]}...\n\n"
        f"{knowledge_summary}\n\n"
        f"🌡 <b>Температура:</b> {config['temperature']}\n\n"
        f"🛒 <b>Всего заказов:</b> {len(load_orders())}",
        reply_markup=admin_menu()
    )

@dp.message(F.text == "📦 Посмотреть заказы")
async def show_orders(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        return
    
    orders = load_orders()
    if not orders:
        await message.answer("📭 Список заказов пуст", reply_markup=admin_menu())
        return
    
    # Разбиваем на сообщения по 5 заказов, чтобы не превысить лимит длины
    for i in range(0, len(orders), 5):
        orders_batch = orders[i:i+5]
        orders_text = "📦 <b>Список заказов:</b>\n\n"
        
        for order in orders_batch:
            color_info = f"🎨 Цвет: {order.get('selected_color', 'Не указан')}\n" if 'selected_color' in order else ""
            
            # Информация об адресе доставки
            address_info = ""
            if 'delivery_address' in order:
                delivery = order['delivery_address']
                address_info = (
                    f"🌍 Адрес доставки:\n"
                    f"   Страна: {delivery.get('country', 'Не указана')}\n"
                    f"   Область: {delivery.get('region', 'Не указан')}\n"
                    f"   Город: {delivery.get('city', 'Не указан')}\n"
                    f"   Район: {delivery.get('district', 'Не указан')}\n"
                    f"   Адрес: {delivery.get('address', 'Не указан')}\n"
                )
            elif 'full_address' in order:
                address_info = f"🌍 Адрес: {order['full_address']}\n"
            
            # Информация о способе оплаты
            payment_info = ""
            if 'payment_method' in order:
                payment_info = f"💳 Способ оплаты: {order['payment_method']}\n"
            
            orders_text += (
                f"🔹 <b>Заказ от {order.get('timestamp', 'N/A')}</b>\n"
                f"👤 Пользователь: @{order['username']} (ID: {order['user_id']})\n"
                f"{color_info}"
                f"📝 Детали: {order['order_details']}\n"
                f"🔄 Статус: {order['status']}\n"
                f"{payment_info}"
                f"{address_info}"
                f"📊 Данные: {json.dumps(order.get('user_data', {}), ensure_ascii=False)[:200]}...\n\n"
            )
        
        await message.answer(orders_text, reply_markup=admin_menu())

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())