import asyncio
from fastapi import APIRouter, HTTPException

from src.api.deps import CurrentUser, SessionDep
from src.models.message import MessageCreate, MessageOut
import src.repositories.sessions as sessions_repo
import src.repositories.messages as messages_repo
from src.services import bot


router = APIRouter(tags=["Chat"])


@router.post("/chat/session")
async def create_chat_session(current_user: CurrentUser, db_session: SessionDep):
    session = await sessions_repo.create_session(db_session, current_user.id)
    return session


@router.post("/chat/message", status_code=201)
async def handle_message(current_user: CurrentUser, session: SessionDep, message_create: MessageCreate):
    check_session = await sessions_repo.get_session(session, message_create.session_id)
    if not check_session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if check_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    await messages_repo.save_message(session, message_create)
    if message_create.sender_type == "bot":
        return None

    bot_answer = bot.get_bot_answer(message_create.text)
    bot_message_create = MessageCreate(session_id=message_create.session_id, sender_type="bot", text=bot_answer)
    await messages_repo.save_message(session, bot_message_create)
    await asyncio.sleep(1.5)
    return { "answer": bot_answer }


@router.get("/chat/history/{session_id}", response_model=list[MessageOut])
async def get_messages_history(current_user: CurrentUser, session: SessionDep, session_id: str):
    check_session = await sessions_repo.get_session(session, session_id)
    if not check_session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if check_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    messages = await messages_repo.get_messages_by_session_id(session, session_id)
    return messages


@router.delete("/chat/history/{session_id}")
async def delete_messages_history(current_user: CurrentUser, session: SessionDep, session_id: str):
    check_session = await sessions_repo.get_session(session, session_id)
    if not check_session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if check_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    await messages_repo.delete_messages_by_session_id(session, session_id)
