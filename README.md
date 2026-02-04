Chat API
REST API для управления чатами и сообщениями, построенное на FastAPI с использованием PostgreSQL, SQLAlchemy и Alembic.

 Оглавление
Основные возможности

Технологический стек

Архитектура проекта

Быстрый старт

Подробная установка

Использование API

Миграции базы данных

Тестирование

Логирование

Структура проекта

Дополнительные возможности

Развертывание в production

Вклад в проект

Лицензия

 Основные возможности
Создание и управление чатами

Создание чатов с валидацией названия

Получение чатов с пагинацией

Каскадное удаление чатов со всеми сообщениями

Отправка и получение сообщений

Отправка сообщений в чаты

Получение последних сообщений чата

Валидация текста сообщений

Полноценное API

RESTful эндпоинты

Автоматическая документация OpenAPI/Swagger

Валидация входных данных

Обработка ошибок

Безопасность и надежность

Каскадное удаление на уровне БД

SQL-инъекция защищена ORM

Валидация всех входных данных

Транзакционная целостность

Дополнительные возможности

Расширенное логирование (JSON, ротация файлов)

Полноценный CRUD слой

Миграции базы данных через Alembic

Контейнеризация с Docker

Набор тестов с покрытием

 Технологический стек
Backend
Python 3.11+ - основной язык программирования

FastAPI - современный, быстрый веб-фреймворк

SQLAlchemy 2.0 - ORM для работы с базой данных

Pydantic 2.0 - валидация данных и схемы

Alembic - система миграций базы данных

Uvicorn - ASGI-сервер для запуска приложения

База данных
PostgreSQL 15 - основная реляционная база данных

psycopg2 - адаптер PostgreSQL для Python

Контейнеризация
Docker - контейнеризация приложения

Docker Compose - оркестрация многоконтейнерного приложения

Тестирование
pytest - фреймворк для тестирования

pytest-asyncio - поддержка асинхронных тестов

TestClient - клиент для тестирования FastAPI

Инструменты разработки
Poetry (рекомендуется) / pip - управление зависимостями

Black / isort - форматирование кода

Flake8 / mypy - линтинг и проверка типов

pre-commit - хуки для контроля качества кода

 Архитектура проекта
Проект следует принципам чистой архитектуры и разделения ответственности:

text
app/
├── api/           # Маршруты и эндпоинты
├── core/          # Основные модули (конфиг, логирование)
├── crud/          # Слой доступа к данным
├── models/        # SQLAlchemy модели
├── schemas/       # Pydantic схемы
├── database.py    # Настройка БД
├── main.py        # Точка входа в приложение
└── config.py      # Конфигурация приложения
Принципы проектирования:
Разделение ответственности: каждый модуль отвечает за свою задачу

Инверсия зависимостей: зависимости внедряются через DI

