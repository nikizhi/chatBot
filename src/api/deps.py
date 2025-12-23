import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from pydantic import ValidationError

from src.core.security import SECRET_KEY, ALGORITHM
from src.models.user import User
from src.models.token import TokenData
from src.core.database import AsyncSessionMaker
from src.repositories.users import get_user_by_username


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_session():
    async with AsyncSessionMaker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(db_session: SessionDep, token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(status_code=401,
                                          detail="Не получилось проверить учетные данные",
                                          headers={"Authenticate": "Bearer"})

    try:
        payload = jwt.decode(jwt=token,
                             key=SECRET_KEY,
                             algorithms=[ALGORITHM])
        token_data = TokenData(**payload)
        if not token_data.username:
            raise credentials_exception
    except (InvalidTokenError, ValidationError):
        raise credentials_exception

    user = await get_user_by_username(db_session, token_data.username)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
