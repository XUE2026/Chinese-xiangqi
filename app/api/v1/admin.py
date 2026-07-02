import os
import signal
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext

from app import config
from app.auth.dependencies import get_current_admin, get_current_super_admin
from app.database.crud import create_temp_credential, create_user, get_system_flag, set_system_flag
from app.models.user import User
from app.utils.file_flags import write_kill_flag, write_purge_flag, write_retain_flag
from app.utils.temp_credential import generate_temp_credential_package
from app.utils.totp import generate_totp_secret, get_totp_uri

router = APIRouter(prefix="/admin", tags=["admin"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/debug/toggle")
async def toggle_debug_mode(current_user: User = Depends(get_current_super_admin)):
    flag = await get_system_flag("DEBUG_MODE")
    current_value = flag.value if flag else "inactive"

    if current_value == "active":
        flag_updated_at = flag.updated_at if flag else datetime.utcnow()
        cooldown_end = flag_updated_at + timedelta(hours=config.DEBUG_COOLDOWN_HOURS)
        if datetime.utcnow() < cooldown_end:
            remaining = int((cooldown_end - datetime.utcnow()).total_seconds() / 3600)
            raise HTTPException(status_code=400, detail=f"调试模式冷却中，还需 {remaining} 小时才能关闭")
        new_value = "inactive"
    else:
        new_value = "active"

    await set_system_flag("DEBUG_MODE", new_value)
    return {"status": "ok", "debug_mode": new_value}


@router.post("/emergency/activate")
async def emergency_activate(current_user: User = Depends(get_current_super_admin)):
    debug_flag = await get_system_flag("DEBUG_MODE")
    debug_mode = debug_flag.value if debug_flag else "inactive"

    if debug_mode == "active":
        write_retain_flag()
    else:
        write_purge_flag()

    write_kill_flag()

    os.kill(os.getpid(), signal.SIGTERM)

    return {"status": "ok", "message": "紧急制动已触发"}


@router.post("/temp/create")
async def create_temp_credential_endpoint(body: dict, current_user: User = Depends(get_current_admin)):
    account_name = body.get("account_name")
    password = body.get("password")
    otp_code = body.get("otp_code")
    days = body.get("days", config.TEMP_CREDENTIAL_DEFAULT_DAYS)
    role = body.get("role", "temp_player")

    if not account_name or not password or not otp_code:
        raise HTTPException(status_code=400, detail="账号、密码、验证码不能为空")

    if days > config.TEMP_CREDENTIAL_MAX_DAYS:
        raise HTTPException(status_code=400, detail=f"有效期最长 {config.TEMP_CREDENTIAL_MAX_DAYS} 天")

    if role not in ("temp_player", "temp_viewer"):
        raise HTTPException(status_code=400, detail="角色无效")

    password_hash = pwd_context.hash(password)
    otp_hash = pwd_context.hash(otp_code)

    temp_uuid_val = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=days)

    user = await create_user(
        account_name=account_name,
        password_hash=password_hash,
        temp_uuid=temp_uuid_val,
        role=role,
        is_active=True,
    )

    await create_temp_credential(
        temp_uuid=temp_uuid_val,
        login_id=account_name,
        password_hash=password_hash,
        otp_code_hash=otp_hash,
        expires_at=expires_at,
        is_used=False,
    )

    package = generate_temp_credential_package(account_name, password, otp_code, days)
    return {"status": "ok", "credential": package, "message": "此凭证仅展示一次，请妥善保存"}