DRY (Don't Repeat Yourself): повторяющийся код вынесен в утилиты

KISS (Keep It Simple): простота и понятность реализации

 Быстрый старт
Требования
Docker и Docker Compose

Или Python 3.11+ и PostgreSQL 15+

Запуск через Docker (рекомендуется)
Клонируйте репозиторий:

bash
git clone <repository-url>
cd chat-api
Создайте файл .env (опционально, есть значения по умолчанию):

bash
cp .env.example .env
# Отредактируйте .env при необходимости
Запустите приложение:

bash
docker-compose up --build
Приложение будет доступно по адресам:

API: http://localhost:8000

Документация: http://localhost:8000/docs

Альтернативная документация: http://localhost:8000/redoc

Остановка приложения
bash
docker-compose down
# Для удаления volumes (включая данные БД):
docker-compose down -v
 Подробная установка
Установка без Docker (для разработки)
Клонируйте репозиторий:

bash
git clone <repository-url>
cd chat-api
Создайте виртуальное окружение:

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
Установите зависимости:

bash
pip install -r requirements.txt
Настройте базу данных PostgreSQL:

bash
# Создайте базу данных и пользователя
sudo -u postgres psql
CREATE DATABASE chat_db;
CREATE USER chat_user WITH PASSWORD 'chat_password';
GRANT ALL PRIVILEGES ON DATABASE chat_db TO chat_user;
\q
Настройте переменные окружения:

bash
cp .env.example .env
# Отредактируйте .env для вашего окружения
Примените миграции:

bash
alembic upgrade head
Запустите сервер разработки:

bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Установка с Poetry (альтернатива)
bash
# Установите Poetry если еще не установлен
curl -sSL https://install.python-poetry.org | python3 -

# Установите зависимости
poetry install

# Активируйте виртуальное окружение
poetry shell

# Запустите приложение
poetry run uvicorn app.main:app --reload
 Конфигурация
Переменные окружения
Создайте файл .env в корневой директории:

env
# Настройки приложения
APP_NAME=Chat API
DEBUG=True

# Настройки базы данных
DATABASE_URL=postgresql://chat_user:chat_password@localhost:5432/chat_db

# Настройки логгирования
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Настройки API
MAX_MESSAGES_LIMIT=100
DEFAULT_MESSAGES_LIMIT=20
Конфигурация Docker
В docker-compose.yml предварительно настроены:

PostgreSQL 15 с настроенным пользователем и базой данных

Автоматическое применение миграций при запуске

Volume для сохранения данных БД

Health checks для БД

 Использование API
Основные эндпоинты
1. Создание чата
http
POST /chats/
Content-Type: application/json

{
  "title": "Мой новый чат"
}
Ответ:

json
{
  "id": 1,
  "title": "Мой новый чат",
  "created_at": "2024-01-15T10:30:00Z",
  "message_count": 0
}
2. Получение чата с сообщениями
http
GET /chats/{chat_id}?limit=20
Параметры:

limit (опционально, по умолчанию 20, максимум 100) - количество возвращаемых сообщений

Ответ:

json
{
  "chat": {
    "id": 1,
    "title": "Мой новый чат",
    "created_at": "2024-01-15T10:30:00Z",
    "message_count": 5
  },
  "messages": [
    {
      "id": 5,
      "chat_id": 1,
      "text": "Последнее сообщение",
      "created_at": "2024-01-15T12:00:00Z"
    },
    {
      "id": 4,
      "chat_id": 1,
      "text": "Предыдущее сообщение",
      "created_at": "2024-01-15T11:30:00Z"
    }
  ]
}
3. Отправка сообщения
http
POST /chats/{chat_id}/messages/
Content-Type: application/json

{
  "text": "Привет всем!"
}
Ответ:

json
{
  "id": 1,
  "chat_id": 1,
  "text": "Привет всем!",
  "created_at": "2024-01-15T10:30:00Z"
}
4. Удаление чата
http
DELETE /chats/{chat_id}
Ответ: 204 No Content

Дополнительные эндпоинты
Получение списка всех чатов
http
GET /chats/?skip=0&limit=100
Получение сообщения по ID
http
GET /messages/{message_id}
Получение всех сообщений чата
http
GET /chats/{chat_id}/messages/?skip=0&limit=100
Проверка здоровья
http
GET /health
GET /health/db
Валидация данных
Чат:
Название: 1-200 символов (пробелы по краям обрезаются автоматически)

Не может быть пустым после обрезки пробелов

Сообщение:
Текст: 1-5000 символов (пробелы по краям обрезаются автоматически)

Не может быть пустым после обрезки пробелов

Чат должен существовать

Обработка ошибок
API возвращает стандартные HTTP статусы:

200 OK - успешный запрос

204 No Content - успешное удаление

400 Bad Request - неверный запрос

404 Not Found - ресурс не найден

422 Unprocessable Entity - ошибка валидации

500 Internal Server Error - внутренняя ошибка сервера

Пример ответа с ошибкой:

json
{
  "detail": "Чат с id=999 не найден"
}
 Миграции базы данных
Использование Alembic
Создание новой миграции
bash
# Создать миграцию на основе изменений в моделях
alembic revision --autogenerate -m "Описание миграции"

# Создать пустую миграцию
alembic revision -m "Описание миграции"
Применение миграций
bash
# Применить все миграции
alembic upgrade head

# Применить конкретную миграцию
alembic upgrade <revision>

# Откатить одну миграцию
alembic downgrade -1

# Откатить все миграции
alembic downgrade base
Просмотр информации о миграциях
bash
# Текущая версия
alembic current

# История миграций
alembic history --verbose

# Показать доступные команды
alembic --help
В Docker контейнере
bash
# Выполнить миграции
docker-compose exec app alembic upgrade head

# Создать миграцию
docker-compose exec app alembic revision --autogenerate -m "Новая миграция"
Существующие миграции
001_initial_migration - создание таблиц chats и messages с индексами и внешними ключами

 Тестирование
Запуск тестов
bash
# Запустить все тесты
pytest

# Запустить с подробным выводом
pytest -v

# Запустить конкретный тестовый файл
pytest tests/test_chats.py

# Запустить тесты с покрытием кода
pytest --cov=app --cov-report=html

# Запустить тесты в Docker
docker-compose exec app pytest
Структура тестов
text
tests/
├── conftest.py           # Фикстуры для тестов
├── test_chats.py         # Тесты для эндпоинтов чатов
├── test_messages.py      # Тесты для эндпоинтов сообщений
└── test_integration.py   # Интеграционные тесты
Что тестируется
Тесты чатов:
Создание чата с валидацией названия

Получение чата с сообщениями и лимитами

Удаление чата с каскадным удалением сообщений

Обработка несуществующих чатов

Пагинация и лимиты

Тесты сообщений:
Отправка сообщений с валидацией текста

Отправка в несуществующий чат

Правильная сортировка сообщений

Ограничения длины текста

Интеграционные тесты:
Полный жизненный цикл чата

Одновременные запросы

Взаимодействие между чатами и сообщениями

Фикстуры
client - тестовый клиент FastAPI

db_session - изолированная сессия базы данных (SQLite in-memory)

sample_chat_data, sample_message_data - тестовые данные

 Логирование
Конфигурация логгирования
Логирование настраивается через переменные окружения:

LOG_LEVEL - уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)

