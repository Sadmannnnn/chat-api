"""
Валидаторы для моделей.

Содержит функции валидации, которые могут использоваться
в нескольких моделях.
"""

import re
from typing import Optional


def validate_not_empty(value: str, field_name: str = "field") -> str:
    """
    Проверяет, что строка не пустая после удаления пробелов.
    
    Args:
        value: Значение для проверки
        field_name: Название поля для сообщения об ошибке
        
    Returns:
        str: Очищенное значение
        
    Raises:
        ValueError: Если значение пустое
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} должен быть строкой")
    
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} не может быть пустым")
    
    return cleaned


def validate_max_length(value: str, max_length: int, field_name: str = "field") -> str:
    """
    Проверяет, что строка не превышает максимальную длину.
    
    Args:
        value: Значение для проверки
        max_length: Максимальная допустимая длина
        field_name: Название поля для сообщения об ошибке
        
    Returns:
        str: Проверенное значение
        
    Raises:
        ValueError: Если значение превышает максимальную длину
    """
    if len(value) > max_length:
        raise ValueError(
            f"{field_name} слишком длинный "
            f"(максимум {max_length} символов, получено {len(value)})"
        )
    return value


def validate_positive_integer(value: int, field_name: str = "field") -> int:
    """
    Проверяет, что значение является положительным целым числом.
    
    Args:
        value: Значение для проверки
        field_name: Название поля для сообщения об ошибке
        
    Returns:
        int: Проверенное значение
        
    Raises:
        ValueError: Если значение не является положительным целым числом
    """
    if not isinstance(value, int):
        raise ValueError(f"{field_name} должен быть целым числом")
    
    if value <= 0:
        raise ValueError(f"{field_name} должен быть положительным числом")
    
    return value


def sanitize_string(value: str) -> str:
    """
    Очищает строку от лишних пробелов и потенциально опасных символов.
    
    Args:
        value: Исходная строка
        
    Returns:
        str: Очищенная строка
    """
    if not isinstance(value, str):
        return str(value) if value else ""
    
    # Удаляем пробелы по краям
    cleaned = value.strip()
    
    # Заменяем множественные пробелы на один
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Удаляем управляющие символы (кроме табуляции и перевода строки)
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
    
    return cleaned