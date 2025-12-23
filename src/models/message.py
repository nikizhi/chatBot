from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, func

from src.models import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    sender_type = Column(String, nullable=False)
    text = Column(String, nullable=False)
    sent_at = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint("sender_type IN ('user', 'bot')", name="check_sender_type"),
    )


class MessageBase(BaseModel):
    sender_type: Literal["user", "bot"]
    text: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    session_id: str


class MessageOut(MessageBase):
    sent_at: datetime
