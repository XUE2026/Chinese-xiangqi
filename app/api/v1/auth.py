from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy import select

from app import config
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.auth.dependencies import get_current_user
from app.auth.session_manager import invalidate_all_sessions
from app.database.connection import async_session
from app.database.crud import (
    create_session,
    get_temp_credential,
    get_user_by_account,
    get_user_by_id,
    mark_temp_credential_used,
    update_user,
)
from app.models.user import User, TempCredential
from app.utils.totp import verify_totp
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
limiter = Limiter(key_func=get_remote_address)


@router.post("/login")
@limiter.limit(config.LOGIN_RATE_LIMIT)
async def login(request: Request):
    body = await request.json()
    account_name = body.get("account_name", "")
    password = body.get("password", "")
    otp_code = body.get("otp_code")

    if not account_name or not password:
        raise HTTPException(status_code=400, detail="账号和密码不能为空")

    user = await get_user_by_account(account_name)

    if user:
        if not pwd_context.verify(password, user.password_hash):
            raise HTTPException(status_code=401, detail="账号或密码错误")
        if user.is_2fa_enabled:
            if not otp_code or not user.totp_secret:
                raise HTTPException(status_code=401, detail="需要双因素验证码")
            if not verify_totp(user.totp_secret, otp_code):
                raise HTTPException(status_code=401, detail="验证码错误")
    else:
        temp_cred = await get_temp_credential(account_name)
        if not temp_cred:
            raise HTTPException(status_code=401, detail="账号或密码错误")
        if not pwd_context.verify(password, temp_cred.password_hash):
            raise HTTPException(status_code=401, detail="账号或密码错误")
        if not otp_code:
            raise HTTPException(status_code=401, detail="需要一次性验证码")
        if not pwd_context.verify(otp_code, temp_cred.otp_code_hash):
            raise HTTPException(status_code=401, detail="验证码错误")

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.temp_uuid == temp_cred.temp_uuid)
            )
            user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="临时凭证无效")

        await mark_temp_credential_used(temp_cred.id)

    await invalidate_all_sessions(user.id)

    token = create_access_token(user.id, user.role)
    payload = decode_access_token(token)
    jti = payload.get("jti") if payload else None
    exp_timestamp = payload.get("exp") if payload else None
    expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow() + config.JWT_ACCESS_TOKEN_EXPIRE

    if jti:
        await create_session(user.id, jti, expires_at)

    await update_user(user.id, last_login_at=datetime.utcnow())

    load_pages = []
    for page in config.LOAD_PAGES:
        text = page["text"].replace("{username}", user.account_name)
        load_pages.append({"id": page["id"], "text": text})

    return {
        "status": "ok",
        "access_token": token,
        "token_type": "bearer",
        "load_pages": load_pages,
        "resource_url": "/static/manifest.json",
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    await invalidate_all_sessions(current_user.id)
    return {"status": "ok", "message": "已登出"}