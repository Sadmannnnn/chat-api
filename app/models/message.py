from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, validates
from typing import Optional

from app.models.base import Base


class Message(Base):
    """
    Модель сообщения.
    
    Атрибуты:
        id: Уникальный идентификатор сообщения
        chat_id: Идентификатор чата (внешний ключ)
        text: Текст сообщения (обязательный, 1-5000 символов)
        created_at: Дата и время создания сообщения
        chat: Чат, к которому относится сообщение (отношение многие-к-одному)
    """
    
    __tablename__ = "messages"
    
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Уникальный идентификатор сообщения"
    )
    
    chat_id = Column(
        Integer,
        ForeignKey(
            "chats.id",
            ondelete="CASCADE",  # Каскадное удаление при удалении чата
            name="fk_message_chat_id"
        ),
        nullable=False,
        index=True,
        doc="Идентификатор чата (внешний ключ)"
    )
    
    text = Column(
        Text,
        nullable=False,
        doc="Текст сообщения (максимум 5000 символов)"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        doc="Дата и время создания сообщения"
    )
    
    # Связь с чатом
    chat = relationship(
        "Chat",
        back_populates="messages",
        lazy="joined",
        doc="Чат, к которому относится сообщение"
    )
    
    @validates('text')
    def validate_text(self, key: str, text: str) -> str:
        """
        Валидация текста сообщения.
        
        Args:
            key: Имя поля (всегда 'text')
            text: Текст сообщения
            
        Returns:
            str: Проверенный и обработанный текст
            
        Raises:
            ValueError: Если текст не проходит валидацию
        """
        # Удаляем пробелы по краям
        text = text.strip() if text else ""
        
        # Валидация
        if not text:
            raise ValueError("Текст сообщения не может быть пустым")
        
        if len(text) > 5000:
            raise ValueError(f"Текст сообщения слишком длинный (максимум 5000 символов, получено {len(text)})")
        
        return text
    
    @validates('chat_id')
    def validate_chat_id(self, key: str, chat_id: int) -> int:
        """
        Валидация идентификатора чата.
        
        Args:
            key: Имя поля (всегда 'chat_id')
            chat_id: Идентификатор чата
            
        Returns:
            int: Проверенный идентификатор чата
            
        Raises:
            ValueError: Если chat_id не положительное число
        """
        if not isinstance(chat_id, int) or chat_id <= 0:
            raise ValueError("Идентификатор чата должен быть положительным целым числом")
        
        return chat_id
    
    def __repr__(self) -> str:
        """Строковое представление объекта для отладки."""
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"<Message(id={self.id}, chat_id={self.chat_id}, text='{text_preview}', created_at={self.created_at})>"
    
    def to_dict(self, include_chat: bool = False) -> dict:
        """
        Преобразует объект сообщения в словарь.
        
        Args:
            include_chat: Включать ли информацию о чате
            
        Returns:
            dict: Словарь с данными сообщения
        """
        result = {
            "id": self.id,
            "chat_id": self.chat_id,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_chat and self.chat:
            result["chat"] = self.chat.to_dict()
        
        return result
    
    @classmethod
    def create(cls, chat_id: int, text: str) -> "Message":
        """
        Создает новый объект сообщения с валидацией.
        
        Args:
            chat_id: Идентификатор чата
            text: Текст сообщения
            
        Returns:
            Message: Новый объект сообщения
            
        Raises:
            ValueError: Если данные не проходят валидацию
        """
        # Валидация chat_id
        if not isinstance(chat_id, int) or chat_id <= 0:
            raise ValueError("Идентификатор чата должен быть положительным целым числом")
        
        # Удаляем пробелы по краям
        text = text.strip() if text else ""
        
        # Валидация текста
        if not text:
            raise ValueError("Текст сообщения не может быть пустым")
        
        if len(text) > 5000:
            raise ValueError(f"Текст сообщения слишком длинный (максимум 5000 символов, получено {len(text)})")
        
        return cls(chat_id=chat_id, text=text)
    
    @property
    def text_preview(self) -> str:
        """
        Возвращает сокращенный предварительный просмотр текста.
        
        Returns:
            str: Первые 100 символов текста с многоточием, если текст длиннее
        """
        if len(self.text) <= 100:
            return self.text
        return self.text[:97] + "..."