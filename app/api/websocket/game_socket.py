import socketio
from typing import Any, Dict, Optional

from app.auth.jwt_handler import decode_access_token
from app.database.connection import async_session
from app.database.crud import create_game_record, get_game_by_id, get_participants, get_user_by_id, update_game
from app.services.chess_engine import apply_move, is_check, is_checkmate, is_valid_move, validate_drag_move

connected_users: Dict[str, dict] = {}
sio: Optional[socketio.AsyncServer] = None


class GameNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        token = None
        query_string = environ.get("QUERY_STRING", "")
        if "token=" in query_string:
            for param in query_string.split("&"):
                if param.startswith("token="):
                    token = param.split("=", 1)[1]
                    break

        if not token:
            await self.disconnect(sid)
            return False

        payload = decode_access_token(token)
        if not payload:
            await self.disconnect(sid)
            return False

        user_id = int(payload.get("sub", 0))
        user = await get_user_by_id(user_id)
        if not user:
            await self.disconnect(sid)
            return False

        connected_users[sid] = {
            "user_id": user.id,
            "account_name": user.account_name,
            "role": user.role,
        }
        return True

    async def on_disconnect(self, sid):
        if sid in connected_users:
            del connected_users[sid]

    async def on_join_room(self, sid, data):
        user_data = connected_users.get(sid)
        if not user_data:
            return {"status": "error", "msg": "未认证"}

        game_id = data.get("game_id")
        if not game_id:
            return {"status": "error", "msg": "缺少game_id"}

        game = await get_game_by_id(game_id)
        if not game:
            return {"status": "error", "msg": "游戏不存在"}

        participants = await get_participants(game_id)
        user_in_game = any(p.user_id == user_data["user_id"] for p in participants)
        if not user_in_game and user_data["role"] not in ("admin", "super_admin"):
            return {"status": "error", "msg": "未加入该游戏"}

        await self.enter_room(sid, f"game_{game_id}")
        return {"status": "ok", "room": f"game_{game_id}"}

    async def on_move_piece(self, sid, data):
        user_data = connected_users.get(sid)
        if not user_data:
            return {"status": "error", "msg": "未认证"}

        game_id = data.get("game_id")
        from_pos = tuple(data.get("from_pos", []))
        to_pos = tuple(data.get("to_pos", []))

        if not game_id or not from_pos or not to_pos:
            return {"status": "error", "msg": "参数不完整"}

        if len(from_pos) != 2 or len(to_pos) != 2:
            return {"status": "error", "msg": "位置格式错误"}

        game = await get_game_by_id(game_id)
        if not game:
            return {"status": "error", "msg": "游戏不存在"}

        if game.status != "playing":
            return {"status": "error", "msg": "游戏未开始"}

        if game.current_turn != user_data["user_id"]:
            return {"status": "error", "msg": "还没轮到你走棋"}

        participants = await get_participants(game_id)
        is_player = any(p.user_id == user_data["user_id"] and p.role_in_room == "player" for p in participants)
        if not is_player:
            return {"status": "error", "msg": "你不是玩家"}

        red_player = next((p for p in participants if p.role_in_room == "player" and p.queue_order == 1), None)
        side = "w" if red_player and red_player.user_id == user_data["user_id"] else "b"

        valid, msg = is_valid_move(game.board_fen, from_pos, to_pos, side)
        if not valid:
            return {"status": "error", "msg": msg}

        new_fen = apply_move(game.board_fen, from_pos, to_pos)

        from_pos_str = f"{from_pos[0]},{from_pos[1]}"
        to_pos_str = f"{to_pos[0]},{to_pos[1]}"

        await create_game_record(
            game_id=game_id,
            user_id=user_data["user_id"],
            move_from=from_pos_str,
            move_to=to_pos_str,
            fen_before=game.board_fen,
            fen_after=new_fen,
            is_drag=False,
        )

        other_player = None
        for p in participants:
            if p.role_in_room == "player" and p.user_id != user_data["user_id"]:
                other_player = p
                break

        new_turn = other_player.user_id if other_player else None

        check_status = is_check(new_fen, "w" if side == "b" else "b")
        checkmate_status = is_checkmate(new_fen, "w" if side == "b" else "b")

        new_status = game.status
        winner = None
        if checkmate_status:
            new_status = "finished"
            winner = user_data["user_id"]
            new_turn = None

        await update_game(game_id, board_fen=new_fen, current_turn=new_turn, status=new_status, winner_id=winner)

        room = f"game_{game_id}"
        await self.emit(
            "move_made",
            {
                "game_id": game_id,
                "user_id": user_data["user_id"],
                "from": list(from_pos),
                "to": list(to_pos),
                "new_fen": new_fen,
                "next_turn": new_turn,
                "is_check": check_status,
                "is_checkmate": checkmate_status,
                "winner": winner,
            },
            room=room,
        )

        return {"status": "ok"}

    async def on_admin_drag_piece(self, sid, data):
        user_data = connected_users.get(sid)
        if not user_data:
            return {"status": "error", "msg": "未认证"}

        if user_data["role"] not in ("admin", "super_admin"):
            return {"status": "error", "msg": "需要管理员权限"}

        game_id = data.get("game_id")
        from_pos = tuple(data.get("from_pos", []))
        to_pos = tuple(data.get("to_pos", []))

        if "force_win" in data or "force_draw" in data:
            return {"status": "error", "msg": "操作失败"}

        if not game_id or not from_pos or not to_pos:
            return {"status": "error", "msg": "参数不完整"}

        if len(from_pos) != 2 or len(to_pos) != 2:
            return {"status": "error", "msg": "位置格式错误"}

        game = await get_game_by_id(game_id)
        if not game:
            return {"status": "error", "msg": "游戏不存在"}

        if not game.type.startswith("entertain"):
            return {"status": "error", "msg": "仅娱乐棋局支持拖拽"}

        valid, msg = validate_drag_move(game.board_fen, from_pos, to_pos)
        if not valid:
            return {"status": "error", "msg": "违规走法"}

        new_fen = apply_move(game.board_fen, from_pos, to_pos)

        from_pos_str = f"{from_pos[0]},{from_pos[1]}"
        to_pos_str = f"{to_pos[0]},{to_pos[1]}"

        await create_game_record(
            game_id=game_id,
            user_id=user_data["user_id"],
            move_from=from_pos_str,
            move_to=to_pos_str,
            fen_before=game.board_fen,
            fen_after=new_fen,
            is_drag=True,
        )

        await update_game(game_id, board_fen=new_fen)

        room = f"game_{game_id}"
        await self.emit(
            "move_made",
            {
                "game_id": game_id,
                "user_id": user_data["user_id"],
                "from": list(from_pos),
                "to": list(to_pos),
                "new_fen": new_fen,
                "is_drag": True,
            },
            room=room,
        )

        return {"status": "ok"}


def init_socketio(sio_server: socketio.AsyncServer) -> None:
    global sio
    sio = sio_server
    sio_server.register_namespace(GameNamespace("/game"))