from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.message import Message, MessageCreate


async def get_messages_by_session_id(session: AsyncSession, session_id: str):
    statement = select(Message).where(Message.session_id == session_id)
    result = await session.execute(statement)
    messages = result.scalars().all()
    return messages


async def save_message(session: AsyncSession, message_create: MessageCreate):
    new_message = Message(**message_create.model_dump())
    session.add(new_message)
    await session.commit()


async def delete_messages_by_session_id(session: AsyncSession, session_id: str):
    statement = delete(Message).where(Message.session_id == session_id)
    await session.execute(statement)
    await session.commit()