"""
Схемы для фильтрации и сортировки.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ChatFilter(BaseModel):
    """Фильтры для поиска чатов."""
    
    title: Optional[str] = Field(None, description="Фильтр по названию чата (поиск по подстроке)")
    created_after: Optional[datetime] = Field(None, description="Чаты, созданные после указанной даты")
    created_before: Optional[datetime] = Field(None, description="Чаты, созданные до указанной даты")
    has_messages: Optional[bool] = Field(None, description="Есть ли сообщения в чате")
    min_messages: Optional[int] = Field(None, ge=0, description="Минимальное количество сообщений")
    max_messages: Optional[int] = Field(None, ge=0, description="Максимальное количество сообщений")


class MessageFilter(BaseModel):
    """Фильтры для поиска сообщений."""
    
    text: Optional[str] = Field(None, description="Фильтр по тексту сообщения (поиск по подстроке)")
    created_after: Optional[datetime] = Field(None, description="Сообщения, созданные после указанной даты")
    created_before: Optional[datetime] = Field(None, description="Сообщения, созданные до указанной даты")
    chat_id: Optional[int] = Field(None, description="Фильтр по идентификатору чата")
    min_length: Optional[int] = Field(None, ge=0, description="Минимальная длина текста")
    max_length: Optional[int] = Field(None, ge=0, le=5000, description="Максимальная длина текста")


class SortField(BaseModel):
    """Поле для сортировки."""
    
    field: str = Field(..., description="Название поля для сортировки")
    descending: bool = Field(False, description="Сортировка по убыванию")


class SortParams(BaseModel):
    """Параметры сортировки."""
    
    sort_by: List[SortField] = Field(
        default_factory=list,
        description="Список полей для сортировки"
    )
    
    def to_sqlalchemy_order_by(self):
        """Преобразование параметров сортировки в формат SQLAlchemy."""
        from sqlalchemy import desc, asc
        
        order_by = []
        for sort_field in self.sort_by:
            # Здесь нужно будет сопоставить имена полей схемы с именами полей модели
            # Это зависит от конкретной реализации
            pass
        return order_by