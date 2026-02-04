"""
Утилиты для работы с миграциями.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List


def run_alembic_command(command: str, args: Optional[List[str]] = None) -> bool:
    """
    Выполнить команду Alembic.
    
    Args:
        command: Команда Alembic (upgrade, downgrade, revision и т.д.)
        args: Дополнительные аргументы
        
    Returns:
        bool: True если команда выполнена успешно
    """
    if args is None:
        args = []
    
    # Путь к alembic.ini
    alembic_ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    
    if not alembic_ini_path.exists():
        print(f"Ошибка: Файл {alembic_ini_path} не найден")
        return False
    
    try:
        # Собираем команду
        cmd = ["alembic", "-c", str(alembic_ini_path), command] + args
        
        # Выполняем команду
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Выводим результат
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Предупреждение: {result.stderr}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения команды: {e}")
        if e.stderr:
            print(f"Детали ошибки: {e.stderr}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return False


def check_database_connection() -> bool:
    """
    Проверить подключение к базе данных.
    
    Returns:
        bool: True если подключение успешно
    """
    try:
        from app.database import engine
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        print("Подключение к базе данных успешно")
        return True
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return False


def get_current_revision() -> Optional[str]:
    """
    Получить текущую ревизию базы данных.
    
    Returns:
        Optional[str]: Текущая ревизия или None
    """
    try:
        from alembic.config import Config
        from alembic import command
        
        # Получаем конфигурацию
        alembic_ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
        config = Config(str(alembic_ini_path))
        
        # Получаем текущую ревизию
        with config.main_context():
            from alembic.runtime.migration import MigrationContext
            from sqlalchemy import create_engine
            
            engine = create_engine(config.get_main_option("sqlalchemy.url"))
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
    
    except Exception as e:
        print(f"Ошибка получения текущей ревизии: {e}")
        return None


def create_initial_data():
    """
    Создать начальные данные в базе данных.
    
    Эта функция может использоваться для заполнения базы данных
    тестовыми данными после выполнения миграций.
    """
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.chat import Chat
    from app.models.message import Message
    
    db = SessionLocal()
    
    try:
        # Создаем тестовые чаты
        chats_data = [
            {"title": "Общий чат"},
            {"title": "Рабочие вопросы"},
            {"title": "Личные сообщения"},
            {"title": "Техническая поддержка"},
            {"title": "Новости проекта"},
        ]
        
        for chat_data in chats_data:
            chat = Chat(title=chat_data["title"])
            db.add(chat)
        
        db.commit()
        
        # Получаем созданные чаты
        chats = db.query(Chat).all()
        
        # Создаем тестовые сообщения
        messages_data = [
            {"chat_id": chats[0].id, "text": "Добро пожаловать в общий чат!"},
            {"chat_id": chats[0].id, "text": "Сегодня обсудим планы на неделю."},
            {"chat_id": chats[1].id, "text": "Кто работает над задачей #123?"},
            {"chat_id": chats[1].id, "text": "Дедлайн по проекту - пятница."},
            {"chat_id": chats[2].id, "text": "Привет! Как дела?"},
            {"chat_id": chats[3].id, "text": "У меня проблема с доступом к системе."},
            {"chat_id": chats[4].id, "text": "Вышла новая версия приложения."},
        ]
        
        for message_data in messages_data:
            message = Message(
                chat_id=message_data["chat_id"],
                text=message_data["text"]
            )
            db.add(message)
        
        db.commit()
        print("Начальные данные успешно созданы")
    
    except Exception as e:
        db.rollback()
        print(f"Ошибка создания начальных данных: {e}")
    
    finally:
        db.close()