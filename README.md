import asyncio
import logging
import sqlite3
import aiosqlite
import requests
import json
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.session.aiohttp import AiohttpSession
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import random
import threading
import time
import wikipedia
import pytz
from googletrans import Translator
from textblob import TextBlob
import emoji

# Скачиваем необходимые ресурсы NLTK
nltk.download('punkt')
nltk.download('stopwords')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chatbot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация бота
class Config:
    def __init__(self):
        self.TOKEN = "YOUR_BOT_TOKEN_HERE"
        self.WEATHER_API_KEY = "YOUR_WEATHER_API_KEY"
        self.NEWS_API_KEY = "YOUR_NEWS_API_KEY"
        self.OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
        self.AI_ENABLED = True
        self.DATABASE_NAME = "chatbot_db.sqlite"
        self.ADMIN_IDS = [123456789, 987654321]
        self.TIMEZONE = "Europe/Moscow"

# Инициализация конфига
config = Config()

# Инициализация бота и диспетчера
session = AiohttpSession()
bot = Bot(token=config.TOKEN, session=session)
dp = Dispatcher()

# Состояния для FSM
class UserStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_question = State()
    waiting_for_feedback = State()
    waiting_for_reminder_text = State()
    waiting_for_reminder_time = State()
    waiting_for_journal_entry = State()
    waiting_for_calorie_food = State()
    waiting_for_calorie_amount = State()
    waiting_for_mood = State()
    waiting_for_translate_text = State()
    waiting_for_language = State()

# Инициализация NLP инструментов
class NLPProcessor:
    def __init__(self):
        self.russian_stopwords = set(stopwords.words('russian'))
        self.stemmer = SnowballStemmer('russian')
        self.intents = self.load_intents()
        self.translator = Translator()
    
    def load_intents(self):
        try:
            with open('intents.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Файл intents.json не найден")
            return {"intents": []}
    
    def preprocess_text(self, text):
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalpha()]
        tokens = [token for token in tokens if token not in self.russian_stopwords]
        tokens = [self.stemmer.stem(token) for token in tokens]
        return tokens
    
    def recognize_intent(self, text):
        processed_text = self.preprocess_text(text)
        best_match = None
        highest_score = 0
        
        for intent in self.intents["intents"]:
            for example in intent["examples"]:
                processed_example = self.preprocess_text(example)
                matches = sum(1 for word in processed_text if word in processed_example)
                score = matches / max(len(processed_text), 1)
                
                if score > highest_score and score > 0.3:
                    highest_score = score
                    best_match = intent
        
        return best_match
    
    def detect_language(self, text):
        try:
            return self.translator.detect(text).lang
        except:
            return "en"
    
    def translate_text(self, text, dest_language):
        try:
            return self.translator.translate(text, dest=dest_language).text
        except:
            return text
    
    def analyze_sentiment(self, text):
        try:
            analysis = TextBlob(text)
            if analysis.sentiment.polarity > 0.1:
                return "positive"
            elif analysis.sentiment.polarity < -0.1:
                return "negative"
            else:
                return "neutral"
        except:
            return "neutral"

# Инициализация NLP процессора
nlp_processor = NLPProcessor()

