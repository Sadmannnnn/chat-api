"""
Эндпоинты для проверки здоровья приложения.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Базовая проверка здоровья приложения.
    
    Returns:
        dict: Статус приложения
    """
    return {"status": "healthy", "service": "chat-api"}


@router.get("/health/db", tags=["Health"])
async def database_health_check(db: Session = Depends(get_db)):
    """
    Проверка подключения к базе данных.
    
    Args:
        db: Сессия базы данных
        
    Returns:
        dict: Статус подключения к БД
    """
    try:
        # Выполняем простой запрос к БД
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/health/version", tags=["Health"])
async def version_check():
    """
    Возвращает информацию о версии приложения.
    
    Returns:
        dict: Версия приложения
    """
    return {"version": "1.0.0", "api_version": "v1"}