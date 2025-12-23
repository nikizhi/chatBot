from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from src.models import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_date = Column(DateTime, default=func.now())