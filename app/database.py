from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager

from app.config import settings

# Создаем движок базы данных
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=False,  # Включаем для отладки SQL-запросов
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Базовый класс для моделей
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Генератор для получения сессии базы данных.
    
    Yields:
        Session: Сессия базы данных
        
    Usage:
        db = next(get_db())
        # или через dependency injection в FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Контекстный менеджер для работы с сессией базы данных.
    
    Yields:
        Session: Сессия базы данных
        
    Usage:
        with get_db_session() as db:
            # работа с базой данных
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Инициализация базы данных.
    Создает все таблицы, определенные в моделях.
    
    Note:
        В production используйте миграции (Alembic) вместо этой функции.
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Удаление всех таблиц из базы данных.
    
    Warning:
        Используйте только для тестирования!
    """
    Base.metadata.drop_all(bind=engine)