LOG_FILE - путь к файлу логов

Форматы логов
Текстовый формат (по умолчанию)
text
2024-01-15 10:30:00 - chat_api - INFO - main:45 - Application started successfully
JSON формат (для production)
json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "logger": "chat_api",
  "message": "Application started successfully",
  "module": "main",
  "function": "startup_event",
  "line": 45
}
Уровни логирования
DEBUG - отладочная информация (SQL запросы, детали выполнения)

INFO - общая информация о работе приложения

WARNING - предупреждения (некритические ошибки)

ERROR - ошибки, требующие внимания

CRITICAL - критические ошибки, приводящие к остановке

Просмотр логов
В Docker
bash
# Просмотр логов приложения
docker-compose logs app

# Просмотр логов базы данных
docker-compose logs postgres

# Просмотр логов в реальном времени
docker-compose logs -f app
Файлы логов
Консольный вывод (stdout/stderr)

Файл логов (если указан LOG_FILE)

Ротация логов: максимум 5 файлов по 10MB каждый

 Структура проекта
text
chat-api/
├── app/                           # Основной код приложения
│   ├── api/                       # Маршруты API
│   │   ├── v1/
│   │   │   └── endpoints/         # Эндпоинты
│   │   │       ├── chats.py      # Эндпоинты чатов
│   │   │       └── messages.py   # Эндпоинты сообщений
│   ├── core/                      # Основные модули
│   │   ├── __init__.py
│   │   └── logger.py             # Система логирования
│   ├── crud/                      # Слой доступа к данным
│   │   ├── base.py               # Базовые CRUD операции
│   │   ├── chat.py               # CRUD для чатов
│   │   └── message.py            # CRUD для сообщений
│   ├── models/                    # Модели базы данных
│   │   ├── base.py               # Базовый класс моделей
│   │   ├── chat.py               # Модель чата
│   │   └── message.py            # Модель сообщения
│   ├── schemas/                   # Pydantic схемы
│   │   ├── chat.py               # Схемы для чатов
│   │   └── message.py            # Схемы для сообщений
│   ├── __init__.py
│   ├── config.py                 # Конфигурация приложения
│   ├── database.py               # Настройка базы данных
│   └── main.py                   # Точка входа в приложение
├── migrations/                    # Миграции базы данных
│   ├── versions/                 # Файлы миграций
│   ├── env.py                    # Конфигурация Alembic
│   └── script.py.mako            # Шаблон миграций
├── tests/                         # Тесты
│   ├── conftest.py               # Фикстуры pytest
│   ├── test_chats.py             # Тесты чатов
│   ├── test_messages.py          # Тесты сообщений
│   └── test_integration.py       # Интеграционные тесты
├── logs/                          # Директория для логов
├── .env.example                  # Пример файла окружения
├── .gitignore                    # Игнорируемые файлы Git
├── alembic.ini                   # Конфигурация Alembic
├── docker-compose.yml            # Конфигурация Docker Compose
├── Dockerfile                    # Конфигурация Docker
├── requirements.txt              # Зависимости Python
└── README.md                     # Документация
 Дополнительные возможности
