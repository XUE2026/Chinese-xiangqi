from typing import Optional, Tuple

INITIAL_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
RED_PIECES = "KABNRCP"
BLACK_PIECES = "kabnrcp"

def fen_to_board_array(fen: str) -> list[list[str]]:
    board_part = fen.split(" ")[0]
    rows = board_part.split("/")
    board: list[list[str]] = []
    for row in rows:
        board_row: list[str] = []
        for ch in row:
            if ch.isdigit():
                board_row.extend([""] * int(ch))
            else:
                board_row.append(ch)
        board.append(board_row)
    return board

def parse_fen(fen: str) -> Tuple[list[list[str]], str]:
    board = fen_to_board_array(fen)
    parts = fen.split(" ")
    side = parts[1] if len(parts) > 1 else "w"
    return board, side

def _is_red(piece: str) -> bool:
    return piece and piece in RED_PIECES
def _is_black(piece: str) -> bool:
    return piece and piece in BLACK_PIECES
def _side_pieces(side: str) -> str:
    return RED_PIECES if side == "w" else BLACK_PIECES
def _opp_pieces(side: str) -> str:
    return BLACK_PIECES if side == "w" else RED_PIECES
def _in_palace(row: int, col: int, side: str) -> bool:
    if not (3 <= col <= 5):
        return False
    if side == "w":
        return 7 <= row <= 9
    else:
        return 0 <= row <= 2
def _crossed_river(row: int, side: str) -> bool:
    if side == "w":
        return row <= 4
    else:
        return row >= 5
def _on_board(row: int, col: int) -> bool:
    return 0 <= row <= 9 and 0 <= col <= 8
def _find_general(board: list[list[str]], side: str) -> Optional[Tuple[int, int]]:
    king = "K" if side == "w" else "k"
    for r in range(10):
        for c in range(9):
            if board[r][c] == king:
                return (r, c)
    return None
def _generals_face(board: list[list[str]]) -> bool:
    red_pos = _find_general(board, "w")
    black_pos = _find_general(board, "b")
    if not red_pos or not black_pos:
        return False
    if red_pos[1] != black_pos[1]:
        return False
    col = red_pos[1]
    for r in range(black_pos[0] + 1, red_pos[0]):
        if board[r][col] != "":
            return False
    return True
def _square_attacked(board: list[list[str]], row: int, col: int, by_side: str) -> bool:
    opp = _opp_pieces(by_side)
    for r in range(10):
        for c in range(9):
            if board[r][c] in opp:
                if _is_attacking(board, r, c, row, col):
                    return True
    return False
def _is_attacking(board: list[list[str]], fr: int, fc: int, tr: int, tc: int) -> bool:
    piece = board[fr][fc]
    if not piece:
        return False
    side = "w" if piece.isupper() else "b"
    valid, _ = _validate_move_raw(board, piece, fr, fc, tr, tc, side)
    return valid

def _validate_move_raw(board, piece, fr, fc, tr, tc, side):
    ptype = piece.lower()
    my_pieces = _side_pieces(side)
    target = board[tr][tc]
    if target and target in my_pieces:
        return False, "不能吃自己的棋子"
    if ptype == "k":
        return _validate_king(board, fr, fc, tr, tc, side)
    elif ptype == "a":
        return _validate_advisor(board, fr, fc, tr, tc, side)
    elif ptype == "b":
        return _validate_elephant(board, fr, fc, tr, tc, side)
    elif ptype == "n":
        return _validate_knight(board, fr, fc, tr, tc, side)
    elif ptype == "r":
        return _validate_chariot(board, fr, fc, tr, tc, side)
    elif ptype == "c":
        return _validate_cannon(board, fr, fc, tr, tc, side, target)
    elif ptype == "p":
        return _validate_pawn(board, fr, fc, tr, tc, side)
    return False, "未知棋子"

def _validate_king(board, fr, fc, tr, tc, side):
    if not _in_palace(tr, tc, side):
        return False, "将/帅不能出九宫"
    dr = abs(tr - fr)
    dc = abs(tc - fc)
    if not ((dr == 1 and dc == 0) or (dr == 0 and dc == 1)):
        if dr >= 2 and dc == 0:
            target = board[tr][tc]
            if target and target.lower() == "k" and _count_between(board, fr, fc, tr, tc) == 0:
                return True, ""
        return False, "将/帅只能走一步"
    return True, ""

def _validate_advisor(board, fr, fc, tr, tc, side):
    if not _in_palace(tr, tc, side):
        return False, "士/仕不能出九宫"
    dr = abs(tr - fr)
    dc = abs(tc - fc)
    if dr != 1 or dc != 1:
        return False, "士/仕只能走斜一步"
    return True, ""

def _validate_elephant(board, fr, fc, tr, tc, side):
    if side == "w" and tr < 5:
        return False, "相不能过河"
    if side == "b" and tr > 4:
        return False, "象不能过河"
    dr = abs(tr - fr)
    dc = abs(tc - fc)
    if dr != 2 or dc != 2:
        return False, "象/相只能走田字"
    er = (fr + tr) // 2
    ec = (fc + tc) // 2
    if board[er][ec] != "":
        return False, "塞象眼"
    return True, ""

