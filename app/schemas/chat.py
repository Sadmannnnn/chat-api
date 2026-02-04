from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# Базовый класс для всех схем чата
class ChatBase(BaseModel):
    """Базовая схема чата с общими полями."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Название чата (1-200 символов)",
        examples=["Общий чат", "Рабочие вопросы", "Личные сообщения"]
    )
    
    @field_validator('title', mode='before')
    @classmethod
    def trim_and_validate_title(cls, v: str) -> str:
        """
        Обрезка пробелов по краям и валидация названия.
        
        Args:
            v: Значение поля title
            
        Returns:
            str: Очищенное и проверенное значение
            
        Raises:
            ValueError: Если значение пустое после обрезки
        """
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Название чата не может быть пустым")
        return v


# Схема для создания чата
class ChatCreate(ChatBase):
    """Схема для создания нового чата."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Мой новый чат"
            }
        }
    )


# Схема для ответа с информацией о чате
class ChatResponse(ChatBase):
    """Схема для ответа с информацией о чате."""
    
    id: int = Field(
        ...,
        description="Уникальный идентификатор чата",
        examples=[1, 2, 3]
    )
    
    created_at: datetime = Field(
        ...,
        description="Дата и время создания чата в формате ISO 8601"
    )
    
    message_count: Optional[int] = Field(
        None,
        description="Количество сообщений в чате",
        examples=[0, 5, 42]
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Мой новый чат",
                "created_at": "2024-01-15T10:30:00Z",
                "message_count": 5
            }
        }
    )


# Схема для элемента списка чатов
class ChatListResponseItem(BaseModel):
    """Схема для элемента в списке чатов."""
    
    id: int = Field(..., description="Уникальный идентификатор чата")
    title: str = Field(..., description="Название чата")
    created_at: datetime = Field(..., description="Дата и время создания чата")
    last_message_text: Optional[str] = Field(
        None,
        description="Текст последнего сообщения",
        examples=["Привет!", "Как дела?", "До завтра!"]
    )
    last_message_at: Optional[datetime] = Field(
        None,
        description="Дата и время последнего сообщения"
    )
    unread_count: Optional[int] = Field(
        0,
        ge=0,
        description="Количество непрочитанных сообщений",
        examples=[0, 3, 10]
    )
    
    model_config = ConfigDict(from_attributes=True)


# Схема для ответа со списком чатов
class ChatListResponse(BaseModel):
    """Схема для ответа со списком чатов."""
    
    chats: List[ChatListResponseItem] = Field(
        ...,
        description="Список чатов"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Общее количество чатов",
        examples=[0, 5, 100]
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
                "chats": [
                    {
                        "id": 1,
                        "title": "Общий чат",
                        "created_at": "2024-01-15T10:30:00Z",
                        "last_message_text": "Привет всем!",
                        "last_message_at": "2024-01-16T14:25:00Z",
                        "unread_count": 3
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20
            }
        }
    )


# Схема для ответа с чатом и сообщениями (для GET /chats/{id})
class ChatWithMessagesResponse(BaseModel):
    """Схема для ответа с чатом и последними сообщениями."""
    
    chat: ChatResponse = Field(
        ...,
        description="Информация о чате"
    )
    messages: List["MessageResponse"] = Field(
        ...,
        description="Список последних сообщений в чате (отсортированных по времени создания)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat": {
                    "id": 1,
                    "title": "Общий чат",
                    "created_at": "2024-01-15T10:30:00Z",
                    "message_count": 25
                },
                "messages": [
                    {
                        "id": 100,
                        "chat_id": 1,
                        "text": "Привет! Как дела?",
                        "created_at": "2024-01-16T15:30:00Z"
                    },
                    {
                        "id": 99,
                        "chat_id": 1,
                        "text": "Всем доброе утро!",
                        "created_at": "2024-01-16T09:15:00Z"
                    }
                ]
            }
        }
    )


# Схема для обновления чата (опционально, если будет функционал обновления)
class ChatUpdate(BaseModel):
    """Схема для обновления информации о чате."""
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Новое название чата (1-200 символов)"
    )
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> "ChatUpdate":
        """
        Проверка, что хотя бы одно поле для обновления указано.
        
        Returns:
            ChatUpdate: Валидированная схема
            
        Raises:
            ValueError: Если ни одно поле не указано
        """
        if self.title is None:
            raise ValueError("Не указано ни одного поля для обновления")
        return self
    
    @field_validator('title', mode='before')
    @classmethod
    def trim_title(cls, v: Optional[str]) -> Optional[str]:
        """
        Обрезка пробелов по краям названия чата.
        
        Args:
            v: Значение поля title
            
        Returns:
            Optional[str]: Очищенное значение или None
        """
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Название чата не может быть пустым")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Обновленное название чата"
            }
        }
    )


# Для предотвращения циклических импортов
from app.schemas.message import MessageResponse