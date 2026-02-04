from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_

from app.crud.base import CRUDBase
from app.models.message import Message
from app.models.chat import Chat
from app.schemas.message import MessageCreate, MessageUpdate


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    """
    CRUD операции для модели Message.
    
    Наследует базовые операции и добавляет специфичные для сообщений.
    """
    
    def __init__(self):
        """Инициализация CRUD операций для сообщений."""
        super().__init__(Message)
    
    def create_with_validation(
        self,
        db: Session,
        *,
        chat_id: int,
        obj_in: MessageCreate
    ) -> Message:
        """
        Создать сообщение с дополнительной валидацией.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            obj_in: Данные для создания сообщения
            
        Returns:
            Message: Созданное сообщение
            
        Raises:
            ValueError: Если данные не проходят валидацию
        """
        # Проверяем существование чата
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise ValueError(f"Чат с id={chat_id} не найден")
        
        # Удаляем пробелы по краям
        text = obj_in.text.strip() if obj_in.text else ""
        
        # Валидация текста
        if not text:
            raise ValueError("Текст сообщения не может быть пустым")
        
        if len(text) > 5000:
            raise ValueError(
                f"Текст сообщения слишком длинный "
                f"(максимум 5000 символов, получено {len(text)})"
            )
        
        # Создаем сообщение
        message = Message(
            chat_id=chat_id,
            text=text
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return message
    
    def get_multi_by_chat(
        self,
        db: Session,
        *,
        chat_id: int,
        skip: int = 0,
        limit: int = 100,
        order_desc: bool = True
    ) -> List[Message]:
        """
        Получить сообщения чата.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            skip: Количество пропускаемых записей
            limit: Количество возвращаемых записей
            order_desc: Сортировка по убыванию (сначала новые)
            
        Returns:
            List[Message]: Список сообщений
        """
        query = db.query(Message).filter(Message.chat_id == chat_id)
        
        # Применяем сортировку
        if order_desc:
            query = query.order_by(desc(Message.created_at))
        else:
            query = query.order_by(Message.created_at)
        
        # Применяем пагинацию
        return query.offset(skip).limit(limit).all()
    
    def get_messages_with_chat_info(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tuple[Message, Chat]]:
        """
        Получить сообщения с информацией о чате.
        
        Args:
            db: Сессия базы данных
            skip: Количество пропускаемых записей
            limit: Количество возвращаемых записей
            
        Returns:
            List[Tuple[Message, Chat]]: Список кортежей (сообщение, чат)
        """
        return (
            db.query(Message, Chat)
            .join(Chat, Message.chat_id == Chat.id)
            .order_by(desc(Message.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_latest_messages(
        self,
        db: Session,
        *,
        chat_id: int,
        limit: int = 20
    ) -> List[Message]:
        """
        Получить последние сообщения чата.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            limit: Количество сообщений
            
        Returns:
            List[Message]: Список последних сообщений
        """
        return (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
            .all()
        )
    
    def get_message_count_by_chat(self, db: Session, *, chat_id: int) -> int:
        """
        Получить количество сообщений в чате.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            
        Returns:
            int: Количество сообщений
        """
        return db.query(Message).filter(Message.chat_id == chat_id).count()
    
    def get_messages_created_after(
        self,
        db: Session,
        *,
        chat_id: int,
        datetime_filter: datetime,
        limit: int = 100
    ) -> List[Message]:
        """
        Получить сообщения чата, созданные после указанной даты.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            datetime_filter: Дата и время для фильтрации
            limit: Количество возвращаемых записей
            
        Returns:
            List[Message]: Список сообщений
        """
        return (
            db.query(Message)
            .filter(
                and_(
                    Message.chat_id == chat_id,
                    Message.created_at > datetime_filter
                )
            )
            .order_by(Message.created_at)
            .limit(limit)
            .all()
        )
    
    def search_by_text(
        self,
        db: Session,
        *,
        text_query: str,
        chat_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        Поиск сообщений по тексту.
        
        Args:
            db: Сессия базы данных
            text_query: Строка для поиска в тексте
            chat_id: Фильтр по чату (опционально)
            skip: Количество пропускаемых записей
            limit: Количество возвращаемых записей
            
        Returns:
            List[Message]: Список найденных сообщений
        """
        query = db.query(Message).filter(Message.text.ilike(f"%{text_query}%"))
        
        # Применяем фильтр по чату если указан
        if chat_id is not None:
            query = query.filter(Message.chat_id == chat_id)
        
        # Сортировка по времени создания (сначала новые)
        query = query.order_by(desc(Message.created_at))
        
        # Применяем пагинацию
        return query.offset(skip).limit(limit).all()
    
    def delete_by_chat(self, db: Session, *, chat_id: int) -> int:
        """
        Удалить все сообщения чата.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            
        Returns:
            int: Количество удаленных сообщений
        """
        result = db.query(Message).filter(Message.chat_id == chat_id).delete()
        db.commit()
        return result
    
    def get_message_stats(
        self,
        db: Session,
        *,
        chat_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Получить статистику по сообщениям.
        
        Args:
            db: Сессия базы данных
            chat_id: Фильтр по чату (опционально)
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации
            
        Returns:
            dict: Статистика сообщений
        """
        query = db.query(Message)
        
        # Применяем фильтры
        filters = []
        
        if chat_id is not None:
            filters.append(Message.chat_id == chat_id)
        
        if start_date is not None:
            filters.append(Message.created_at >= start_date)
        
        if end_date is not None:
            filters.append(Message.created_at <= end_date)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Выполняем запросы для статистики
        total_count = query.count()
        
        if total_count == 0:
            return {
                "total_count": 0,
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0
            }
        
        # Используем func для вычислений
        from sqlalchemy import func
        
        stats = db.query(
            func.count(Message.id).label("total_count"),
            func.avg(func.length(Message.text)).label("avg_length"),
            func.min(func.length(Message.text)).label("min_length"),
            func.max(func.length(Message.text)).label("max_length")
        ).filter(and_(*filters) if filters else True).first()
        
        return {
            "total_count": stats.total_count or 0,
            "avg_length": float(stats.avg_length or 0),
            "min_length": stats.min_length or 0,
            "max_length": stats.max_length or 0
        }