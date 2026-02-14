"""
2x8 Mini Chess Match Runner: Orchestrates head-to-head matches for A7-TwoByEightChess.

2x8 Mini Chess on a 2x8 board with King, Knight, Rook, and Pawn pieces per side.
Agents compete across multiple games with randomized color assignment.
"""

import argparse
import asyncio
from datetime import datetime
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Add utils directory to sys.path
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging
from scoreboard import update_scoreboard

logger = setup_logging(__name__)

load_dotenv()

# Configuration
try:
    NUM_GAMES_PER_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    NUM_GAMES_PER_MATCH = 100

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

MAX_MOVES_PER_GAME = 200

# Paths
RESULTS_DIR = Path(__file__).parent.parent / "results" / "twobyeightchess"
SCOREBOARD_PATH = Path(__file__).parent.parent / "scoreboard" / "A7-scoreboard.txt"
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A7-TwoByEightChess"


# ============================================================
# Shared game engine code (used by both match and human modes)
# ============================================================
GAME_ENGINE_CODE = r'''
class TwoByEightChess:
    """
    2x8 Mini Chess game engine.
    Board: 2 rows x 8 columns (row 0-1, col 0-7)
    Displayed as rows 1-2, columns a-h.
    Pieces: K/N/R/P (White), k/n/r/p (Black), '' (empty)
    """

    WHITE = 'W'
    BLACK = 'B'
    COLS = 'abcdefgh'

    def __init__(self):
        self.board = [
            ['R', 'N', 'P', '', '', 'p', 'n', 'r'],
            ['K', 'N', 'P', '', '', 'p', 'n', 'k'],
        ]
        self.current_turn = self.WHITE
        self.move_history = []
        self.position_history = []
        self._record_position()

    def _record_position(self):
        pos = (tuple(tuple(row) for row in self.board), self.current_turn)
        self.position_history.append(pos)

    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R', 'P')

    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r', 'p')

    def _is_own_piece(self, piece, color):
        if color == self.WHITE:
            return self._is_white_piece(piece)
        return self._is_black_piece(piece)

    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)

    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"

    def _notation_to_pos(self, notation):
        if len(notation) != 2:
            return None
        col_char = notation[0].lower()
        if col_char not in self.COLS:
            return None
        try:
            row = int(notation[1]) - 1
        except ValueError:
            return None
        col = self.COLS.index(col_char)
        if not self._in_bounds(row, col):
            return None
        return (row, col)

    def _find_king(self, color):
        target = 'K' if color == self.WHITE else 'k'
        for r in range(2):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

    def _get_valid_moves_for_piece(self, row, col, ignore_check=False):
        piece = self.board[row][col]
        if not piece:
            return []

        color = self.WHITE if self._is_white_piece(piece) else self.BLACK
        piece_type = self._get_piece_type(piece)
        moves = []

        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = self.board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append(((nr, nc), is_capture))

        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))

        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                    elif self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif piece_type == 'P':
            direction = 1 if color == self.WHITE else -1
            nc = col + direction
            if self._in_bounds(row, nc) and self.board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        if ignore_check:
            return moves

        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe((row, col), to_pos, color):
                valid_moves.append((to_pos, is_capture))

        return valid_moves

    def _is_move_safe(self, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = self.board[fr][fc]
        original_to = self.board[tr][tc]

        moving_piece = original_from
        if moving_piece.upper() == 'P':
            if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                moving_piece = 'R' if color == self.WHITE else 'r'
        self.board[tr][tc] = moving_piece
        self.board[fr][fc] = ''

        in_check = self._is_in_check(color)

        self.board[fr][fc] = original_from
        self.board[tr][tc] = original_to

        return not in_check

    def _is_in_check(self, color):
        king_pos = self._find_king(color)
        if king_pos is None:
            return True

        enemy_color = self.BLACK if color == self.WHITE else self.WHITE

        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    enemy_moves = self._get_valid_moves_for_piece(r, c, ignore_check=True)
                    for to_pos, _ in enemy_moves:
                        if to_pos == king_pos:
                            return True
        return False

    def _has_legal_moves(self, color):
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    if self._get_valid_moves_for_piece(r, c):
                        return True
        return False

    def _is_insufficient_material(self):
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.upper() != 'K':
                    return False
        return True

    def _is_threefold_repetition(self):
        if len(self.position_history) < 3:
            return False
        current_pos = self.position_history[-1]
        count = sum(1 for pos in self.position_history if pos == current_pos)
        return count >= 3

    def get_all_valid_moves(self, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_type = self._get_piece_type(piece)
                    from_sq = self._pos_to_notation(r, c)
                    for to_pos, is_capture in self._get_valid_moves_for_piece(r, c):
                        to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        moves.append(move_str)
        return moves

    def parse_move(self, move_str):
        if not isinstance(move_str, str):
            return None
        move_str = move_str.strip()
        if len(move_str) < 5:
            return None

        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R', 'P'):
            return None

        if 'x' in move_str.lower():
            idx = move_str.lower().index('x')
            from_notation = move_str[1:idx]
            to_notation = move_str[idx+1:]
            is_capture = True
        else:
            from_notation = move_str[1:3]
            to_notation = move_str[3:5]
            is_capture = False

        from_pos = self._notation_to_pos(from_notation)
        to_pos = self._notation_to_pos(to_notation)

        if from_pos is None or to_pos is None:
            return None

        return (piece, from_pos, to_pos, is_capture)

    def is_valid_move(self, move_str, color):
        parsed = self.parse_move(move_str)
        if not parsed:
            return False, "Invalid move notation"

        piece_type, from_pos, to_pos, is_capture = parsed
        fr, fc = from_pos

        piece = self.board[fr][fc]
        if not piece:
            return False, f"No piece at {self._pos_to_notation(fr, fc)}"

        if not self._is_own_piece(piece, color):
            return False, "Cannot move opponent's piece"

        if self._get_piece_type(piece) != piece_type:
            return False, f"Piece at {self._pos_to_notation(fr, fc)} is not a {piece_type}"

        valid_moves = self._get_valid_moves_for_piece(fr, fc)
        for valid_to, valid_capture in valid_moves:
            if valid_to == to_pos:
                if is_capture != valid_capture:
                    if is_capture:
                        return False, "No piece to capture at destination"
                    else:
                        return False, "Must use capture notation (x) when capturing"
                return True, ""

        if self._is_in_check(color):
            return False, "Must escape check"
        return False, "Invalid move for this piece"

    def make_move(self, move_str, color):
        valid, error = self.is_valid_move(move_str, color)
        if not valid:
            return False, error

        parsed = self.parse_move(move_str)
        _, from_pos, to_pos, _ = parsed
        fr, fc = from_pos
        tr, tc = to_pos

        self.board[tr][tc] = self.board[fr][fc]
        self.board[fr][fc] = ''

        piece = self.board[tr][tc]
        if piece.upper() == 'P':
            if (self._is_white_piece(piece) and tc == 7) or \
               (self._is_black_piece(piece) and tc == 0):
                self.board[tr][tc] = 'R' if self._is_white_piece(piece) else 'r'

        self.move_history.append(move_str)
        self._record_position()

        self.current_turn = self.BLACK if self.current_turn == self.WHITE else self.WHITE

        return True, ""

    def get_game_state(self):
        if self._is_insufficient_material():
            return 'draw_material'

        if self._is_threefold_repetition():
            return 'draw_repetition'

        current = self.current_turn
        in_check = self._is_in_check(current)
        has_moves = self._has_legal_moves(current)

        if not has_moves:
            if in_check:
                return 'white_wins' if current == self.BLACK else 'black_wins'
            else:
                return 'draw_stalemate'

        return 'ongoing'

    def get_board_display(self):
        header = "    " + "  ".join(c for c in 'a b c d e f g h'.split())
        row1 = "1 | " + " | ".join(p if p else '.' for p in self.board[0]) + " |"
        row2 = "2 | " + " | ".join(p if p else '.' for p in self.board[1]) + " |"
        return f"{header}\n{row1}\n{row2}"
'''


