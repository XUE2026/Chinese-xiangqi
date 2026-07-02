from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    status = Column(String(20), default="waiting")
    max_steps = Column(Integer, default=0)
    step_time_limit = Column(Integer, default=5)
    allow_draw = Column(Boolean, default=True)
    allow_review = Column(Boolean, default=True)
    current_turn = Column(Integer, nullable=True)
    board_fen = Column(Text, nullable=True)
    winner_id = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    participants = relationship("GameParticipant", back_populates="game", lazy="selectin")
    records = relationship("GameRecord", back_populates="game", lazy="selectin")

class GameParticipant(Base):
    __tablename__ = "game_participants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_in_room = Column(String(10), default="spectator")
    queue_order = Column(Integer, default=0)
    is_ready = Column(Boolean, default=False)
    game = relationship("Game", back_populates="participants")

class GameRecord(Base):
    __tablename__ = "game_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    move_from = Column(String(10), nullable=False)
    move_to = Column(String(10), nullable=False)
    fen_before = Column(Text, nullable=False)
    fen_after = Column(Text, nullable=False)
    move_time = Column(DateTime, default=datetime.utcnow)
    is_drag = Column(Boolean, default=False)
    game = relationship("Game", back_populates="records")