Расширенное логирование
Декоратор для измерения времени выполнения
python
from app.core.logger import log_execution_time

@log_execution_time()
def long_running_function():
    # функция будет залогирована с временем выполнения
    pass
Контекстные фильтры
python
from app.core.logger import RequestContextFilter

# Добавление request_id к логам
filter = RequestContextFilter(request_id="req-123")
logger.addFilter(filter)
Дополнительные CRUD операции
Поиск чатов по названию
python
from app.crud import chat

results = chat.search_by_title(db, title_query="рабочий")
Статистика сообщений
python
from app.crud import message

stats = message.get_message_stats(
    db, 
    chat_id=1, 
    start_date=datetime(2024, 1, 1)
)
Массовые операции
python
from app.crud.utils import bulk_create, bulk_update

# Массовое создание
chats = bulk_create(db, Chat, [{"title": "Чат 1"}, {"title": "Чат 2"}])

# Массовое обновление
updated = bulk_update(db, Message, messages, {"is_read": True})
Утилиты для миграций
Создание тестовых данных
python
from app.migrations.utils import create_initial_data

create_initial_data()
Проверка подключения к БД
python
from app.migrations.utils import check_database_connection

if check_database_connection():
    print("База данных доступна")
Health checks
API предоставляет эндпоинты для мониторинга:

bash
# Базовая проверка
curl http://localhost:8000/health

# Проверка базы данных
curl http://localhost:8000/health/db

# Версия приложения
curl http://localhost:8000/health/version
 Развертывание в production
Рекомендации для production
Безопасность

Используйте HTTPS

Настройте CORS для конкретных доменов

Используйте секретные ключи для переменных окружения

Регулярно обновляйте зависимости

Производительность

Настройте connection pooling для базы данных

Используйте gunicorn с несколькими workers для FastAPI

Настройте кэширование (Redis)

Используйте CDN для статики

Мониторинг

Настройте логирование в JSON формате

Интегрируйте с системами мониторинга (Prometheus, Grafana)

Настройте алерты для критических ошибок

Используйте APM (Application Performance Monitoring)

Пример production Dockerfile
dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Создание директории для логов
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
Настройка nginx как reverse proxy
nginx
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Дополнительные настройки
    client_max_body_size 10M;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
}
Балансировка нагрузки
yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: postgres -c max_connections=200
    
  redis:
    image: redis:7-alpine
    
  app:
    build: .
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379/0
      DEBUG: "False"
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

volumes:
  postgres_data:
 Вклад в проект
Установка для разработки
Форкните репозиторий

Клонируйте свой форк

Создайте ветку для новой функциональности

Установите pre-commit хуки:

bash
pip install pre-commit
pre-commit install
Стиль кода
Проект использует:

Black для форматирования кода

isort для сортировки импортов

Flake8 для линтинга

mypy для проверки типов

Запустите проверки перед коммитом:

bash
# Форматирование кода
black app tests

# Сортировка импортов
isort app tests

# Проверка линтером
flake8 app tests

# Проверка типов
mypy app
Тестирование
Перед отправкой pull request убедитесь:

Все тесты проходят

Добавлены тесты для новой функциональности

Покрытие кода не уменьшилось

bash
pytest --cov=app --cov-report=term-missing
Документация
Обновите документацию для новых эндпоинтов

Добавьте примеры использования

Обновите README.md при необходимости


Поддержка
Если у вас возникли проблемы или вопросы:

Проверьте документацию и примеры

Посмотрите Issues на GitHub

Создайте новый Issue с подробным описанием проблемы

Примечание: Этот проект был создан как тестовое задание и демонстрирует современные подходы к разработке API на Python. Он готов к использованию в production с минимальными доработками.