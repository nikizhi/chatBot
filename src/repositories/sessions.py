import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.session import Session


async def get_session(db_session: AsyncSession, session_id: str) -> Session | None:
    session = await db_session.get(Session, session_id)
    return session


async def create_session(session: AsyncSession, user_id: int) -> Session:
    new_session = Session(user_id=user_id)
    new_session.id = str(uuid.uuid4())
    session.add(new_session)
    await session.commit()
    return new_session
