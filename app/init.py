"""
API чатов и сообщений

Модуль предоставляет REST API для управления чатами и сообщениями.
Использует FastAPI, SQLAlchemy и PostgreSQL.
"""

__version__ = "1.0.0"
__author__ = "Chat API Team"

# Инициализация логгера
import logging
from .core.logger import setup_logger

logger = setup_logger()