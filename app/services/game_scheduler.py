import asyncio
import logging
from typing import Optional

from app.database.crud import get_game_by_id, get_participants, update_participant

logger = logging.getLogger(__name__)

async def schedule_next_player(game_id: int, winner_id: Optional[int] = None) -> dict:
    game = await get_game_by_id(game_id)
    if not game:
        return {"action": "error", "message": "游戏不存在"}
    participants = await get_participants(game_id)
    players = [p for p in participants if p.role_in_room == "player"]
    players_sorted = sorted(players, key=lambda p: p.queue_order)
    if len(players_sorted) < 2:
        return {"action": "wait", "message": "等待更多玩家加入"}
    if len(players_sorted) == 2:
        return {"action": "ask_next_round", "message": "是否开启下一局？"}
    if winner_id is None:
        return {"action": "wait", "message": "未知胜者"}
    max_order = max(p.queue_order for p in players_sorted)
    winner = None
    loser = None
    for p in players_sorted:
        if p.user_id == winner_id:
            winner = p
        elif loser is None:
            loser = p
    if not winner or not loser:
        return {"action": "error", "message": "无法确定胜负"}
    await update_participant(loser.id, queue_order=max_order + 1)
    remaining = [p for p in players_sorted if p.id != loser.id and p.id != winner.id]
    remaining_sorted = sorted(remaining, key=lambda p: p.queue_order)
    if remaining_sorted:
        next_player = remaining_sorted[0]
        return {"action": "rotate", "winner_id": winner.user_id, "next_player_id": next_player.user_id, "message": "下一位挑战者已上场"}
    return {"action": "wait", "message": "没有更多挑战者"}

_timer_tasks: dict[int, asyncio.Task] = {}

async def _timer_expired(game_id: int) -> None:
    logger.info(f"Game {game_id}: step timer expired")
    game = await get_game_by_id(game_id)
    if game and game.status == "playing":
        logger.info(f"Game {game_id}: timeout loss for user {game.current_turn}")

def start_step_timer(game_id: int, step_time_limit: int) -> asyncio.Task:
    if game_id in _timer_tasks:
        _timer_tasks[game_id].cancel()
    task = asyncio.create_task(_timer_expired_task(game_id, step_time_limit))
    _timer_tasks[game_id] = task
    return task

async def _timer_expired_task(game_id: int, step_time_limit: int) -> None:
    try:
        await asyncio.sleep(step_time_limit * 60)
        await _timer_expired(game_id)
    except asyncio.CancelledError:
        pass
    finally:
        _timer_tasks.pop(game_id, None)
