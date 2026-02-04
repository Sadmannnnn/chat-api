"""
CRUD (Create, Read, Update, Delete) операции для работы с базой данных.

Модули:
- base: базовые CRUD операции
- chat: операции с чатами
- message: операции с сообщениями
"""

from app.crud.base import CRUDBase
from app.crud.chat import CRUDChat
from app.crud.message import CRUDMessage

# Создаем экземпляры CRUD классов для каждой модели
chat = CRUDChat()
message = CRUDMessage()

# Экспорт для удобного импорта
__all__ = ["CRUDBase", "CRUDChat", "CRUDMessage", "chat", "message"]