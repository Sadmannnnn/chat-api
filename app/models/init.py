"""
Модели базы данных для чатов и сообщений.

Этот модуль содержит SQLAlchemy модели для таблиц:
- Chat: чаты
- Message: сообщения

Также предоставляет фабричные методы и утилиты для работы с моделями.
"""

from app.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.models.chat import Chat
from app.models.message import Message


# Экспорт моделей и миксинов
__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "Chat",
    "Message",
]


def create_tables(engine):
    """
    Создает все таблицы в базе данных.
    
    Args:
        engine: Движок SQLAlchemy
    """
    Base.metadata.create_all(bind=engine)


def drop_tables(engine):
    """
    Удаляет все таблицы из базы данных.
    
    Args:
        engine: Движок SQLAlchemy
    """
    Base.metadata.drop_all(bind=engine)