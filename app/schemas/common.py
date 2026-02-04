"""
Общие схемы и утилиты для всех схем.
"""

from typing import TypeVar, Generic, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Параметры пагинации."""
    
    page: int = Field(
        1,
        ge=1,
        description="Номер страницы",
        examples=[1, 2, 3]
    )
    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="Количество элементов на странице",
        examples=[10, 20, 50]
    )
    
    @property
    def offset(self) -> int:
        """Вычисление смещения для SQL запроса."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Лимит для SQL запроса."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Обобщенная схема для пагинированного ответа."""
    
    items: List[T] = Field(..., description="Список элементов")
    total: int = Field(..., ge=0, description="Общее количество элементов")
    page: int = Field(..., ge=1, description="Текущая страница")
    page_size: int = Field(..., ge=1, le=100, description="Количество элементов на странице")
    total_pages: int = Field(..., ge=0, description="Общее количество страниц")
    has_next: bool = Field(..., description="Есть ли следующая страница")
    has_previous: bool = Field(..., description="Есть ли предыдущая страница")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """
        Фабричный метод для создания пагинированного ответа.
        
        Args:
            items: Список элементов на текущей странице
            total: Общее количество элементов
            page: Текущая страница
            page_size: Количество элементов на странице
            
        Returns:
            PaginatedResponse[T]: Пагинированный ответ
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )


class ErrorResponse(BaseModel):
    """Схема для ответа с ошибкой."""
    
    detail: str = Field(..., description="Описание ошибки")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время возникновения ошибки"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Чат не найден",
                "error_code": "CHAT_NOT_FOUND",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class SuccessResponse(BaseModel):
    """Схема для успешного ответа без данных."""
    
    success: bool = Field(True, description="Флаг успешного выполнения")
    message: Optional[str] = Field(None, description="Сообщение об успехе")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Время выполнения операции"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Чат успешно удален",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )