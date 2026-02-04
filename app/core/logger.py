import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from app.config import settings


class JSONFormatter(logging.Formatter):
    """
    Форматтер для логов в формате JSON.
    
    Полезен для интеграции с системами анализа логов (ELK Stack, Splunk и т.д.).
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует запись лога в JSON.
        
        Args:
            record: Запись лога
            
        Returns:
            str: JSON строка с данными лога
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Добавляем дополнительные поля, если они есть
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Добавляем информацию об исключении, если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Добавляем stack trace, если есть
        if record.stack_info:
            log_data["stack_trace"] = self.formatStack(record.stack_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str = "chat_api",
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_json: bool = False
) -> logging.Logger:
    """
    Настройка логгера приложения.
    
    Args:
        name: Имя логгера
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу для записи логов
        max_bytes: Максимальный размер файла лога перед ротацией
        backup_count: Количество файлов для хранения
        enable_json: Использовать JSON формат для логов
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Определяем уровень логирования
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    level = getattr(logging, log_level.upper())
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Удаляем существующие обработчики, чтобы избежать дублирования
    logger.handlers.clear()
    
    # Форматтер для логов
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для записи в файл (если указан файл для логов)
    if log_file or settings.LOG_FILE:
        log_path = Path(log_file or settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Создаем ротируемый обработчик файлов
            file_handler = RotatingFileHandler(
                str(log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            logger.warning(f"Не удалось создать файловый обработчик логов: {e}")
    
    # Настройка логирования для внешних библиотек
    setup_external_loggers(level)
    
    logger.info(f"Логгер инициализирован. Уровень: {log_level}")
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Получить логгер по имени.
    
    Args:
        name: Имя логгера (если None, возвращает корневой логгер)
        
    Returns:
        logging.Logger: Логгер
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)


def setup_external_loggers(level: int = logging.WARNING):
    """
    Настройка логирования для внешних библиотек.
    
    Args:
        level: Уровень логирования для внешних библиотек
    """
    # Устанавливаем уровень логирования для SQLAlchemy
    logging.getLogger("sqlalchemy.engine").setLevel(level)
    logging.getLogger("sqlalchemy.pool").setLevel(level)
    
    # Устанавливаем уровень логирования для Alembic
    logging.getLogger("alembic").setLevel(level)
    
    # Устанавливаем уровень логирования для Uvicorn
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Устанавливаем уровень логирования для других библиотек
    logging.getLogger("asyncio").setLevel(level)


class RequestContextFilter(logging.Filter):
    """
    Фильтр для добавления контекстной информации в логи.
    
    Добавляет информацию о запросе (request_id, user_id, etc.) в записи логов.
    """
    
    def __init__(self, name: str = "", request_id: Optional[str] = None):
        """
        Инициализация фильтра.
        
        Args:
            name: Имя фильтра
            request_id: ID запроса
        """
        super().__init__(name)
        self.request_id = request_id
        self.user_id = None
        self.ip_address = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Добавление контекстной информации в запись лога.
        
        Args:
            record: Запись лога
            
        Returns:
            bool: Всегда True (запись не фильтруется)
        """
        if self.request_id:
            record.request_id = self.request_id
        if self.user_id:
            record.user_id = self.user_id
        if self.ip_address:
            record.ip_address = self.ip_address
        
        return True


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Декоратор для логирования времени выполнения функций.
    
    Args:
        logger: Логгер для записи (если None, используется корневой логгер)
        
    Returns:
        decorator: Декоратор функции
    """
    if logger is None:
        logger = get_logger()
    
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                logger.debug(
                    f"Функция {func.__name__} выполнена за {elapsed_time:.4f} секунд",
                    extra={"execution_time": elapsed_time, "function": func.__name__}
                )
                
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(
                    f"Функция {func.__name__} завершилась с ошибкой через {elapsed_time:.4f} секунд: {str(e)}",
                    extra={"execution_time": elapsed_time, "function": func.__name__, "error": str(e)},
                    exc_info=True
                )
                raise
        
        return wrapper
    
    return decorator


# Создаем глобальный логгер
logger = setup_logger()