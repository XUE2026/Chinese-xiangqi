import re

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_super_admin
from app.database.crud import get_all_users, get_user_by_id, get_user_by_user_id, update_user
from app.models.user import User

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

USER_ID_PATTERN = re.compile(r'^[A-Za-z0-9]{3,20}$')


@router.get("/")
async def list_users(current_user: User = Depends(get_current_super_admin)):
    users = await get_all_users()
    return [
        {
            "id": u.id,
            "user_id": u.user_id,
            "account_name": u.account_name,
            "role": u.role,
            "signature": u.signature,
            "css_style": u.css_style,
            "is_active": u.is_active,
            "wins_total": u.wins_total,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.put("/{user_id_field}/id")
async def modify_user_id(user_id_field: str, body: dict, current_user: User = Depends(get_current_super_admin)):
    new_user_id = body.get("user_id", "")
    if not USER_ID_PATTERN.match(new_user_id):
        raise HTTPException(status_code=400, detail="用户ID格式错误，只能包含英文字母和数字，长度3-20位")

    user = await get_user_by_id(int(user_id_field))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    existing = await get_user_by_user_id(new_user_id)
    if existing and existing.id != user.id:
        raise HTTPException(status_code=400, detail="该用户ID已被使用")

    updated = await update_user(user.id, user_id=new_user_id)
    return {
        "status": "ok",
        "user": {"id": updated.id, "user_id": updated.user_id, "account_name": updated.account_name},
    }


@router.put("/{user_id_field}/style")
async def modify_user_style(user_id_field: str, body: dict, current_user: User = Depends(get_current_super_admin)):
    css_style = body.get("css_style", "classic")

    user = await get_user_by_id(int(user_id_field))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    updated = await update_user(user.id, css_style=css_style)
    return {"status": "ok", "user": {"id": updated.id, "css_style": updated.css_style}}
