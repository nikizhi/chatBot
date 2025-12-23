from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.security import get_password_hash, verify_password
from src.models.user import User, UserCreate, UserUpdate


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    user_data = user_create.model_dump(exclude={"password"})
    new_user = User(**user_data, hashed_password=get_password_hash(user_create.password))
    session.add(new_user)
    await session.commit()
    return new_user

async def update_user(session: AsyncSession, user_db: User, user_update: UserUpdate) -> User:
    user_data = user_update.model_dump(exclude_unset=True)
    if "password" in user_data:
        new_password = user_data.pop("password")
        user_db.hashed_password = get_password_hash(new_password)
    for key, value in user_data.items():
        setattr(user_db, key, value)

    session.add(user_db)
    await session.commit()
    return user_db

async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    return user

async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)

async def authenticate(session: AsyncSession, username: str, password: str) -> User | None:
    user_db = await get_user_by_username(session, username)
    if not user_db:
        return None
    if not verify_password(password, user_db.hashed_password):
        return None
    return user_db
