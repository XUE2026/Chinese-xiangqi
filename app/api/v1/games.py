from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_admin
from app.database.crud import add_participant, create_game, delete_game_soft, get_game_by_id, update_game
from app.models.user import User
from app.services import INITIAL_FEN

router = APIRouter(prefix="/admin/games", tags=["admin-games"])

@router.post("/")
async def create_game_endpoint(body: dict, current_user: User = Depends(get_current_admin)):
    name = body.get("name", "未命名棋局")
    game_type = body.get("type", "normal")
    step_time_limit = body.get("step_time_limit", 5)
    max_steps = body.get("max_steps", 0)
    allow_draw = body.get("allow_draw", True)
    allow_review = body.get("allow_review", True)
    player_ids = body.get("players", [])
    spectator_ids = body.get("spectators", [])
    game = await create_game(name=name, type=game_type, status="waiting", max_steps=max_steps, step_time_limit=step_time_limit, allow_draw=allow_draw, allow_review=allow_review, board_fen=INITIAL_FEN, created_by=current_user.id)
    for i, pid in enumerate(player_ids):
        await add_participant(game_id=game.id, user_id=pid, role_in_room="player", queue_order=i + 1, is_ready=False)
    for sid in spectator_ids:
        await add_participant(game_id=game.id, user_id=sid, role_in_room="spectator", is_ready=False)
    return {"status": "ok", "game_id": game.id, "name": game.name}

@router.post("/{game_id}/delete")
async def delete_game(game_id: int, body: dict, current_user: User = Depends(get_current_admin)):
    deduct_wins = body.get("deduct_wins", False)
    game = await get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="棋局不存在")
    if deduct_wins:
        from app.database.crud import get_participants, update_user, get_user_by_id
        participants = await get_participants(game_id)
        for p in participants:
            if p.role_in_room == "player":
                user = await get_user_by_id(p.user_id)
                if user and user.wins_total > 0:
                    new_total = max(0, user.wins_total - 1)
                    new_entertain = max(0, user.wins_entertain - 1) if game.type.startswith("entertain") else user.wins_entertain
                    new_normal = max(0, user.wins_normal - 1) if game.type == "normal" else user.wins_normal
                    new_ai = max(0, user.wins_ai - 1) if game.type == "ai" else user.wins_ai
                    await update_user(p.user_id, wins_total=new_total, wins_entertain=new_entertain, wins_normal=new_normal, wins_ai=new_ai)
    await delete_game_soft(game_id)
    return {"status": "ok"}

@router.post("/{game_id}/force_end")
async def force_end_game(game_id: int, current_user: User = Depends(get_current_admin)):
    game = await get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="棋局不存在")
    await update_game(game_id, status="force_draw", winner_id=None)
    return {"status": "ok", "message": "游戏已强制和棋"}
