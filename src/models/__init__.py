from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from src.models.user import User
from src.models.session import Session
from src.models.message import Message
