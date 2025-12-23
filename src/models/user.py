from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, Field

from src.models import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)

class UserBase(BaseModel):
    username: str = Field(min_length=4, max_length=64)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=32)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=4, max_length=64)
    password: str | None = Field(default=None, min_length=6, max_length=32)
