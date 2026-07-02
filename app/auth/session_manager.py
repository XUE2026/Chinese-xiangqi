from app.database.crud import get_active_session, invalidate_user_sessions

async def validate_session(user_id: int, jti: str) -> bool:
    session = await get_active_session(user_id, jti)
    return session is not None

async def invalidate_all_sessions(user_id: int) -> None:
    await invalidate_user_sessions(user_id)