def _validate_knight(board, fr, fc, tr, tc, side):
    dr = tr - fr
    dc = tc - fc
    abs_dr = abs(dr)
    abs_dc = abs(dc)
    if not ((abs_dr == 2 and abs_dc == 1) or (abs_dr == 1 and abs_dc == 2)):
        return False, "马走日"
    if abs_dr == 2:
        br = fr + (1 if dr > 0 else -1)
        bc = fc
    else:
        br = fr
        bc = fc + (1 if dc > 0 else -1)
    if board[br][bc] != "":
        return False, "蹩马腿"
    return True, ""

def _validate_chariot(board, fr, fc, tr, tc, side):
    if fr != tr and fc != tc:
        return False, "车走直线"
    if _count_between(board, fr, fc, tr, tc) > 0:
        return False, "车不能越子"
    return True, ""

def _validate_cannon(board, fr, fc, tr, tc, side, target):
    if fr != tr and fc != tc:
        return False, "炮走直线"
    count = _count_between(board, fr, fc, tr, tc)
    if target == "":
        if count > 0:
            return False, "炮不能越子"
        return True, ""
    else:
        if count != 1:
            return False, "炮吃子需隔一子"
        return True, ""

def _validate_pawn(board, fr, fc, tr, tc, side):
    dr = tr - fr
    dc = tc - fc
    abs_dc = abs(dc)
    if side == "w" and dr > 0:
        return False, "兵不能后退"
    if side == "b" and dr < 0:
        return False, "卒不能后退"
    crossed = _crossed_river(fr, side)
    if abs_dc == 1 and dr == 0:
        if not crossed:
            return False, "未过河不能横走"
        return True, ""
    if abs(dr) == 1 and dc == 0:
        return True, ""
    return False, "兵卒走法不对"

def _count_between(board, fr, fc, tr, tc):
    count = 0
    if fr == tr:
        step = 1 if tc > fc else -1
        for c in range(fc + step, tc, step):
            if board[fr][c] != "":
                count += 1
    elif fc == tc:
        step = 1 if tr > fr else -1
        for r in range(fr + step, tr, step):
            if board[r][fc] != "":
                count += 1
    return count

def is_valid_move(fen, from_pos, to_pos, side):
    board, current_side = parse_fen(fen)
    fr, fc = from_pos
    tr, tc = to_pos
    if not _on_board(fr, fc) or not _on_board(tr, tc):
        return False, "越出棋盘"
    piece = board[fr][fc]
    if not piece:
        return False, "没有棋子"
    my_pieces = _side_pieces(side)
    if piece not in my_pieces:
        return False, "不是你的棋子"
    valid, msg = _validate_move_raw(board, piece, fr, fc, tr, tc, side)
    if not valid:
        return False, msg
    test_board = [row[:] for row in board]
    test_board[tr][tc] = piece
    test_board[fr][fc] = ""
    if _generals_face(test_board):
        return False, "将帅不能对面"
    if is_check_board(test_board, side):
        return False, "不能送将"
    return True, ""

def is_check_board(board, side):
    pos = _find_general(board, side)
    if not pos:
        return False
    opp_side = "b" if side == "w" else "w"
    return _square_attacked(board, pos[0], pos[1], opp_side)

def is_check(fen, side):
    board, _ = parse_fen(fen)
    return is_check_board(board, side)

def apply_move(fen, from_pos, to_pos):
    board, side = parse_fen(fen)
    fr, fc = from_pos
    tr, tc = to_pos
    board[tr][tc] = board[fr][fc]
    board[fr][fc] = ""
    new_side = "b" if side == "w" else "w"
    return _board_to_fen(board, new_side)

def _board_to_fen(board, side):
    rows = []
    for row in board:
        row_str = ""
        empty = 0
        for cell in row:
            if cell == "":
                empty += 1
            else:
                if empty > 0:
                    row_str += str(empty)
                    empty = 0
                row_str += cell
        if empty > 0:
            row_str += str(empty)
        rows.append(row_str)
    return "/".join(rows) + " " + side + " - - 0 1"

def validate_drag_move(fen, from_pos, to_pos):
    board, _ = parse_fen(fen)
    fr, fc = from_pos
    tr, tc = to_pos
    if not _on_board(fr, fc) or not _on_board(tr, tc):
        return False, "违规走法"
    piece = board[fr][fc]
    if not piece:
        return False, "违规走法"
    side = "w" if piece.isupper() else "b"
    valid, msg = _validate_move_raw(board, piece, fr, fc, tr, tc, side)
    if not valid:
        return False, "违规走法"
    test_board = [row[:] for row in board]
    test_board[tr][tc] = piece
    test_board[fr][fc] = ""
    if _generals_face(test_board):
        return False, "违规走法"
    return True, ""

def is_checkmate(fen, side):
    if not is_check(fen, side):
        return False
    board, current_side = parse_fen(fen)
    my_pieces = _side_pieces(side)
    for r in range(10):
        for c in range(9):
            if board[r][c] in my_pieces:
                if _has_legal_move(board, r, c, side):
                    return False
    return True

def _has_legal_move(board, r, c, side):
    for tr in range(10):
        for tc in range(9):
            piece = board[r][c]
            valid, _ = _validate_move_raw(board, piece, r, c, tr, tc, side)
            if not valid:
                continue
            test_board = [row[:] for row in board]
            test_board[tr][tc] = piece
            test_board[r][c] = ""
            if _generals_face(test_board):
                continue
            if is_check_board(test_board, side):
                continue
            return True
    return False
