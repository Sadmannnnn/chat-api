from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import relationship
from typing import List, Optional

from app.models.base import Base


class Chat(Base):
    """
    Модель чата.
    
    Атрибуты:
        id: Уникальный идентификатор чата
        title: Название чата (обязательное, 1-200 символов)
        created_at: Дата и время создания чата
        messages: Список сообщений в чате (отношение один-ко-многим)
    """
    
    __tablename__ = "chats"
    
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Уникальный идентификатор чата"
    )
    
    title = Column(
        String(200),
        nullable=False,
        index=True,
        doc="Название чата (максимум 200 символов)"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        doc="Дата и время создания чата"
    )
    
    # Связь с сообщениями
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(Message.created_at)",
        doc="Сообщения в чате"
    )
    
    def __repr__(self) -> str:
        """Строковое представление объекта для отладки."""
        return f"<Chat(id={self.id}, title='{self.title}', created_at={self.created_at})>"
    
    def to_dict(self) -> dict:
        """
        Преобразует объект чата в словарь.
        
        Returns:
            dict: Словарь с данными чата
        """
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message_count": self.messages.count() if hasattr(self.messages, 'count') else len(self.messages)
        }
    
    @classmethod
    def create(cls, title: str) -> "Chat":
        """
        Создает новый объект чата с валидацией.
        
        Args:
            title: Название чата
            
        Returns:
            Chat: Новый объект чата
            
        Raises:
            ValueError: Если название не проходит валидацию
        """
        # Удаляем пробелы по краям
        title = title.strip() if title else ""
        
        # Валидация
        if not title:
            raise ValueError("Название чата не может быть пустым")
        
        if len(title) > 200:
            raise ValueError(f"Название чата слишком длинное (максимум 200 символов, получено {len(title)})")
        
        return cls(title=title)
    
    @property
    def last_message(self) -> Optional["Message"]:
        """
        Возвращает последнее сообщение в чате.
        
        Returns:
            Optional[Message]: Последнее сообщение или None, если сообщений нет
        """
        if hasattr(self.messages, 'first'):
            return self.messages.first()
        elif self.messages:
            return sorted(self.messages, key=lambda m: m.created_at, reverse=True)[0]
        return None
    
    @property
    def message_count(self) -> int:
        """
        Возвращает количество сообщений в чате.
        
        Returns:
            int: Количество сообщений
        """
        if hasattr(self.messages, 'count'):
            return self.messages.count()
        return len(self.messages)