# ============================================================
# Match runner code (play_game + main for agent-vs-agent)
# ============================================================
MATCH_RUNNER_CODE = r'''
class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")


def play_game(game_num, match_stats):
    game = TwoByEightChess()

    if game_num % 2 == 1:
        white_agent_class = TwoByEightChessAgent_1
        black_agent_class = TwoByEightChessAgent_2
        white_name = "Agent-1"
        black_name = "Agent-2"
    else:
        white_agent_class = TwoByEightChessAgent_2
        black_agent_class = TwoByEightChessAgent_1
        white_name = "Agent-2"
        black_name = "Agent-1"

    print()
    print("=" * 60)
    print(f"Game {game_num}")
    a1_color = 'W' if white_name == "Agent-1" else 'B'
    a2_color = 'W' if white_name == "Agent-2" else 'B'
    print(f"Agent-1: {AGENT1_INFO} ({a1_color})")
    print(f"Agent-2: {AGENT2_INFO} ({a2_color})")
    print("-" * 60)

    # --- Init agents (crash = forfeit) ---
    try:
        agent_white = white_agent_class(white_name, game.WHITE)
    except Exception as e:
        print(f"{white_name} (W) init crash: {e}")
        match_stats[white_name]["other_crash"] += 1
        match_stats[black_name]["wins"] += 1
        match_stats[black_name]["points"] += 3
        match_stats[black_name]["score"] += 12
        match_stats[white_name]["losses"] += 1
        match_stats[white_name]["score"] -= 12

        print("Final Position: N/A (initialization crash)")
        print("-" * 40)
        print(f"Final Result: {black_name} wins by forfeit.")
        print("-" * 40)
        print("Points:")
        print(f"{black_name}: 3")
        print(f"{white_name}: 0")
        print("-" * 40)
        print("Scores:")
        print(f"{black_name}: 12")
        print(f"{white_name}: -12")
        print("=" * 60)
        return black_name

    try:
        agent_black = black_agent_class(black_name, game.BLACK)
    except Exception as e:
        print(f"{black_name} (B) init crash: {e}")
        match_stats[black_name]["other_crash"] += 1
        match_stats[white_name]["wins"] += 1
        match_stats[white_name]["points"] += 3
        match_stats[white_name]["score"] += 12
        match_stats[black_name]["losses"] += 1
        match_stats[black_name]["score"] -= 12

        print("Final Position: N/A (initialization crash)")
        print("-" * 40)
        print(f"Final Result: {white_name} wins by forfeit.")
        print("-" * 40)
        print("Points:")
        print(f"{white_name}: 3")
        print(f"{black_name}: 0")
        print("-" * 40)
        print("Scores:")
        print(f"{white_name}: 12")
        print(f"{black_name}: -12")
        print("=" * 60)
        return white_name

    agents = {game.WHITE: agent_white, game.BLACK: agent_black}
    names = {game.WHITE: white_name, game.BLACK: black_name}

    move_count = 0

    while move_count < MAX_MOVES:
        current_color = game.current_turn
        current_agent = agents[current_color]
        current_name = names[current_color]
        opponent_color = game.BLACK if current_color == game.WHITE else game.WHITE
        opponent_name = names[opponent_color]

        move = None
        valid = False

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                move = current_agent.make_move([row[:] for row in game.board], game.move_history[:])
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            print(f"{current_name} ({current_color}): TIMEOUT")
            match_stats[current_name]["timeout"] += 1
            move = None
        except Exception as e:
            print(f"{current_name} ({current_color}): CRASH '{str(e)[:80]}'")
            match_stats[current_name]["make_move_crash"] += 1
            move = None

        if move is not None:
            ok, err = game.is_valid_move(move, current_color)
            if ok:
                valid = True
            else:
                print(f"{current_name} ({current_color}): INVALID '{move}' - {err}")
                match_stats[current_name]["invalid"] += 1

        if valid:
            game.make_move(move, current_color)
            print(f"{current_name} ({current_color}): {move}")
        else:
            all_moves = game.get_all_valid_moves(current_color)
            if all_moves:
                fallback = random.choice(all_moves)
                game.make_move(fallback, current_color)
                print(f"{current_name} ({current_color}): random {fallback}")
            else:
                break

        move_count += 1

        state = game.get_game_state()
        if state != 'ongoing':
            break

    # --- Game over: determine result ---
    state = game.get_game_state()

    print()
    print("Final Position:")
    board_display = game.get_board_display()
    for line in board_display.split('\n'):
        print(f"BOARD: {line}")

    if state == 'white_wins':
        winner = names[game.WHITE]
        loser = names[game.BLACK]
        result_reason = f"{winner} wins by checkmate"
    elif state == 'black_wins':
        winner = names[game.BLACK]
        loser = names[game.WHITE]
        result_reason = f"{winner} wins by checkmate"
    elif state == 'ongoing':
        winner = "DRAW"
        result_reason = f"Draw by move limit ({MAX_MOVES} moves)"
    else:
        draw_reasons = {
            'draw_stalemate': 'stalemate',
            'draw_repetition': 'threefold repetition',
            'draw_material': 'insufficient material',
        }
        winner = "DRAW"
        result_reason = f"Draw by {draw_reasons.get(state, 'unknown')}"

    # Calculate tie-breaker score: full_moves = len(move_history) // 2
    if winner != "DRAW":
        full_moves = len(game.move_history) // 2
        if full_moves <= 5:
            winner_score = 10
        elif full_moves <= 10:
            winner_score = 5
        else:
            winner_score = 3
        loser_score = -winner_score
    else:
        winner_score = 0
        loser_score = 0

    print("-" * 40)
    print(f"Final Result: {result_reason}")
    print(f"Moves: {' - '.join(game.move_history)}")
    print("-" * 40)

    print("Points:")
    if winner != "DRAW":
        print(f"{winner}: 3")
        print(f"{loser}: 0")
    else:
        print("Agent-1: 1")
        print("Agent-2: 1")
    print("-" * 40)

    print("Scores:")
    if winner != "DRAW":
        print(f"{winner}: {winner_score}")
        print(f"{loser}: {loser_score}")
    else:
        print("Agent-1: 0")
        print("Agent-2: 0")
    print("=" * 60)

    # Update match stats
    if winner != "DRAW":
        match_stats[winner]["wins"] += 1
        match_stats[winner]["points"] += 3
        match_stats[winner]["score"] += winner_score
        match_stats[loser]["losses"] += 1
        match_stats[loser]["score"] += loser_score
    else:
        match_stats["Agent-1"]["draws"] += 1
        match_stats["Agent-1"]["points"] += 1
        match_stats["Agent-2"]["draws"] += 1
        match_stats["Agent-2"]["points"] += 1

    sys.stdout.flush()
    return winner


def main():
    match_stats = {
        "Agent-1": {
            "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0,
        },
        "Agent-2": {
            "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0,
        },
    }

    for i in range(NUM_GAMES):
        play_game(i + 1, match_stats)
        sys.stdout.flush()

    # Aggregate crash stat for backward compatibility
    for agent_key in ["Agent-1", "Agent-2"]:
        match_stats[agent_key]["crash"] = (
            match_stats[agent_key]["make_move_crash"]
            + match_stats[agent_key]["other_crash"]
        )

    print("=" * 60)
    print(f"Agent-1: {AGENT1_INFO}")
    print(f"Agent-2: {AGENT2_INFO}")
    print(f"RESULT:Agent-1={match_stats['Agent-1']['points']},Agent-2={match_stats['Agent-2']['points']}")
    print(f"SCORE:Agent-1={match_stats['Agent-1']['score']},Agent-2={match_stats['Agent-2']['score']}")
    print(f"WINS:Agent-1={match_stats['Agent-1']['wins']},Agent-2={match_stats['Agent-2']['wins']}")
    print(f"DRAWS:{match_stats['Agent-1']['draws']}")
    print(f"STATS:Agent-1={match_stats['Agent-1']}")
    print(f"STATS:Agent-2={match_stats['Agent-2']}")
    print("--- MATCH STATISTICS ---")
    print(f"Agent-1 make_move_crash: {match_stats['Agent-1']['make_move_crash']}")
    print(f"Agent-2 make_move_crash: {match_stats['Agent-2']['make_move_crash']}")
    print(f"Agent-1 other_crash: {match_stats['Agent-1']['other_crash']}")
    print(f"Agent-2 other_crash: {match_stats['Agent-2']['other_crash']}")
    print(f"Agent-1 crash (total): {match_stats['Agent-1']['crash']}")
    print(f"Agent-2 crash (total): {match_stats['Agent-2']['crash']}")
    print(f"Agent-1 Timeouts: {match_stats['Agent-1']['timeout']}")
    print(f"Agent-2 Timeouts: {match_stats['Agent-2']['timeout']}")
    print(f"Agent-1 Invalid: {match_stats['Agent-1']['invalid']}")
    print(f"Agent-2 Invalid: {match_stats['Agent-2']['invalid']}")


if __name__ == "__main__":
    main()
'''


# ============================================================
# Human play mode code (self-contained with own engine copy)
# ============================================================
HUMAN_GAME_CODE = '''
import random

class TwoByEightChess:
    """
    2x8 Mini Chess game engine.
    Board: 2 rows x 8 columns (row 0-1, col 0-7)
    Displayed as rows 1-2, columns a-h.
    Pieces: K/N/R/P (White), k/n/r/p (Black), '' (empty)
    """

    WHITE = 'W'
    BLACK = 'B'
    COLS = 'abcdefgh'

    def __init__(self):
        self.board = [
            ['R', 'N', 'P', '', '', 'p', 'n', 'r'],
            ['K', 'N', 'P', '', '', 'p', 'n', 'k'],
        ]
        self.current_turn = self.WHITE
        self.move_history = []
        self.position_history = []
        self._record_position()

    def _record_position(self):
        pos = (tuple(tuple(row) for row in self.board), self.current_turn)
        self.position_history.append(pos)

    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R', 'P')

    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r', 'p')

    def _is_own_piece(self, piece, color):
        if color == self.WHITE:
            return self._is_white_piece(piece)
        return self._is_black_piece(piece)

    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)

    def _get_piece_type(self, piece):
        return piece.upper() if piece else ''

    def _in_bounds(self, row, col):
        return 0 <= row < 2 and 0 <= col < 8

    def _pos_to_notation(self, row, col):
        return f"{self.COLS[col]}{row + 1}"

    def _notation_to_pos(self, notation):
        if len(notation) != 2:
            return None
        col_char = notation[0].lower()
        if col_char not in self.COLS:
            return None
        try:
            row = int(notation[1]) - 1
        except ValueError:
            return None
        col = self.COLS.index(col_char)
        if not self._in_bounds(row, col):
            return None
        return (row, col)

    def _find_king(self, color):
        target = 'K' if color == self.WHITE else 'k'
        for r in range(2):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

    def _get_valid_moves_for_piece(self, row, col, ignore_check=False):
        piece = self.board[row][col]
        if not piece:
            return []

        color = self.WHITE if self._is_white_piece(piece) else self.BLACK
        piece_type = self._get_piece_type(piece)
        moves = []

        if piece_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self._in_bounds(nr, nc):
                        target = self.board[nr][nc]
                        if not self._is_own_piece(target, color):
                            is_capture = self._is_enemy_piece(target, color)
                            moves.append(((nr, nc), is_capture))

        elif piece_type == 'N':
            l_deltas = [(-1, -2), (-1, 2), (1, -2), (1, 2),
                        (-2, -1), (-2, 1), (2, -1), (2, 1)]
            linear_deltas = [(0, -2), (0, 2)]
            for dr, dc in l_deltas + linear_deltas:
                nr, nc = row + dr, col + dc
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append(((nr, nc), is_capture))

        elif piece_type == 'R':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                while self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if target == '':
                        moves.append(((nr, nc), False))
                    elif self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif piece_type == 'P':
            direction = 1 if color == self.WHITE else -1
            nc = col + direction
            if self._in_bounds(row, nc) and self.board[row][nc] == '':
                moves.append(((row, nc), False))
            for dr in [-1, 1]:
                nr = row + dr
                nc = col + direction
                if self._in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if self._is_enemy_piece(target, color):
                        moves.append(((nr, nc), True))

        if ignore_check:
            return moves

        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe((row, col), to_pos, color):
                valid_moves.append((to_pos, is_capture))

        return valid_moves

    def _is_move_safe(self, from_pos, to_pos, color):
        fr, fc = from_pos
        tr, tc = to_pos
        original_from = self.board[fr][fc]
        original_to = self.board[tr][tc]

        moving_piece = original_from
        if moving_piece.upper() == 'P':
            if (color == self.WHITE and tc == 7) or (color == self.BLACK and tc == 0):
                moving_piece = 'R' if color == self.WHITE else 'r'
        self.board[tr][tc] = moving_piece
        self.board[fr][fc] = ''

        in_check = self._is_in_check(color)

        self.board[fr][fc] = original_from
        self.board[tr][tc] = original_to

        return not in_check

    def _is_in_check(self, color):
        king_pos = self._find_king(color)
        if king_pos is None:
            return True

        enemy_color = self.BLACK if color == self.WHITE else self.WHITE

        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, enemy_color):
                    enemy_moves = self._get_valid_moves_for_piece(r, c, ignore_check=True)
                    for to_pos, _ in enemy_moves:
                        if to_pos == king_pos:
                            return True
        return False

    def _has_legal_moves(self, color):
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    if self._get_valid_moves_for_piece(r, c):
                        return True
        return False

    def _is_insufficient_material(self):
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.upper() != 'K':
                    return False
        return True

    def _is_threefold_repetition(self):
        if len(self.position_history) < 3:
            return False
        current_pos = self.position_history[-1]
        count = sum(1 for pos in self.position_history if pos == current_pos)
        return count >= 3

    def get_all_valid_moves(self, color):
        moves = []
        for r in range(2):
            for c in range(8):
                piece = self.board[r][c]
                if piece and self._is_own_piece(piece, color):
                    piece_type = self._get_piece_type(piece)
                    from_sq = self._pos_to_notation(r, c)
                    for to_pos, is_capture in self._get_valid_moves_for_piece(r, c):
                        to_sq = self._pos_to_notation(to_pos[0], to_pos[1])
                        if is_capture:
                            move_str = f"{piece_type}{from_sq}x{to_sq}"
                        else:
                            move_str = f"{piece_type}{from_sq}{to_sq}"
                        moves.append(move_str)
        return moves

    def parse_move(self, move_str):
        if not isinstance(move_str, str):
            return None
        move_str = move_str.strip()
        if len(move_str) < 5:
            return None

        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R', 'P'):
            return None

        if 'x' in move_str.lower():
            idx = move_str.lower().index('x')
            from_notation = move_str[1:idx]
            to_notation = move_str[idx+1:]
            is_capture = True
        else:
            from_notation = move_str[1:3]
            to_notation = move_str[3:5]
            is_capture = False

        from_pos = self._notation_to_pos(from_notation)
        to_pos = self._notation_to_pos(to_notation)

        if from_pos is None or to_pos is None:
            return None

        return (piece, from_pos, to_pos, is_capture)

    def is_valid_move(self, move_str, color):
        parsed = self.parse_move(move_str)
        if not parsed:
            return False, "Invalid move notation"

        piece_type, from_pos, to_pos, is_capture = parsed
        fr, fc = from_pos

        piece = self.board[fr][fc]
        if not piece:
            return False, f"No piece at {self._pos_to_notation(fr, fc)}"

        if not self._is_own_piece(piece, color):
            return False, "Cannot move opponent's piece"

        if self._get_piece_type(piece) != piece_type:
            return False, f"Piece at {self._pos_to_notation(fr, fc)} is not a {piece_type}"

        valid_moves = self._get_valid_moves_for_piece(fr, fc)
        for valid_to, valid_capture in valid_moves:
            if valid_to == to_pos:
                if is_capture != valid_capture:
                    if is_capture:
                        return False, "No piece to capture at destination"
                    else:
                        return False, "Must use capture notation (x) when capturing"
                return True, ""

        if self._is_in_check(color):
            return False, "Must escape check"
        return False, "Invalid move for this piece"

    def make_move(self, move_str, color):
        valid, error = self.is_valid_move(move_str, color)
        if not valid:
            return False, error

        parsed = self.parse_move(move_str)
        _, from_pos, to_pos, _ = parsed
        fr, fc = from_pos
        tr, tc = to_pos

        self.board[tr][tc] = self.board[fr][fc]
        self.board[fr][fc] = ''

        piece = self.board[tr][tc]
        if piece.upper() == 'P':
            if (self._is_white_piece(piece) and tc == 7) or \\
               (self._is_black_piece(piece) and tc == 0):
                self.board[tr][tc] = 'R' if self._is_white_piece(piece) else 'r'

        self.move_history.append(move_str)
        self._record_position()

        self.current_turn = self.BLACK if self.current_turn == self.WHITE else self.WHITE

        return True, ""

    def get_game_state(self):
        if self._is_insufficient_material():
            return 'draw_material'

        if self._is_threefold_repetition():
            return 'draw_repetition'

        current = self.current_turn
        in_check = self._is_in_check(current)
        has_moves = self._has_legal_moves(current)

        if not has_moves:
            if in_check:
                return 'white_wins' if current == self.BLACK else 'black_wins'
            else:
                return 'draw_stalemate'

        return 'ongoing'

    def get_board_display(self):
        header = "    " + "  ".join(c for c in 'a b c d e f g h'.split())
        row1 = "1 | " + " | ".join(p if p else '.' for p in self.board[0]) + " |"
        row2 = "2 | " + " | ".join(p if p else '.' for p in self.board[1]) + " |"
        return f"{header}\\n{row1}\\n{row2}"


class HumanAgent:
    """Human player that inputs moves via terminal."""

    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        game = TwoByEightChess()
        game.board = [row[:] for row in board]
        game.current_turn = self.color

        while True:
            print()
            print("=" * 40)
            print(f"{self.name}'s turn ({'White' if self.color == 'W' else 'Black'})")
            print("=" * 40)
            print()
            print("Board (columns a-h, rows 1-2):")
            print("    " + "  ".join(c for c in 'a b c d e f g h'.split()))
            print("1 | " + " | ".join(p if p else '.' for p in board[0]) + " |")
            print("2 | " + " | ".join(p if p else '.' for p in board[1]) + " |")
            print()
            print("Pieces: K=King, N=Knight, R=Rook, P=Pawn")
            print("        Uppercase=White, lowercase=Black")
            print()

            if game._is_in_check(self.color):
                print("*** YOU ARE IN CHECK! ***")
                print()

            valid_moves = game.get_all_valid_moves(self.color)
            print(f"Valid moves: {', '.join(valid_moves)}")
            print()
            print("Move format: [Piece][FromSquare][ToSquare] or [Piece][FromSquare]x[ToSquare]")
            print("Examples: Nb2d1 (Knight from b2 to d1), Ra1xa5 (Rook from a1 captures on a5)")
            print()

            move = input("Enter your move: ").strip()

            if not move:
                print("Please enter a move.")
                continue

            valid, error = game.is_valid_move(move, self.color)
            if valid:
                return move
            else:
                print(f"Invalid move: {error}")
                print("Try again.")


class RandomAgent:
    """Bot that plays random valid moves."""

    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, board, move_history):
        game = TwoByEightChess()
        game.board = [row[:] for row in board]
        game.current_turn = self.color

        valid_moves = game.get_all_valid_moves(self.color)
        if not valid_moves:
            return None
        return random.choice(valid_moves)


def print_board(board):
    print("    " + "  ".join(c for c in 'a b c d e f g h'.split()))
    print("1 | " + " | ".join(p if p else '.' for p in board[0]) + " |")
    print("2 | " + " | ".join(p if p else '.' for p in board[1]) + " |")


if __name__ == "__main__":
    print("=" * 50)
    print("2x8 MINI CHESS - Human vs Random Bot")
    print("=" * 50)
    print()
    print("Starting position:")
    print("White: Rook(a1), Knight(b1), Pawn(c1), King(a2), Knight(b2), Pawn(c2)")
    print("Black: pawn(f1), knight(g1), rook(h1), pawn(f2), knight(g2), king(h2)")
    print()

    game = TwoByEightChess()

    if random.random() < 0.5:
        human = HumanAgent("Human", game.WHITE)
        bot = RandomAgent("Bot", game.BLACK)
        print("You are White (move first).")
    else:
        human = HumanAgent("Human", game.BLACK)
        bot = RandomAgent("Bot", game.WHITE)
        print("You are Black (move second).")

    agents = {game.WHITE: human if human.color == game.WHITE else bot,
              game.BLACK: human if human.color == game.BLACK else bot}
    names = {game.WHITE: agents[game.WHITE].name, game.BLACK: agents[game.BLACK].name}

    move_count = 0
    MAX_MOVES = 200

    while move_count < MAX_MOVES:
        current_color = game.current_turn
        current_agent = agents[current_color]
        current_name = names[current_color]
        opponent_name = names[game.BLACK if current_color == game.WHITE else game.WHITE]

        try:
            move = current_agent.make_move([row[:] for row in game.board], game.move_history[:])
        except Exception as e:
            print(f"{current_name} crashed: {e}")
            print(f"{opponent_name} wins!")
            break

        if move is None:
            print(f"{current_name} has no valid moves!")
            break

        success, error = game.make_move(move, current_color)
        if not success:
            print(f"{current_name} made invalid move \\'{move}\\': {error}")
            print(f"{opponent_name} wins!")
            break

        print(f"{current_name} plays: {move}")
        move_count += 1

        state = game.get_game_state()
        if state != 'ongoing':
            print()
            print("Final Board:")
            print_board(game.board)
            print()

            if state == 'white_wins':
                print("CHECKMATE! White wins!")
            elif state == 'black_wins':
                print("CHECKMATE! Black wins!")
            elif state == 'draw_stalemate':
                print("DRAW by stalemate!")
            elif state == 'draw_repetition':
                print("DRAW by threefold repetition!")
            elif state == 'draw_material':
                print("DRAW by insufficient material!")
            break
    else:
        print()
        print("Final Board:")
        print_board(game.board)
        print(f"DRAW by move limit ({MAX_MOVES} moves)")

    print()
    print("Thanks for playing!")
'''


# ============================================================
# Outer layer: agent loading, match orchestration, logging
# ============================================================

def load_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "games" / "A7-TwoByEightChess.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()


def find_model_folder(pattern: str) -> str | None:
    """Find a model folder matching the given pattern."""
    if not AGENTS_DIR.exists():
        logger.error("Agents directory not found: %s", AGENTS_DIR)
        return None

    exact = AGENTS_DIR / pattern
    if exact.is_dir():
        return pattern

    matches = [
        d.name for d in AGENTS_DIR.iterdir()
        if d.is_dir() and pattern.lower() in d.name.lower()
    ]

    if not matches:
        logger.error("No model folder matches pattern '%s'", pattern)
        return None

    if len(matches) > 1:
        return ModelAPI.resolve_model_interactive(pattern, matches, context="folder")

    return matches[0]


def get_available_runs(model_folder: str, game: str) -> list[int]:
    """Get list of available run IDs for a model and game."""
    model_dir = AGENTS_DIR / model_folder
    runs = []
    pattern = re.compile(rf"^{re.escape(game)}_(\d+)\.py$")

    for file in model_dir.glob(f"{game}_*.py"):
        match = pattern.match(file.name)
        if match:
            runs.append(int(match.group(1)))

    return sorted(runs)


def load_stored_agent(model_folder: str, game: str, run: int, agent_idx: int) -> tuple[str, str]:
    """Load agent code from a stored file and rename the class."""
    agent_file = AGENTS_DIR / model_folder / f"{game}_{run}.py"

    if not agent_file.exists():
        logger.error("Agent file not found: %s", agent_file)
        return "", ""

    content = agent_file.read_text()
    lines = content.split("\n")

    # Skip the header docstring
    code_start = 0
    in_docstring = False
    for i, line in enumerate(lines):
        if '"""' in line:
            if in_docstring:
                code_start = i + 1
                break
            else:
                in_docstring = True

    code_lines = lines[code_start:]

    # Extract imports
    imports = []
    for line in code_lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:
                imports.append(stripped)

    code = "\n".join(code_lines)
    code = re.sub(r"class\s+TwoByEightChessAgent\b", f"class TwoByEightChessAgent_{agent_idx}", code)

    return code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    """Parse agent spec (model:run1:run2) into model pattern and list of runs."""
    parts = spec.split(":")
    model_pattern = parts[0]
    runs = [int(r) for r in parts[1:]]
    return model_pattern, runs


