from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_

from app.crud.base import CRUDBase
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.chat import ChatCreate, ChatUpdate


class CRUDChat(CRUDBase[Chat, ChatCreate, ChatUpdate]):
    """
    CRUD операции для модели Chat.
    
    Наследует базовые операции и добавляет специфичные для чатов.
    """
    
    def __init__(self):
        """Инициализация CRUD операций для чатов."""
        super().__init__(Chat)
    
    def create_with_validation(self, db: Session, *, obj_in: ChatCreate) -> Chat:
        """
        Создать чат с дополнительной валидацией.
        
        Args:
            db: Сессия базы данных
            obj_in: Данные для создания чата
            
        Returns:
            Chat: Созданный чат
            
        Raises:
            ValueError: Если название не проходит валидацию
        """
        # Удаляем пробелы по краям
        title = obj_in.title.strip() if obj_in.title else ""
        
        # Валидация
        if not title:
            raise ValueError("Название чата не может быть пустым")
        
        if len(title) > 200:
            raise ValueError(
                f"Название чата слишком длинное "
                f"(максимум 200 символов, получено {len(title)})"
            )
        
        # Создаем чат
        chat = Chat(title=title)
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        return chat
    
    def get_with_messages(
        self,
        db: Session,
        *,
        chat_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> Optional[Tuple[Chat, List[Message]]]:
        """
        Получить чат с сообщениями.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            limit: Количество сообщений
            offset: Смещение для пагинации
            
        Returns:
            Optional[Tuple[Chat, List[Message]]]: Чат и список сообщений или None
        """
        # Получаем чат
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        
        if not chat:
            return None
        
        # Получаем сообщения чата с сортировкой по времени (сначала новые)
        messages = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(desc(Message.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return chat, messages
    
    def get_chat_with_message_count(self, db: Session, *, chat_id: int) -> Optional[dict]:
        """
        Получить чат с количеством сообщений.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            
        Returns:
            Optional[dict]: Словарь с чатом и количеством сообщений или None
        """
        # Используем подзапрос для подсчета сообщений
        from sqlalchemy import select
        
        message_count_subquery = (
            select(func.count(Message.id))
            .where(Message.chat_id == Chat.id)
            .scalar_subquery()
        )
        
        result = (
            db.query(Chat, message_count_subquery.label("message_count"))
            .filter(Chat.id == chat_id)
            .first()
        )
        
        if not result:
            return None
        
        chat, message_count = result
        return {
            "chat": chat,
            "message_count": message_count
        }
    
    def get_multi_with_stats(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Tuple[Chat, int, Optional[Message]]]:
        """
        Получить список чатов со статистикой.
        
        Args:
            db: Сессия базы данных
            skip: Количество пропускаемых записей
            limit: Количество возвращаемых записей
            search: Поиск по названию чата
            
        Returns:
            List[Tuple[Chat, int, Optional[Message]]]: Список кортежей (чат, количество сообщений, последнее сообщение)
        """
        # Подзапрос для количества сообщений
        from sqlalchemy import select
        
        message_count_subquery = (
            select(func.count(Message.id))
            .where(Message.chat_id == Chat.id)
            .scalar_subquery()
        )
        
        # Подзапрос для последнего сообщения
        last_message_subquery = (
            select(Message)
            .where(Message.chat_id == Chat.id)
            .order_by(desc(Message.created_at))
            .limit(1)
            .scalar_subquery()
        )
        
        # Основной запрос
        query = (
            db.query(
                Chat,
                message_count_subquery.label("message_count"),
                last_message_subquery.label("last_message")
            )
        )
        
        # Применяем поиск по названию если указан
        if search:
            query = query.filter(Chat.title.ilike(f"%{search}%"))
        
        # Сортировка по времени последнего сообщения или создания чата
        query = query.order_by(desc(Chat.created_at))
        
        # Применяем пагинацию
        results = query.offset(skip).limit(limit).all()
        
        return results
    
    def delete_with_messages(self, db: Session, *, chat_id: int) -> bool:
        """
        Удалить чат и все его сообщения.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            
        Returns:
            bool: True если чат удален
            
        Raises:
            ValueError: Если чат не найден
        """
        # Находим чат
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        
        if not chat:
            raise ValueError(f"Чат с id={chat_id} не найден")
        
        try:
            # Удаляем чат (сообщения удалятся каскадно)
            db.delete(chat)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
    
    def get_message_count(self, db: Session, *, chat_id: int) -> int:
        """
        Получить количество сообщений в чате.
        
        Args:
            db: Сессия базы данных
            chat_id: Идентификатор чата
            
        Returns:
            int: Количество сообщений
        """
        return db.query(Message).filter(Message.chat_id == chat_id).count()
    
    def search_by_title(
        self,
        db: Session,
        *,
        title_query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chat]:
        """
        Поиск чатов по названию.
        
        Args:
            db: Сессия базы данных
            title_query: Строка для поиска в названии
            skip: Количество пропускаемых записей
            limit: Количество возвращаемых записей
            
        Returns:
            List[Chat]: Список найденных чатов
        """
        return (
            db.query(Chat)
            .filter(Chat.title.ilike(f"%{title_query}%"))
            .order_by(Chat.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_chats_created_after(
        self,
        db: Session,
        *,
        datetime_filter,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chat]:
        """
        Получить чаты, созданные после указанной даты.
        
        Args:
            db: Сессия базы данных
            datetime_filter: Дата и время для фильтрации
            skip: Количество пропускаемых записей
            limit: Количество возвращаемых записей
            
        Returns:
            List[Chat]: Список чатов
        """
        return (
            db.query(Chat)
            .filter(Chat.created_at > datetime_filter)
            .order_by(Chat.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )