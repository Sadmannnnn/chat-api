from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.chat import ChatResponse

router = APIRouter()


@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Отправить сообщение в чат",
    description="""
    Отправляет новое сообщение в указанный чат.
    
    Текст сообщения должен быть от 1 до 5000 символов.
    Нельзя отправить сообщение в несуществующий чат.
    """,
    responses={
        200: {"description": "Сообщение успешно отправлено"},
        404: {"description": "Чат не найден"},
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def create_message(
    chat_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Отправить сообщение в чат.
    
    Args:
        chat_id: Идентификатор чата
        message_data: Данные для создания сообщения
        db: Сессия базы данных
        
    Returns:
        MessageResponse: Созданное сообщение
        
    Raises:
        HTTPException: Если чат не найден или произошла ошибка при создании сообщения
    """
    # Проверяем существование чата
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Чат с id={chat_id} не найден",
        )
    
    try:
        # Создаем новое сообщение
        message = Message(
            chat_id=chat_id,
            text=message_data.text.strip(),
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return MessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            text=message.text,
            created_at=message.created_at,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отправке сообщения: {str(e)}",
        )


# Опционально: эндпоинт для получения сообщения по ID
@router.get(
    "/{message_id}",
    response_model=MessageResponse,
    summary="Получить сообщение по ID",
    description="Возвращает информацию о сообщении по его идентификатору.",
    responses={
        200: {"description": "Сообщение успешно получено"},
        404: {"description": "Сообщение не найдено"},
    },
)
async def get_message(
    message_id: int,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Получить сообщение по ID.
    
    Args:
        message_id: Идентификатор сообщения
        db: Сессия базы данных
        
    Returns:
        MessageResponse: Информация о сообщении
        
    Raises:
        HTTPException: Если сообщение не найдено
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сообщение с id={message_id} не найдено",
        )
    
    return MessageResponse(
        id=message.id,
        chat_id=message.chat_id,
        text=message.text,
        created_at=message.created_at,
    )


# Опционально: эндпоинт для получения всех сообщений чата
@router.get(
    "/",
    response_model=list[MessageResponse],
    summary="Получить все сообщения чата",
    description="Возвращает все сообщения указанного чата, отсортированные по времени создания.",
    responses={
        200: {"description": "Сообщения успешно получены"},
        404: {"description": "Чат не найден"},
    },
)
async def get_chat_messages(
    chat_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[MessageResponse]:
    """
    Получить все сообщения чата.
    
    Args:
        chat_id: Идентификатор чата
        skip: Количество пропускаемых записей
        limit: Количество возвращаемых записей
        db: Сессия базы данных
        
    Returns:
        List[MessageResponse]: Список сообщений
        
    Raises:
        HTTPException: Если чат не найден
    """
    # Проверяем существование чата
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Чат с id={chat_id} не найден",
        )
    
    # Получаем сообщения
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        MessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            text=message.text,
            created_at=message.created_at,
        )
        for message in messages
    ]


# Опционально: эндпоинт для удаления сообщения
@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить сообщение",
    description="Удаляет сообщение по его идентификатору.",
    responses={
        204: {"description": "Сообщение успешно удалено"},
        404: {"description": "Сообщение не найдено"},
    },
)
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Удалить сообщение.
    
    Args:
        message_id: Идентификатор сообщения
        db: Сессия базы данных
        
    Raises:
        HTTPException: Если сообщение не найдено
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сообщение с id={message_id} не найдено",
        )
    
    try:
        db.delete(message)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении сообщения: {str(e)}",
        )