def build_game_code(
    agent1_code: str,
    agent2_code: str,
    extra_imports: str,
    num_games: int,
    move_timeout: float,
    max_moves: int,
    agent1_info: str,
    agent2_info: str,
) -> str:
    """Concatenate header, imports, agent code, engine, and runner into executable script."""
    header = (
        "import sys\n"
        "import random\n"
        "import signal\n"
        "\n"
        f"MOVE_TIMEOUT = {move_timeout}\n"
        f"MAX_MOVES = {max_moves}\n"
        f"NUM_GAMES = {num_games}\n"
        f'AGENT1_INFO = "{agent1_info}"\n'
        f'AGENT2_INFO = "{agent2_info}"\n'
    )

    return "\n\n".join([
        header,
        extra_imports,
        agent1_code,
        agent2_code,
        GAME_ENGINE_CODE,
        MATCH_RUNNER_CODE,
    ])


def run_match(
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = 600
) -> dict:
    """Spawn subprocess, parse structured output, filter log lines."""
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"twobyeightchess_match_{match_id}_{temp_id}.py"
    )

    try:
        with open(temp_file, "w") as f:
            f.write(game_code)

        result = subprocess.run(
            ["python", temp_file], capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            return {
                "match_id": match_id,
                "agent1_run_id": run_ids[0],
                "agent2_run_id": run_ids[1],
                "success": False,
                "agent1_score": 0,
                "agent2_score": 0,
                "error": result.stderr[:500],
            }

        match = re.search(
            r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout
        )

        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            wins_match = re.search(
                r"WINS:Agent-1=(\d+),Agent-2=(\d+)", result.stdout
            )
            draws_match = re.search(r"DRAWS:(\d+)", result.stdout)
            score_match = re.search(
                r"SCORE:Agent-1=(-?[\d.]+),Agent-2=(-?[\d.]+)", result.stdout
            )

            agent1_wins = int(wins_match.group(1)) if wins_match else 0
            agent2_wins = int(wins_match.group(2)) if wins_match else 0
            draws = int(draws_match.group(1)) if draws_match else 0
            agent1_points = int(float(match.group(1)))
            agent2_points = int(float(match.group(2)))
            agent1_score = float(score_match.group(1)) if score_match else 0.0
            agent2_score = float(score_match.group(2)) if score_match else 0.0

            # Log filtering: keep only structurally meaningful lines
            log_lines = []
            for line in result.stdout.splitlines():
                if line.startswith((
                    "Agent-1:", "Agent-2:", "Game ",
                    "=====", "----",
                    "Final", "Moves:", "Scores:", "Points:",
                    "BOARD:",
                    "CRASH", "RESULT", "SCORE", "WINS", "DRAWS",
                    "STATS",
                )) or line.strip() == "":
                    log_lines.append(line)

            return {
                "match_id": match_id,
                "agent1_run_id": run_ids[0],
                "agent2_run_id": run_ids[1],
                "success": True,
                "agent1_score": agent1_score,
                "agent2_score": agent2_score,
                "agent1_wins": agent1_wins,
                "agent2_wins": agent2_wins,
                "agent1_points": agent1_points,
                "agent2_points": agent2_points,
                "draws": draws,
                "error": None,
                "stats_block": stats_block,
                "log": "\n".join(log_lines),
            }

        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": False,
            "agent1_score": 0,
            "agent2_score": 0,
            "error": "Could not parse results:\n" + result.stdout[:200],
        }

    except Exception as e:
        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": False,
            "agent1_score": 0,
            "agent2_score": 0,
            "error": str(e),
        }
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def run_match_async(
    game_code: str, match_id: int, run_ids: tuple[int, int]
) -> dict:
    """Wrap run_match in executor for async scheduling."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    parser = argparse.ArgumentParser(description="Run 2x8 Mini Chess matches between stored AI agents")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4]")
    parser.add_argument("--human", action="store_true", help="Play interactively against a random bot")
    args = parser.parse_args()

    # Human play mode
    if args.human:
        temp_file = os.path.join(tempfile.gettempdir(), f"chess1d_human_{uuid.uuid4().hex[:8]}.py")
        try:
            with open(temp_file, "w") as f:
                f.write(HUMAN_GAME_CODE)
            subprocess.run(["python", temp_file], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return

    if not args.agent or len(args.agent) != 2:
        print("ERROR: Need exactly 2 agent specifications.")
        print("Example: --agent mistral:1:2 gpt-5-mini:1:4")
        sys.exit(1)

    # Parse and load agents
    model1_pattern, runs1 = parse_agent_spec(args.agent[0])
    model2_pattern, runs2 = parse_agent_spec(args.agent[1])

    folder1 = find_model_folder(model1_pattern)
    folder2 = find_model_folder(model2_pattern)

    if not folder1 or not folder2:
        sys.exit(1)

    if not runs1:
        runs1 = get_available_runs(folder1, GAME_NAME)
    if not runs2:
        runs2 = get_available_runs(folder2, GAME_NAME)

    num_matches = min(len(runs1), len(runs2))
    if len(runs1) != len(runs2):
        logger.warning(
            "Run count mismatch: %s (%d) vs %s (%d). Using first %d.",
            folder1, len(runs1), folder2, len(runs2), num_matches,
        )

    runs1 = runs1[:num_matches]
    runs2 = runs2[:num_matches]

    print("\n" + "=" * 60)
    print("2x8 MINI CHESS MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    match_tasks = []

    for i in range(num_matches):
        run1 = runs1[i]
        run2 = runs2[i]

        code1, imp1 = load_stored_agent(folder1, GAME_NAME, run1, 1)
        code2, imp2 = load_stored_agent(folder2, GAME_NAME, run2, 2)

        if not code1 or not code2:
            print(f"  FAILED to load match {i + 1}")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        agent1_info = f"{folder1}:{run1}"
        agent2_info = f"{folder2}:{run2}"

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_GAMES_PER_MATCH,
            MOVE_TIME_LIMIT, MAX_MOVES_PER_GAME, agent1_info, agent2_info,
        )

        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    for result in sorted(results, key=lambda x: x["match_id"]):
        match_id = result["match_id"]
        run1 = runs1[match_id - 1]
        run2 = runs2[match_id - 1]

        log_f = RESULTS_DIR / f"{ts}_{folder1}:{run1}_vs_{folder2}:{run2}_match.txt"

        if result["success"]:
            s1 = result["agent1_score"]
            s2 = result["agent2_score"]
            p1 = result.get("agent1_points", 0)
            p2 = result.get("agent2_points", 0)

            with open(log_f, "w") as f:
                f.write("Match Contenders:\n")
                f.write(f"{folder1}:{run1}\n")
                f.write(f"{folder2}:{run2}\n\n")

                f.write("Result:\n")
                f.write(f"{folder1}:{run1} : Pts: {p1} - Score: {s1:.1f}\n")
                f.write(f"{folder2}:{run2} : Pts: {p2} - Score: {s2:.1f}\n")

                game_log = result.get("log", "")
                if game_log:
                    f.write(f"\n{game_log}\n")
                if result.get("stats_block"):
                    f.write(
                        f"--- MATCH STATISTICS ---\n{result['stats_block']}\n"
                    )
                f.write("-" * 60 + "\n")

            print(f"  Match {match_id} ({folder1}:{run1} vs {folder2}:{run2}): Pts {p1}-{p2}")

            # Update scoreboard for both agents
            agent1_key = f"{folder1}:{run1}"
            agent2_key = f"{folder2}:{run2}"
            a1_wins = result.get("agent1_wins", 0)
            a2_wins = result.get("agent2_wins", 0)
            match_draws = result.get("draws", 0)

            update_scoreboard(
                SCOREBOARD_PATH, agent1_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=a1_wins,
                losses=a2_wins,
                draws=match_draws,
                score=s1,
                points=p1,
            )
            update_scoreboard(
                SCOREBOARD_PATH, agent2_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=a2_wins,
                losses=a1_wins,
                draws=match_draws,
                score=s2,
                points=p2,
            )
        else:
            print(f"  Match {match_id} ({folder1}:{run1} vs {folder2}:{run2}): FAILED - {result.get('error')}")

    print(f"\nLogs saved to: {RESULTS_DIR}")
    print(f"Scoreboard updated: {SCOREBOARD_PATH}")


if __name__ == "__main__":
    asyncio.run(main_async())
