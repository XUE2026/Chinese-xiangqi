from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from app.database.connection import Base

class SystemFlag(Base):
    __tablename__ = "system_flags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(200), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
