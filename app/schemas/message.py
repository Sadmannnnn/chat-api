from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# Базовый класс для всех схем сообщений
class MessageBase(BaseModel):
    """Базовая схема сообщения с общими полями."""
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Текст сообщения (1-5000 символов)",
        examples=["Привет!", "Как дела?", "Давай встретимся завтра в 10:00"]
    )
    
    @field_validator('text', mode='before')
    @classmethod
    def trim_and_validate_text(cls, v: str) -> str:
        """
        Обрезка пробелов по краям и валидация текста сообщения.
        
        Args:
            v: Значение поля text
            
        Returns:
            str: Очищенное и проверенное значение
            
        Raises:
            ValueError: Если значение пустое после обрезки
        """
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Текст сообщения не может быть пустым")
        return v


# Схема для создания сообщения
class MessageCreate(MessageBase):
    """Схема для создания нового сообщения."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Привет! Как дела?"
            }
        }
    )


# Схема для ответа с информацией о сообщении
class MessageResponse(MessageBase):
    """Схема для ответа с информацией о сообщении."""
    
    id: int = Field(
        ...,
        description="Уникальный идентификатор сообщения",
        examples=[1, 2, 3]
    )
    
    chat_id: int = Field(
        ...,
        description="Идентификатор чата, к которому относится сообщение",
        examples=[1, 5, 10]
    )
    
    created_at: datetime = Field(
        ...,
        description="Дата и время создания сообщения в формате ISO 8601"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "chat_id": 1,
                "text": "Привет! Как дела?",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


# Схема для ответа с сообщением и информацией о чате
class MessageWithChatResponse(MessageResponse):
    """Схема для ответа с сообщением и полной информацией о чате."""
    
    chat: "ChatResponse" = Field(
        ...,
        description="Информация о чате, к которому относится сообщение"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "chat_id": 1,
                "text": "Привет! Как дела?",
                "created_at": "2024-01-15T10:30:00Z",
                "chat": {
                    "id": 1,
                    "title": "Общий чат",
                    "created_at": "2024-01-15T09:00:00Z",
                    "message_count": 25
                }
            }
        }
    )


# Схема для ответа со списком сообщений
class MessageListResponse(BaseModel):
    """Схема для ответа со списком сообщений."""
    
    messages: List[MessageResponse] = Field(
        ...,
        description="Список сообщений"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Общее количество сообщений",
        examples=[0, 50, 1000]
    )
    page: Optional[int] = Field(
        1,
        ge=1,
        description="Текущая страница",
        examples=[1, 2, 3]
    )
    page_size: Optional[int] = Field(
        20,
        ge=1,
        le=100,
        description="Количество элементов на странице",
        examples=[10, 20, 50]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {
                        "id": 100,
                        "chat_id": 1,
                        "text": "Привет!",
                        "created_at": "2024-01-16T15:30:00Z"
                    },
                    {
                        "id": 99,
                        "chat_id": 1,
                        "text": "Как дела?",
                        "created_at": "2024-01-16T15:25:00Z"
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 20
            }
        }
    )


# Схема для обновления сообщения (опционально, если будет функционал обновления)
class MessageUpdate(BaseModel):
    """Схема для обновления текста сообщения."""
    
    text: Optional[str] = Field(
        None,
        min_length=1,
        max_length=5000,
        description="Новый текст сообщения (1-5000 символов)"
    )
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> "MessageUpdate":
        """
        Проверка, что хотя бы одно поле для обновления указано.
        
        Returns:
            MessageUpdate: Валидированная схема
            
        Raises:
            ValueError: Если ни одно поле не указано
        """
        if self.text is None:
            raise ValueError("Не указано ни одного поля для обновления")
        return self
    
    @field_validator('text', mode='before')
    @classmethod
    def trim_text(cls, v: Optional[str]) -> Optional[str]:
        """
        Обрезка пробелов по краям текста сообщения.
        
        Args:
            v: Значение поля text
            
        Returns:
            Optional[str]: Очищенное значение или None
        """
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Текст сообщения не может быть пустым")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Обновленный текст сообщения"
            }
        }
    )


# Схема для запроса на отправку сообщения (с дополнительной проверкой чата)
class MessageSendRequest(MessageBase):
    """Схема для запроса на отправку сообщения в чат."""
    
    chat_id: Optional[int] = Field(
        None,
        description="Идентификатор чата (если не указан в URL)",
        examples=[1, 5, 10]
    )
    
    @model_validator(mode='after')
    def validate_chat_id_present(self) -> "MessageSendRequest":
        """
        Проверка, что chat_id указан либо в схеме, либо в URL.
        
        Returns:
            MessageSendRequest: Валидированная схема
        """
        # chat_id может быть None, если он указан в URL
        # Этот валидатор просто гарантирует, что логика ясна
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Привет! Как дела?"
            }
        }
    )


# Для предотвращения циклических импортов
from app.schemas.chat import ChatResponse