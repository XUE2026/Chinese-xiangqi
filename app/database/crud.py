from datetime import datetime
from typing import Optional
from sqlalchemy import select, delete, update
from app.database.connection import async_session
from app.models.user import User, UserSession, TempCredential
from app.models.game import Game, GameParticipant, GameRecord
from app.models.system import SystemFlag

async def create_user(**kwargs) -> User:
    async with async_session() as session:
        user = User(**kwargs)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def get_user_by_account(account_name: str) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.account_name == account_name, User.is_active == True))
        return result.scalar_one_or_none()

async def get_user_by_id(user_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

async def get_user_by_user_id(user_id_str: str) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id_str))
        return result.scalar_one_or_none()

async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.id))
        return list(result.scalars().all())

async def update_user(user_id: int, **kwargs) -> Optional[User]:
    async with async_session() as session:
        stmt = update(User).where(User.id == user_id).values(**kwargs).execution_options(synchronize_session="fetch")
        result = await session.execute(stmt)
        await session.commit()
        if result.rowcount == 0:
            return None
        user = await session.get(User, user_id)
        return user

async def delete_user(user_id: int) -> bool:
    async with async_session() as session:
        stmt = delete(User).where(User.id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

async def create_session(user_id: int, jti: str, expires_at: datetime) -> UserSession:
    async with async_session() as session:
        s = UserSession(user_id=user_id, jwt_jti=jti, expires_at=expires_at)
        session.add(s)
        await session.commit()
        await session.refresh(s)
        return s

async def get_active_session(user_id: int, jti: str) -> Optional[UserSession]:
    async with async_session() as session:
        result = await session.execute(
            select(UserSession).where(UserSession.user_id == user_id, UserSession.jwt_jti == jti, UserSession.expires_at > datetime.utcnow())
        )
        return result.scalar_one_or_none()

async def invalidate_user_sessions(user_id: int) -> None:
    async with async_session() as session:
        stmt = delete(UserSession).where(UserSession.user_id == user_id)
        await session.execute(stmt)
        await session.commit()

async def create_temp_credential(**kwargs) -> TempCredential:
    async with async_session() as session:
        tc = TempCredential(**kwargs)
        session.add(tc)
        await session.commit()
        await session.refresh(tc)
        return tc

async def get_temp_credential(login_id: str) -> Optional[TempCredential]:
    async with async_session() as session:
        result = await session.execute(
            select(TempCredential).where(TempCredential.login_id == login_id, TempCredential.is_used == False, TempCredential.expires_at > datetime.utcnow())
        )
        return result.scalar_one_or_none()

async def mark_temp_credential_used(cred_id: int) -> bool:
    async with async_session() as session:
        stmt = update(TempCredential).where(TempCredential.id == cred_id).values(is_used=True).execution_options(synchronize_session="fetch")
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

async def create_game(**kwargs) -> Game:
    async with async_session() as session:
        game = Game(**kwargs)
        session.add(game)
        await session.commit()
        await session.refresh(game)
        return game

async def get_game_by_id(game_id: int) -> Optional[Game]:
    async with async_session() as session:
        result = await session.execute(select(Game).where(Game.id == game_id, Game.is_deleted == False))
        return result.scalar_one_or_none()

async def get_all_games() -> list[Game]:
    async with async_session() as session:
        result = await session.execute(select(Game).where(Game.is_deleted == False).order_by(Game.id.desc()))
        return list(result.scalars().all())

async def update_game(game_id: int, **kwargs) -> Optional[Game]:
    async with async_session() as session:
        stmt = update(Game).where(Game.id == game_id).values(**kwargs).execution_options(synchronize_session="fetch")
        result = await session.execute(stmt)
        await session.commit()
        if result.rowcount == 0:
            return None
        game = await session.get(Game, game_id)
        return game

async def delete_game_soft(game_id: int) -> bool:
    async with async_session() as session:
        stmt = update(Game).where(Game.id == game_id).values(is_deleted=True).execution_options(synchronize_session="fetch")
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

async def add_participant(**kwargs) -> GameParticipant:
    async with async_session() as session:
        p = GameParticipant(**kwargs)
        session.add(p)
        await session.commit()
        await session.refresh(p)
        return p

async def get_participants(game_id: int) -> list[GameParticipant]:
    async with async_session() as session:
        result = await session.execute(select(GameParticipant).where(GameParticipant.game_id == game_id).order_by(GameParticipant.queue_order))
        return list(result.scalars().all())

async def update_participant(participant_id: int, **kwargs) -> Optional[GameParticipant]:
    async with async_session() as session:
        stmt = update(GameParticipant).where(GameParticipant.id == participant_id).values(**kwargs).execution_options(synchronize_session="fetch")
        result = await session.execute(stmt)
        await session.commit()
        if result.rowcount == 0:
            return None
        p = await session.get(GameParticipant, participant_id)
        return p

async def get_system_flag(key: str) -> Optional[SystemFlag]:
    async with async_session() as session:
        result = await session.execute(select(SystemFlag).where(SystemFlag.key == key))
        return result.scalar_one_or_none()

async def set_system_flag(key: str, value: str) -> SystemFlag:
    async with async_session() as session:
        existing = await session.execute(select(SystemFlag).where(SystemFlag.key == key))
        flag = existing.scalar_one_or_none()
        if flag:
            flag.value = value
            flag.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(flag)
            return flag
        flag = SystemFlag(key=key, value=value)
        session.add(flag)
        await session.commit()
        await session.refresh(flag)
        return flag

async def create_game_record(**kwargs) -> GameRecord:
    async with async_session() as session:
        r = GameRecord(**kwargs)
        session.add(r)
        await session.commit()
        await session.refresh(r)
        return r
