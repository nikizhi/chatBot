from datetime import timedelta
from fastapi import APIRouter, HTTPException

from src.api.deps import SessionDep
from src.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from src.models.token import Token
from src.models.user import UserCreate
from src.repositories import users as user_repo
from loguru import logger


router = APIRouter(tags=["Auth"])


@router.post("/auth/register", status_code=201)
async def register(session: SessionDep, user_create: UserCreate):
    user = await user_repo.get_user_by_username(session, user_create.username)
    if user:
        logger.warning(f'Неудачная попытка регистрации {user.username}')
        raise HTTPException(status_code=400, detail="Имя пользователя уже используется")
    logger.info(f'Пользователь успешно зашел в систему {user.username}')
    await user_repo.create_user(session, user_create)


@router.post("/auth/login", response_model=Token)
async def login(session: SessionDep, user_login: UserCreate) -> Token:
    user = await user_repo.authenticate(session, user_login.username, user_login.password)
    if not user:
        logger.warning(f'Неудачная попытка входа {user_login.username}')
        raise HTTPException(status_code=401, detail="Неверное имя или пароль")
    access_token = create_access_token(
        data={"username": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    logger.info(f'Пользователь успешно вошел в систему {user.username}')
    return Token(access_token=access_token)
