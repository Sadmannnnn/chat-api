"""
Модуль миграций базы данных.

Использует Alembic для управления миграциями.
Все миграции находятся в директории versions.
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

__version__ = "1.0.0"
__description__ = "Миграции базы данных для Chat API"


def get_alembic_config():
    """
    Получить конфигурацию Alembic.
    
    Returns:
        dict: Конфигурация Alembic
    """
    from alembic.config import Config
    
    # Путь к alembic.ini
    alembic_ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"Файл конфигурации не найден: {alembic_ini_path}")
    
    return Config(str(alembic_ini_path))


def run_migrations():
    """
    Запуск миграций вручную.
    
    Эта функция может использоваться для запуска миграций из кода.
    """
    from alembic import command
    from alembic.config import Config
    
    config = get_alembic_config()
    
    # Выполняем миграции до последней версии
    command.upgrade(config, "head")
    print("Миграции успешно выполнены.")


def create_migration(message: str = "Auto-generated migration"):
    """
    Создание новой миграции.
    
    Args:
        message: Описание миграции
        
    Note:
        Для использования этой функции необходимо настроить autogenerate в Alembic.
    """
    from alembic import command
    from alembic.config import Config
    
    config = get_alembic_config()
    
    # Создаем новую миграцию
    command.revision(config, message=message, autogenerate=True)
    print(f"Миграция создана: {message}")


def rollback_migrations(revision: str = "-1"):
    """
    Откат миграций.
    
    Args:
        revision: Версия для отката (по умолчанию -1 - одна версия назад)
    """
    from alembic import command
    from alembic.config import Config
    
    config = get_alembic_config()
    
    # Откатываем миграции
    command.downgrade(config, revision)
    print(f"Миграции откачены до версии: {revision}")