# Класс для работы с базой данных
class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        messages_count INTEGER DEFAULT 0,
                        mood TEXT DEFAULT 'neutral',
                        language_preference TEXT DEFAULT 'ru'
                    )
                ''')
                # Таблица напоминаний
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        reminder_text TEXT,
                        reminder_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                # Таблица историй сообщений
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS message_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        message_text TEXT,
                        bot_response TEXT,
                        sentiment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                # Таблица журнала настроения
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mood_journal (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        mood TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                # Таблица отслеживания калорий
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calorie_tracker (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        food_item TEXT,
                        calories INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
    
    async def add_user(self, user_id, username, first_name, last_name):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, last_name)
            )
            await db.commit()
    
    async def update_message_count(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE users SET messages_count = messages_count + 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
    
    async def add_reminder(self, user_id, reminder_text, reminder_time):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT INTO reminders (user_id, reminder_text, reminder_time) VALUES (?, ?, ?)",
                (user_id, reminder_text, reminder_time)
            )
            await db.commit()
    
    async def add_message_to_history(self, user_id, message_text, bot_response, sentiment):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT INTO message_history (user_id, message_text, bot_response, sentiment) VALUES (?, ?, ?, ?)",
                (user_id, message_text, bot_response, sentiment)
            )
            await db.commit()
    
    async def add_mood_entry(self, user_id, mood, notes):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT INTO mood_journal (user_id, mood, notes) VALUES (?, ?, ?)",
                (user_id, mood, notes)
            )
            await db.execute(
                "UPDATE users SET mood = ? WHERE user_id = ?",
                (mood, user_id)
            )
            await db.commit()
    
    async def add_calorie_entry(self, user_id, food_item, calories):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT INTO calorie_tracker (user_id, food_item, calories) VALUES (?, ?, ?)",
                (user_id, food_item, calories)
            )
            await db.commit()
    
    async def get_user_stats(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "SELECT messages_count, created_at, mood FROM users WHERE user_id = ?",
                (user_id,)
            )
            return await cursor.fetchone()
    
    async def get_mood_history(self, user_id, days=7):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "SELECT mood, notes, created_at FROM mood_journal WHERE user_id = ? AND created_at >= date('now', ?) ORDER BY created_at DESC",
                (user_id, f"-{days} days")
            )
            return await cursor.fetchall()
    
    async def get_calorie_summary(self, user_id, days=1):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "SELECT SUM(calories) FROM calorie_tracker WHERE user_id = ? AND date(created_at) = date('now', ?)",
                (user_id, f"-{days-1} days")
            )
            result = await cursor.fetchone()
            return result[0] if result[0] else 0
    
    async def get_pending_reminders(self):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "SELECT r.id, r.user_id, r.reminder_text FROM reminders r WHERE r.reminder_time <= datetime('now')",
            )
            return await cursor.fetchall()
    
    async def update_language_preference(self, user_id, language):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE users SET language_preference = ? WHERE user_id = ?",
                (language, user_id)
            )
            await db.commit()
    
    async def get_language_preference(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "SELECT language_preference FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 'ru'

# Инициализация менеджера базы данных
db_manager = DatabaseManager(config.DATABASE_NAME)

# Класс для работы с внешними API
class APIIntegration:
    @staticmethod
    async def get_weather(city):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.WEATHER_API_KEY}&units=metric&lang=ru"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                weather_desc = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]
                feels_like = data["main"]["feels_like"]
                
                return (f"🌤 Погода в {city}:\n"
                        f"• Описание: {weather_desc}\n"
                        f"• Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                        f"• Влажность: {humidity}%\n"
                        f"• Скорость ветра: {wind_speed} м/с")
            else:
                return "Не удалось получить данные о погоде. Проверьте название города."
        except Exception as e:
            logger.error(f"Ошибка при запросе погоды: {e}")
            return "Произошла ошибка при получении данных о погоде."
    
    @staticmethod
    async def get_news(category="general", count=5):
        try:
            url = f"https://newsapi.org/v2/top-headlines?category={category}&pageSize={count}&language=ru&apiKey={config.NEWS_API_KEY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data["status"] == "ok" and data["totalResults"] > 0:
                news_items = []
                for article in data["articles"][:count]:
                    title = article["title"]
                    url = article["url"]
                    news_items.append(f"• {title}\n{url}")
                
                return f"📰 Последние новости ({category}):\n\n" + "\n\n".join(news_items)
            else:
                return "Не удалось получить новости. Попробуйте позже."
        except Exception as e:
            logger.error(f"Ошибка при запросе новостей: {e}")
            return "Произошла ошибка при получении новостей."
    
    @staticmethod
    async def get_ai_response(prompt, context=""):
        try:
            headers = {
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that provides useful information and friendly conversation."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                return "Извините, я не смог обработать ваш запрос. Попробуйте еще раз."
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenAI: {e}")
            return "Произошла ошибка при обработке вашего запроса."

# Менеджер напоминаний
class ReminderManager:
    def __init__(self):
        self.active = True
        self.thread = threading.Thread(target=self.check_reminders, daemon=True)
        self.thread.start()
    
    def check_reminders(self):
        while self.active:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def process_reminders():
                    reminders = await db_manager.get_pending_reminders()
                    for reminder_id, user_id, reminder_text in reminders:
                        try:
                            await bot.send_message(
                                user_id, 
                                f"⏰ Напоминание: {reminder_text}"
                            )
                            # Удаляем отправленное напоминание
                            async with aiosqlite.connect(config.DATABASE_NAME) as db:
                                await db.execute(
                                    "DELETE FROM reminders WHERE id = ?",
                                    (reminder_id,)
                                )
                                await db.commit()
                        except Exception as e:
                            logger.error(f"Ошибка отправки напоминания: {e}")
                
                loop.run_until_complete(process_reminders())
                loop.close()
            except Exception as e:
                logger.error(f"Ошибка в потоке напоминаний: {e}")
            
            time.sleep(60)  # Проверка каждую минуту
    
    def stop(self):
        self.active = False

# Инициализация менеджера напоминаний
reminder_manager = ReminderManager()

# Создание клавиатур
def create_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🌤 Погода"),
        KeyboardButton(text="📰 Новости"),
        KeyboardButton(text="💡 Совет"),
        KeyboardButton(text="⏰ Напоминание"),
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="🎭 Отслеживание настроения"),
        KeyboardButton(text="🍎 Отслеживание калорий"),
        KeyboardButton(text="🔍 Поиск в Википедии"),
        KeyboardButton(text="🌐 Переводчик"),
        KeyboardButton(text="🎮 Игры"),
        KeyboardButton(text="📝 Обратная связь"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    builder.adjust(2)  # 2 кнопки в строке
    return builder.as_markup(resize_keyboard=True)

def create_mood_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="😊 Отлично"),
        KeyboardButton(text="😐 Нормально"),
        KeyboardButton(text="😔 Плохо"),
        KeyboardButton(text="😡 Злой"),
        KeyboardButton(text="😴 Уставший"),
        KeyboardButton(text="↩️ Назад")
    )
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)

def create_games_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🎲 Случайное число"),
        KeyboardButton(text="🎯 Угадай число"),
        KeyboardButton(text="📖 История"),
        KeyboardButton(text="🔠 Викторина"),
        KeyboardButton(text="↩️ Назад")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Утилиты для игр
class GameManager:
    def __init__(self):
        self.active_games = {}
    
    def start_number_guess(self, user_id):
        number = random.randint(1, 100)
        self.active_games[user_id] = {
            'type': 'number_guess',
            'number': number,
            'attempts': 0
        }
        return "Я загадал число от 1 до 100. Попробуй угадать!"
    
    def check_number_guess(self, user_id, guess):
        if user_id not in self.active_games or self.active_games[user_id]['type'] != 'number_guess':
            return None
        
        try:
            guess_num = int(guess)
            game = self.active_games[user_id]
            game['attempts'] += 1
            
            if guess_num == game['number']:
                attempts = game['attempts']
                del self.active_games[user_id]
                return f"🎉 Правильно! Ты угадал число за {attempts} попыток."
            elif guess_num < game['number']:
                return "⬆️ Загаданное число больше."
            else:
                return "⬇️ Загаданное число меньше."
        except ValueError:
            return "Пожалуйста, введите число."

# Инициализация менеджера игр
game_manager = GameManager()

# Обработчики команд
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await db_manager.add_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я продвинутый чат-бот с искусственным интеллектом и множеством функций:\n\n"
        "• 🌤 Узнать погоду в любом городе\n"
        "• 📰 Читать последние новости\n"
        "• 💡 Получить случайный совет\n"
        "• ⏰ Установить напоминание\n"
        "• 📊 Посмотреть статистику использования\n"
        "• 🎭 Отслеживать настроение\n"
        "• 🍎 Вести учет калорий\n"
        "• 🔍 Искать информацию в Википедии\n"
        "• 🌐 Переводить текст\n"
        "• 🎮 Играть в игры\n"
        "• 📝 Оставить обратную связь\n\n"
        "Выберите действие или просто напишите ваш вопрос!"
    )
    
    await message.answer(welcome_text, reply_markup=create_main_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📋 Доступные команды:\n\n"
        "/start - начать работу с ботом\n"
        "/weather - узнать погоду\n"
        "/news - последние новости\n"
        "/advice - случайный совет\n"
        "/reminder - установить напоминание\n"
        "/stats - ваша статистика\n"
        "/mood - отслеживание настроения\n"
        "/calories - учет калорий\n"
        "/wiki - поиск в Википедии\n"
        "/translate - перевод текста\n"
        "/games - игровое меню\n"
        "/feedback - оставить обратную связь\n"
        "/help - это сообщение\n\n"
        "Или используйте кнопки меню!"
    )
    await message.answer(help_text)

# Обработчик текстовых сообщений
@dp.message(F.text)
async def handle_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text
    
    # Обновляем статистику
    await db_manager.update_message_count(user_id)
    
    # Проверяем, является ли сообщение игровым действием
    if user_id in game_manager.active_games and game_manager.active_games[user_id]['type'] == 'number_guess':
        result = game_manager.check_number_guess(user_id, user_text)
        if result:
            await message.answer(result)
            return
    
    # Определяем намерение пользователя
    intent = nlp_processor.recognize_intent(user_text)
    
    # Анализируем sentiment сообщения
    sentiment = nlp_processor.analyze_sentiment(user_text)
    
    # Обработка различных команд через текст
    if user_text == "🌤 Погода":
        await message.answer("Введите название города:")
        await state.set_state(UserStates.waiting_for_city)
    
    elif user_text == "📰 Новости":
        news_categories = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Общие", callback_data="news_general"),
            InlineKeyboardButton(text="Технологии", callback_data="news_technology")],
            [InlineKeyboardButton(text="Спорт", callback_data="news_sports"),
            InlineKeyboardButton(text="Наука", callback_data="news_science")],
            [InlineKeyboardButton(text="Бизнес", callback_data="news_business")]
        ])
        await message.answer("Выберите категорию новостей:", reply_markup=news_categories)
    
    elif user_text == "💡 Совет":
        advice_responses = [
            "Никогда не отказывайтесь от мечты только потому, что на её осуществление потребуется много времени. Время всё равно пройдет.",
            "Единственный способ делать великие дела — это любить то, что вы делаете.",
            "Успех — это способность идти от неудачи к неудаче, не теряя энтузиазма.",
            "Ваше время ограничено, не тратьте его, живя чужой жизнью.",
            "Лучший способ предсказать будущее — создать его."
        ]
        await message.answer(f"💡 Совет: {random.choice(advice_responses)}")
    
    elif user_text == "⏰ Напоминание":
        await message.answer("Введите текст напоминания:")
        await state.set_state(UserStates.waiting_for_reminder_text)
    
    elif user_text == "📊 Статистика":
        stats = await db_manager.get_user_stats(user_id)
        if stats:
            count, created, mood = stats
            calorie_sum = await db_manager.get_calorie_summary(user_id)
            
            await message.answer(
                f"📊 Ваша статистика:\n\n"
                f"• Сообщений отправлено: {count}\n"
                f"• Дата регистрации: {created}\n"
                f"• Текущее настроение: {mood or 'не указано'}\n"
                f"• Калорий сегодня: {calorie_sum}"
            )
    
    elif user_text == "🎭 Отслеживание настроения":
        await message.answer("Как вы себя чувствуете сегодня?", reply_markup=create_mood_keyboard())
    
    elif user_text in ["😊 Отлично", "😐 Нормально", "😔 Плохо", "😡 Злой", "😴 Уставший"]:
        mood_emoji = user_text.split()[0]
        await state.update_data(mood=mood_emoji)
        await message.answer("Хотите добавить заметку о вашем настроении? (напишите 'нет' чтобы пропустить)")
        await state.set_state(UserStates.waiting_for_mood)
    
    elif user_text == "🍎 Отслеживание калорий":
        await message.answer("Что вы съели?")
        await state.set_state(UserStates.waiting_for_calorie_food)
    
    elif user_text == "🔍 Поиск в Википедии":
        await message.answer("Что вы хотите найти в Википедии?")
        await state.set_state(UserStates.waiting_for_question)
    
    elif user_text == "🌐 Переводчик":
        await message.answer("Введите текст для перевода:")
        await state.set_state(UserStates.waiting_for_translate_text)
    
    elif user_text == "🎮 Игры":
        await message.answer("Выберите игру:", reply_markup=create_games_keyboard())
    
    elif user_text == "🎲 Случайное число":
        num = random.randint(1, 100)
        await message.answer(f"🎲 Ваше случайное число: {num}")
    
    elif user_text == "🎯 Угадай число":
        response = game_manager.start_number_guess(user_id)
        await message.answer(response)
    
    elif user_text == "📖 История":
        # Получаем историю настроения за последние 7 дней
        mood_history = await db_manager.get_mood_history(user_id, 7)
        if mood_history:
            response = "📖 Ваша история настроения за последние 7 дней:\n\n"
            for mood, notes, created_at in mood_history:
                response += f"• {created_at[:10]}: {mood} - {notes or 'без заметок'}\n"
            await message.answer(response)
        else:
            await message.answer("У вас пока нет записей о настроении.")
    
    elif user_text == "↩️ Назад":
        await message.answer("Главное меню", reply_markup=create_main_keyboard())
    
    elif user_text == "📝 Обратная связь":
        await message.answer("Пожалуйста, напишите ваш отзыв или предложение:")
        await state.set_state(UserStates.waiting_for_feedback)
    
    elif user_text == "ℹ️ Помощь":
        await cmd_help(message)
    
    elif intent:
        # Если распознано намерение, используем ответ из intents.json
        response = random.choice(intent["responses"])
        await message.answer(response)
        await db_manager.add_message_to_history(user_id, user_text, response, sentiment)
    
    else:
        # Используем AI для генерации ответа, если намерение не распознано
        ai_response = await APIIntegration.get_ai_response(user_text)
        await message.answer(ai_response)
        await db_manager.add_message_to_history(user_id, user_text, ai_response, sentiment)

# Обработчик состояния города для погоды
@dp.message(UserStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    city = message.text
    weather = await APIIntegration.get_weather(city)
    await message.answer(weather)
    await state.clear()

# Обработчик состояния напоминания
@dp.message(UserStates.waiting_for_reminder_text)
async def process_reminder_text(message: Message, state: FSMContext):
    await state.update_data(reminder_text=message.text)
    await message.answer("Через сколько минут напомнить? (Введите число)")
    await state.set_state(UserStates.waiting_for_reminder_time)

@dp.message(UserStates.waiting_for_reminder_time)
async def process_reminder_time(message: Message, state: FSMContext):
    try:
        minutes = int(message.text)
        reminder_data = await state.get_data()
        reminder_text = reminder_data['reminder_text']
        reminder_time = datetime.now().timestamp() + (minutes * 60)
        
        await db_manager.add_reminder(
            message.from_user.id, 
            reminder_text, 
            datetime.fromtimestamp(reminder_time).strftime("%Y-%m-%d %H:%M:%S")
        )
        
        await message.answer(f"⏰ Напоминание установлено: {reminder_text}")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число минут.")

# Обработчик состояния настроения
@dp.message(UserStates.waiting_for_mood)
async def process_mood_note(message: Message, state: FSMContext):
    mood_data = await state.get_data()
    mood = mood_data['mood']
    notes = message.text if message.text.lower() != "нет" else None
    
    await db_manager.add_mood_entry(message.from_user.id, mood, notes)
    await message.answer("✅ Ваше настроение сохранено!", reply_markup=create_main_keyboard())
    await state.clear()

# Обработчик состояния калорий
@dp.message(UserStates.waiting_for_calorie_food)
async def process_calorie_food(message: Message, state: FSMContext):
    await state.update_data(food_item=message.text)
    await message.answer("Сколько калорий?")
    await state.set_state(UserStates.waiting_for_calorie_amount)

@dp.message(UserStates.waiting_for_calorie_amount)
async def process_calorie_amount(message: Message, state: FSMContext):
    try:
        calories = int(message.text)
        calorie_data = await state.get_data()
        food_item = calorie_data['food_item']
        
        await db_manager.add_calorie_entry(message.from_user.id, food_item, calories)
        total_today = await db_manager.get_calorie_summary(message.from_user.id)
        
        await message.answer(
            f"✅ Добавлено: {food_item} - {calories} калорий\n"
            f"📊 Всего сегодня: {total_today} калорий",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число калорий.")

# Обработчик состояния перевода
@dp.message(UserStates.waiting_for_translate_text)
async def process_translate_text(message: Message, state: FSMContext):
    await state.update_data(translate_text=message.text)
    
    languages = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Английский", callback_data="lang_en"),
        InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="Немецкий", callback_data="lang_de"),
        InlineKeyboardButton(text="Французский", callback_data="lang_fr")],
        [InlineKeyboardButton(text="Испанский", callback_data="lang_es")]
    ])
    
    await message.answer("Выберите язык перевода:", reply_markup=languages)
    await state.set_state(UserStates.waiting_for_language)

# Обработчик состояния языка для перевода
@dp.callback_query(UserStates.waiting_for_language)
async def process_translation_language(callback_query: types.CallbackQuery, state: FSMContext):
    lang_code = callback_query.data.replace("lang_", "")
    lang_names = {
        "en": "английский",
        "ru": "русский",
        "de": "немецкий",
        "fr": "французский",
        "es": "испанский"
    }
    
    translate_data = await state.get_data()
    text_to_translate = translate_data['translate_text']
    
    translated_text = nlp_processor.translate_text(text_to_translate, lang_code)
    
    await callback_query.message.answer(
        f"🌐 Перевод ({lang_names[lang_code]}):\n\n{translated_text}",
        reply_markup=create_main_keyboard()
    )
    await state.clear()
    await callback_query.answer()

# Обработчик состояния вопроса для Википедии
@dp.message(UserStates.waiting_for_question)
async def process_wiki_search(message: Message, state: FSMContext):
    query = message.text
    try:
        wikipedia.set_lang("ru")
        search_results = wikipedia.search(query)
        if search_results:
            page = wikipedia.page(search_results[0])
            summary = page.summary[:1000] + "..." if len(page.summary) > 1000 else page.summary
            await message.answer(
                f"🔍 Результат поиска по запросу '{query}':\n\n{summary}\n\n"
                f"📖 Полная статья: {page.url}",
                reply_markup=create_main_keyboard()
            )
        else:
            await message.answer("По вашему запросу ничего не найдено.")
    except Exception as e:
        logger.error(f"Ошибка поиска в Википедии: {e}")
        await message.answer("Произошла ошибка при поиске. Попробуйте другой запрос.")
    
    await state.clear()

# Обработчик обратной связи
@dp.message(UserStates.waiting_for_feedback)
async def process_feedback(message: Message, state: FSMContext):
    feedback = message.text
    user = message.from_user
    
    # Отправляем отзыв администраторам
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id, 
                f"📝 Новый отзыв от @{user.username}:\n\n{feedback}"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки отзыва админу: {e}")
    
    await message.answer("Спасибо за ваш отзыв! Мы ценим ваше мнение.", reply_markup=create_main_keyboard())
    await state.clear()

# Обработчик инлайн-кнопок новостей
@dp.callback_query(F.data.startswith("news_"))
async def process_news_category(callback_query: types.CallbackQuery):
    category = callback_query.data.replace("news_", "")
    news = await APIIntegration.get_news(category)
    await callback_query.message.answer(news)
    await callback_query.answer()

# Запуск бота
async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
        reminder_manager.stop()
    finally:
        logger.info("Бот остановлен")