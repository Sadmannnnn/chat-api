"""
Утилиты для CRUD операций.
"""

from typing import Type, Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import inspect


def model_to_dict(model_instance: Any) -> Dict[str, Any]:
    """
    Преобразовать SQLAlchemy модель в словарь.
    
    Args:
        model_instance: Экземпляр SQLAlchemy модели
        
    Returns:
        Dict[str, Any]: Словарь с данными модели
    """
    if not model_instance:
        return {}
    
    result = {}
    for column in inspect(model_instance).mapper.column_attrs:
        value = getattr(model_instance, column.key)
        result[column.key] = value
    
    return result


def bulk_create(
    db: Session,
    model_class: Type,
    objects_data: List[Dict[str, Any]],
    batch_size: int = 100
) -> List[Any]:
    """
    Массовое создание объектов.
    
    Args:
        db: Сессия базы данных
        model_class: Класс модели
        objects_data: Список словарей с данными
        batch_size: Размер пакета
        
    Returns:
        List[Any]: Список созданных объектов
    """
    created_objects = []
    
    for i in range(0, len(objects_data), batch_size):
        batch = objects_data[i:i + batch_size]
        objects = [model_class(**data) for data in batch]
        
        db.bulk_save_objects(objects)
        db.commit()
        
        # Обновляем объекты чтобы получить их ID
        for obj in objects:
            db.refresh(obj)
        
        created_objects.extend(objects)
    
    return created_objects


def bulk_update(
    db: Session,
    model_class: Type,
    objects: List[Any],
    update_data: Dict[str, Any],
    filter_by: Optional[Dict[str, Any]] = None
) -> int:
    """
    Массовое обновление объектов.
    
    Args:
        db: Сессия базы данных
        model_class: Класс модели
        objects: Список объектов для обновления
        update_data: Данные для обновления
        filter_by: Дополнительные фильтры
        
    Returns:
        int: Количество обновленных объектов
    """
    if not objects:
        return 0
    
    # Получаем ID объектов
    object_ids = [obj.id for obj in objects]
    
    # Обновляем объекты
    query = db.query(model_class).filter(model_class.id.in_(object_ids))
    
    if filter_by:
        query = query.filter_by(**filter_by)
    
    result = query.update(update_data, synchronize_session=False)
    db.commit()
    
    return result


def get_or_create_many(
    db: Session,
    model_class: Type,
    objects_data: List[Dict[str, Any]],
    unique_fields: List[str]
) -> List[Any]:
    """
    Получить или создать несколько объектов.
    
    Args:
        db: Сессия базы данных
        model_class: Класс модели
        objects_data: Список словарей с данными
        unique_fields: Поля для проверки уникальности
        
    Returns:
        List[Any]: Список объектов
    """
    result = []
    
    for data in objects_data:
        # Формируем фильтр по уникальным полям
        filters = {field: data[field] for field in unique_fields if field in data}
        
        # Ищем существующий объект
        existing_obj = db.query(model_class).filter_by(**filters).first()
        
        if existing_obj:
            result.append(existing_obj)
        else:
            # Создаем новый объект
            new_obj = model_class(**data)
            db.add(new_obj)
            db.commit()
            db.refresh(new_obj)
            result.append(new_obj)
    
    return result