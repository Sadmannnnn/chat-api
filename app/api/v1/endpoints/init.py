"""
Конечные точки API версии 1.

Модули:
- chats: операции с чатами
- messages: операции с сообщениями
"""

from app.api.v1.endpoints.chats import router as chats_router
from app.api.v1.endpoints.messages import router as messages_router

# Экспорт всех маршрутизаторов
__all__ = ["chats_router", "messages_router"]