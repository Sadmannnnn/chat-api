import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Настройки приложения
    APP_NAME: str = "Chat API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Настройки базы данных
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://chat_user:chat_password@localhost:5432/chat_db"
    )
    
    # Настройки логгирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # Настройки API
    API_V1_PREFIX: str = ""
    MAX_MESSAGES_LIMIT: int = 100
    DEFAULT_MESSAGES_LIMIT: int = 20
    
    # Настройки валидации
    MIN_TITLE_LENGTH: int = 1
    MAX_TITLE_LENGTH: int = 200
    MIN_TEXT_LENGTH: int = 1
    MAX_TEXT_LENGTH: int = 5000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Создаем экземпляр настроек
settings = Settings()