import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(20), unique=True, nullable=True)
    temp_uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    account_name = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    signature = Column(String(60), nullable=False, default="此人很懒，暂无签名~")
    css_style = Column(String(50), default="classic")
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(255), nullable=True)
    role = Column(String(20), default="player")
    wins_total = Column(Integer, default=0)
    wins_entertain = Column(Integer, default=0)
    wins_normal = Column(Integer, default=0)
    wins_ai = Column(Integer, default=0)
    last_login_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("UserSession", back_populates="user", lazy="selectin")
    temp_credentials = relationship("TempCredential", back_populates="user", lazy="selectin")

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    jwt_jti = Column(String(36), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="sessions")

class TempCredential(Base):
    __tablename__ = "temp_credentials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    temp_uuid = Column(String(36), ForeignKey("users.temp_uuid"), nullable=False)
    login_id = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    otp_code_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    user = relationship("User", back_populates="temp_credentials")
