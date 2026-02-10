"""
1D Chess Match Runner: Orchestrates head-to-head matches between two AI models.

Prompts two models to implement OneDChessAgent, extracts their code, renames
them to OneDChessAgent_1 and OneDChessAgent_2, runs games, and reports
win/loss statistics.
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

logger = setup_logging(__name__)

# Load environment variables
load_dotenv()

# Configuration
try:
    NUM_ROUNDS_PER_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    NUM_ROUNDS_PER_MATCH = 100

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

# Maximum moves per game to prevent infinite games
MAX_MOVES_PER_GAME = 200

# Results directories
RESULTS_DIR = Path(__file__).parent.parent / "results" / "oned_chess"
GAME_LOGS_DIR = RESULTS_DIR / "game_logs"
MODEL_RESPONSES_DIR = RESULTS_DIR / "model_responses"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A7-1D_Chess"

# The game code template with placeholders for agent implementations
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal

# Move timeout in seconds
MOVE_TIMEOUT = {move_timeout}

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

# --- 1D Chess Game Engine ---

class OneDChessGame:
    """
    1D Chess game engine.
    Board: 8 squares (index 0-7, displayed as 1-8 to players)
    Pieces: K/N/R (White), k/n/r (Black), '' (empty)
    """
    
    WHITE = 'W'
    BLACK = 'B'
    
    def __init__(self):
        # Board index 0-7 maps to squares 1-8
        # Starting position: White K(0), N(1), R(2), Black r(5), n(6), k(7)
        self.board = ['K', 'N', 'R', '', '', 'r', 'n', 'k']
        self.current_turn = self.WHITE
        self.move_history = []
        self.position_history = []  # For threefold repetition
        self._record_position()
    
    def _record_position(self):
        """Record current position for repetition detection."""
        pos = (tuple(self.board), self.current_turn)
        self.position_history.append(pos)
    
    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R')
    
    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r')
    
    def _is_own_piece(self, piece, color):
        if color == self.WHITE:
            return self._is_white_piece(piece)
        return self._is_black_piece(piece)
    
    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)
    
    def _get_piece_type(self, piece):
        """Return piece type in uppercase."""
        return piece.upper() if piece else ''
    
    def _find_king(self, color):
        """Find the position of the King for the given color."""
        target = 'K' if color == self.WHITE else 'k'
        for i, piece in enumerate(self.board):
            if piece == target:
                return i
        return -1  # King not found (should not happen in valid game)
    
    def _get_valid_moves_for_piece(self, pos, ignore_check=False):
        """
        Get all valid destination squares for the piece at pos.
        Returns list of (to_pos, is_capture) tuples.
        """
        piece = self.board[pos]
        if not piece:
            return []
        
        color = self.WHITE if self._is_white_piece(piece) else self.BLACK
        piece_type = self._get_piece_type(piece)
        moves = []
        
        if piece_type == 'K':
            # King: move 1 square left or right
            for delta in [-1, 1]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = self.board[to_pos]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'N':
            # Knight: move exactly 2 squares, can jump
            for delta in [-2, 2]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = self.board[to_pos]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'R':
            # Rook: move any distance, blocked by pieces
            for direction in [-1, 1]:
                to_pos = pos + direction
                while 0 <= to_pos < 8:
                    target = self.board[to_pos]
                    if target == '':
                        moves.append((to_pos, False))
                    elif self._is_enemy_piece(target, color):
                        moves.append((to_pos, True))
                        break  # Can capture but not go further
                    else:
                        break  # Blocked by own piece
                    to_pos += direction
        
        if ignore_check:
            return moves
        
        # Filter moves that would leave own King in check
        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe(pos, to_pos, color):
                valid_moves.append((to_pos, is_capture))
        
        return valid_moves
    
    def _is_move_safe(self, from_pos, to_pos, color):
        """Check if making this move would leave the King in check."""
        # Simulate the move
        original_from = self.board[from_pos]
        original_to = self.board[to_pos]
        
        self.board[to_pos] = self.board[from_pos]
        self.board[from_pos] = ''
        
        # Check if King is in check after move
        in_check = self._is_in_check(color)
        
        # Undo the move
        self.board[from_pos] = original_from
        self.board[to_pos] = original_to
        
        return not in_check
    
    def _is_in_check(self, color):
        """Check if the given color's King is under attack."""
        king_pos = self._find_king(color)
        if king_pos == -1:
            return True  # King captured (shouldn't happen in normal play)
        
        enemy_color = self.BLACK if color == self.WHITE else self.WHITE
        
        # Check all enemy pieces for attacks on the King
        for pos in range(8):
            piece = self.board[pos]
            if piece and self._is_own_piece(piece, enemy_color):
                # Get moves ignoring check (to avoid infinite recursion)
                enemy_moves = self._get_valid_moves_for_piece(pos, ignore_check=True)
                for to_pos, _ in enemy_moves:
                    if to_pos == king_pos:
                        return True
        return False
    
    def _has_legal_moves(self, color):
        """Check if the given color has any legal moves."""
        for pos in range(8):
            piece = self.board[pos]
            if piece and self._is_own_piece(piece, color):
                if self._get_valid_moves_for_piece(pos):
                    return True
        return False
    
    def _is_insufficient_material(self):
        """Check if only Kings remain (draw by insufficient material)."""
        for piece in self.board:
            if piece and piece.upper() != 'K':
                return False
        return True
    
    def _is_threefold_repetition(self):
        """Check for threefold repetition."""
        if len(self.position_history) < 3:
            return False
        current_pos = self.position_history[-1]
        count = sum(1 for pos in self.position_history if pos == current_pos)
        return count >= 3
    
    def parse_move(self, move_str):
        """
        Parse move notation into (piece_type, from_pos, to_pos, is_capture).
        Returns None if invalid format.
        
        Format: [Piece][From][x?][To]
        Examples: "N24", "R3x6", "K12"
        """
        if not isinstance(move_str, str):
            return None
        move_str = move_str.strip()
        if len(move_str) < 3:
            return None
        
        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R'):
            return None
        
        # Check for capture notation
        if 'x' in move_str.lower():
            parts = move_str[1:].lower().split('x')
            if len(parts) != 2:
                return None
            try:
                from_sq = int(parts[0])
                to_sq = int(parts[1])
                is_capture = True
            except ValueError:
                return None
        else:
            # Regular move: piece + from + to (e.g., "N24")
            if len(move_str) != 3:
                return None
            try:
                from_sq = int(move_str[1])
                to_sq = int(move_str[2])
                is_capture = False
            except ValueError:
                return None
        
        # Convert 1-8 notation to 0-7 index
        from_pos = from_sq - 1
        to_pos = to_sq - 1
        
        if not (0 <= from_pos < 8 and 0 <= to_pos < 8):
            return None
        
        return (piece, from_pos, to_pos, is_capture)
    
    def is_valid_move(self, move_str, color):
        """Validate a move for the given color."""
        parsed = self.parse_move(move_str)
        if not parsed:
            return False, "Invalid move notation"
        
        piece_type, from_pos, to_pos, is_capture = parsed
        
        # Check piece at from_pos
        piece = self.board[from_pos]
        if not piece:
            return False, f"No piece at square {{from_pos + 1}}"
        
        if not self._is_own_piece(piece, color):
            return False, "Cannot move opponent's piece"
        
        if self._get_piece_type(piece) != piece_type:
            return False, f"Piece at square {{from_pos + 1}} is not a {{piece_type}}"
        
        # Check if move is in valid moves
        valid_moves = self._get_valid_moves_for_piece(from_pos)
        for valid_to, valid_capture in valid_moves:
            if valid_to == to_pos:
                # Verify capture notation matches
                if is_capture != valid_capture:
                    if is_capture:
                        return False, "No piece to capture at destination"
                    else:
                        return False, "Must use capture notation (x) when capturing"
                return True, ""
        
        # Move not found in valid moves
        if self._is_in_check(color):
            return False, "Must escape check"
        return False, "Invalid move for this piece"
    
    def make_move(self, move_str, color):
        """
        Execute a move. Returns (success, message).
        """
        valid, error = self.is_valid_move(move_str, color)
        if not valid:
            return False, error
        
        parsed = self.parse_move(move_str)
        _, from_pos, to_pos, _ = parsed
        
        # Execute move
        self.board[to_pos] = self.board[from_pos]
        self.board[from_pos] = ''
        
        # Record move and position
        self.move_history.append(move_str)
        self._record_position()
        
        # Switch turn
        self.current_turn = self.BLACK if self.current_turn == self.WHITE else self.WHITE
        
        return True, ""
    
    def get_game_state(self):
        """
        Check the current game state.
        Returns: 'ongoing', 'white_wins', 'black_wins', 'draw_stalemate',
                 'draw_repetition', 'draw_material'
        """
        # Check for insufficient material
        if self._is_insufficient_material():
            return 'draw_material'
        
        # Check for threefold repetition
        if self._is_threefold_repetition():
            return 'draw_repetition'
        
        current = self.current_turn
        in_check = self._is_in_check(current)
        has_moves = self._has_legal_moves(current)
        
        if not has_moves:
            if in_check:
                # Checkmate
                return 'white_wins' if current == self.BLACK else 'black_wins'
            else:
                # Stalemate
                return 'draw_stalemate'
        
        return 'ongoing'
    
    def get_board_display(self):
        """Return a string representation of the board."""
        squares = "| " + " | ".join(str(i+1) for i in range(8)) + " |"
        pieces = "| " + " | ".join(p if p else '.' for p in self.board) + " |"
        return f"{{squares}}\\n{{pieces}}"

# ---------------------------------------------------------

{{extra_imports}}

{{agent1_code}}

{{agent2_code}}

# --- Stats ---
stats = {{{{
    "normal": 0,
    "draw": 0,
    "c1": 0,
    "c2": 0,
    "r1_timeout": 0,
    "r1_crash": 0,
    "r1_invalid": 0,
    "r2_timeout": 0,
    "r2_crash": 0,
    "r2_invalid": 0,
}}}}

MAX_MOVES = {max_moves}

def print_board(board):
    squares = "| " + " | ".join(str(i+1) for i in range(8)) + " |"
    pieces = "| " + " | ".join(p if p else '.' for p in board) + " |"
    print(squares)
    print(pieces)

def play_game(game_num):
    """Plays a single game and returns the winner's name or DRAW."""
    game = OneDChessGame()
    
    # Randomize starting agent
    if random.random() < 0.5:
        white_agent_class = OneDChessAgent_1
        black_agent_class = OneDChessAgent_2
        white_name = "Agent-1"
        black_name = "Agent-2"
    else:
        white_agent_class = OneDChessAgent_2
        black_agent_class = OneDChessAgent_1
        white_name = "Agent-2"
        black_name = "Agent-1"

    print(f"--- GAME {{game_num}} ---")
    print(f"Colors: {{white_name}} is White, {{black_name}} is Black")
    
    try:
        agent_white = white_agent_class(white_name, game.WHITE)
    except Exception as e:
        stats["c1" if white_name == "Agent-1" else "c2"] += 1
        print(f"{{white_name}} crashed during init: {{e}}")
        return black_name
    
    try:
        agent_black = black_agent_class(black_name, game.BLACK)
    except Exception as e:
        stats["c1" if black_name == "Agent-1" else "c2"] += 1
        print(f"{{black_name}} crashed during init: {{e}}")
        return white_name

    agents = {{game.WHITE: agent_white, game.BLACK: agent_black}}
    names = {{game.WHITE: white_name, game.BLACK: black_name}}
    
    move_count = 0

    while move_count < MAX_MOVES:
        current_color = game.current_turn
        current_agent = agents[current_color]
        current_name = names[current_color]
        opponent_name = names[game.BLACK if current_color == game.WHITE else game.WHITE]
        
        move = None
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(MOVE_TIMEOUT))
            try:
                move = current_agent.make_move(game.board[:], game.move_history[:])
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            if current_name == "Agent-1":
                stats["r1_timeout"] += 1
            else:
                stats["r2_timeout"] += 1
            print(f"{{current_name}} TIMEOUT - forfeit")
            return opponent_name
        except Exception as e:
            if current_name == "Agent-1":
                stats["r1_crash"] += 1
            else:
                stats["r2_crash"] += 1
            print(f"{{current_name}} CRASH: {{e}} - forfeit")
            return opponent_name

        # Validate and execute move
        success, error = game.make_move(move, current_color)
        if not success:
            if current_name == "Agent-1":
                stats["r1_invalid"] += 1
            else:
                stats["r2_invalid"] += 1
            print(f"{{current_name}} INVALID MOVE '{{move}}': {{error}} - forfeit")
            return opponent_name
        
        print(f"{{current_name}}: {{move}}")
        move_count += 1
        
        # Check game state
        state = game.get_game_state()
        if state != 'ongoing':
            print("Final Board:")
            print_board(game.board)
            
            if state == 'white_wins':
                print(f"Result: {{white_name}} wins by checkmate!")
                stats["normal"] += 1
                return white_name
            elif state == 'black_wins':
                print(f"Result: {{black_name}} wins by checkmate!")
                stats["normal"] += 1
                return black_name
            else:
                # Draw
                draw_reason = {{
                    'draw_stalemate': 'stalemate',
                    'draw_repetition': 'threefold repetition',
                    'draw_material': 'insufficient material'
                }}.get(state, 'unknown')
                print(f"Result: DRAW by {{draw_reason}}")
                stats["draw"] += 1
                return "DRAW"
    
    # Max moves reached - draw
    print("Final Board:")
    print_board(game.board)
    print(f"Result: DRAW by move limit ({{MAX_MOVES}} moves)")
    stats["draw"] += 1
    return "DRAW"

def main():
    scores = {{"Agent-1": 0, "Agent-2": 0}}
    num_games = {num_games}

    for i in range(num_games):
        result = play_game(i + 1)
        if result == "DRAW":
            scores["Agent-1"] += 0.5
            scores["Agent-2"] += 0.5
        elif result in scores:
            scores[result] += 1
        
        sys.stdout.flush()

    print(f"RESULT:Agent-1={{scores['Agent-1']}},Agent-2={{scores['Agent-2']}}")
    print(f"STATS:Normal={{stats['normal']}},Draw={{stats['draw']}},C1={{stats['c1']}},C2={{stats['c2']}},R1T={{stats['r1_timeout']}},R1C={{stats['r1_crash']}},R1I={{stats['r1_invalid']}},R2T={{stats['r2_timeout']}},R2C={{stats['r2_crash']}},R2I={{stats['r2_invalid']}}")

if __name__ == "__main__":
    main()
'''

# --- Human play mode ---
HUMAN_GAME_CODE = '''
import random

class OneDChessGame:
    """
    1D Chess game engine.
    Board: 8 squares (index 0-7, displayed as 1-8 to players)
    Pieces: K/N/R (White), k/n/r (Black), '' (empty)
    """
    
    WHITE = 'W'
    BLACK = 'B'
    
    def __init__(self):
        # Board index 0-7 maps to squares 1-8
        # Starting position: White K(0), N(1), R(2), Black r(5), n(6), k(7)
        self.board = ['K', 'N', 'R', '', '', 'r', 'n', 'k']
        self.current_turn = self.WHITE
        self.move_history = []
        self.position_history = []  # For threefold repetition
        self._record_position()
    
    def _record_position(self):
        """Record current position for repetition detection."""
        pos = (tuple(self.board), self.current_turn)
        self.position_history.append(pos)
    
    def _is_white_piece(self, piece):
        return piece in ('K', 'N', 'R')
    
    def _is_black_piece(self, piece):
        return piece in ('k', 'n', 'r')
    
    def _is_own_piece(self, piece, color):
        if color == self.WHITE:
            return self._is_white_piece(piece)
        return self._is_black_piece(piece)
    
    def _is_enemy_piece(self, piece, color):
        if piece == '':
            return False
        return not self._is_own_piece(piece, color)
    
    def _get_piece_type(self, piece):
        """Return piece type in uppercase."""
        return piece.upper() if piece else ''
    
    def _find_king(self, color):
        """Find the position of the King for the given color."""
        target = 'K' if color == self.WHITE else 'k'
        for i, piece in enumerate(self.board):
            if piece == target:
                return i
        return -1  # King not found (should not happen in valid game)
    
    def _get_valid_moves_for_piece(self, pos, ignore_check=False):
        """
        Get all valid destination squares for the piece at pos.
        Returns list of (to_pos, is_capture) tuples.
        """
        piece = self.board[pos]
        if not piece:
            return []
        
        color = self.WHITE if self._is_white_piece(piece) else self.BLACK
        piece_type = self._get_piece_type(piece)
        moves = []
        
        if piece_type == 'K':
            # King: move 1 square left or right
            for delta in [-1, 1]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = self.board[to_pos]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'N':
            # Knight: move exactly 2 squares, can jump
            for delta in [-2, 2]:
                to_pos = pos + delta
                if 0 <= to_pos < 8:
                    target = self.board[to_pos]
                    if not self._is_own_piece(target, color):
                        is_capture = self._is_enemy_piece(target, color)
                        moves.append((to_pos, is_capture))
        
        elif piece_type == 'R':
            # Rook: move any distance, blocked by pieces
            for direction in [-1, 1]:
                to_pos = pos + direction
                while 0 <= to_pos < 8:
                    target = self.board[to_pos]
                    if target == '':
                        moves.append((to_pos, False))
                    elif self._is_enemy_piece(target, color):
                        moves.append((to_pos, True))
                        break  # Can capture but not go further
                    else:
                        break  # Blocked by own piece
                    to_pos += direction
        
        if ignore_check:
            return moves
        
        # Filter moves that would leave own King in check
        valid_moves = []
        for to_pos, is_capture in moves:
            if self._is_move_safe(pos, to_pos, color):
                valid_moves.append((to_pos, is_capture))
        
        return valid_moves
    
    def _is_move_safe(self, from_pos, to_pos, color):
        """Check if making this move would leave the King in check."""
        # Simulate the move
        original_from = self.board[from_pos]
        original_to = self.board[to_pos]
        
        self.board[to_pos] = self.board[from_pos]
        self.board[from_pos] = ''
        
        # Check if King is in check after move
        in_check = self._is_in_check(color)
        
        # Undo the move
        self.board[from_pos] = original_from
        self.board[to_pos] = original_to
        
        return not in_check
    
    def _is_in_check(self, color):
        """Check if the given color's King is under attack."""
        king_pos = self._find_king(color)
        if king_pos == -1:
            return True  # King captured (shouldn't happen in normal play)
        
        enemy_color = self.BLACK if color == self.WHITE else self.WHITE
        
        # Check all enemy pieces for attacks on the King
        for pos in range(8):
            piece = self.board[pos]
            if piece and self._is_own_piece(piece, enemy_color):
                # Get moves ignoring check (to avoid infinite recursion)
                enemy_moves = self._get_valid_moves_for_piece(pos, ignore_check=True)
                for to_pos, _ in enemy_moves:
                    if to_pos == king_pos:
                        return True
        return False
    
    def _has_legal_moves(self, color):
        """Check if the given color has any legal moves."""
        for pos in range(8):
            piece = self.board[pos]
            if piece and self._is_own_piece(piece, color):
                if self._get_valid_moves_for_piece(pos):
                    return True
        return False
    
    def _is_insufficient_material(self):
        """Check if only Kings remain (draw by insufficient material)."""
        for piece in self.board:
            if piece and piece.upper() != 'K':
                return False
        return True
    
    def _is_threefold_repetition(self):
        """Check for threefold repetition."""
        if len(self.position_history) < 3:
            return False
        current_pos = self.position_history[-1]
        count = sum(1 for pos in self.position_history if pos == current_pos)
        return count >= 3
    
    def get_all_valid_moves(self, color):
        """Get all valid moves for a color. Returns list of move strings."""
        moves = []
        for pos in range(8):
            piece = self.board[pos]
            if piece and self._is_own_piece(piece, color):
                piece_type = self._get_piece_type(piece)
                for to_pos, is_capture in self._get_valid_moves_for_piece(pos):
                    from_sq = pos + 1
                    to_sq = to_pos + 1
                    if is_capture:
                        move_str = f"{piece_type}{from_sq}x{to_sq}"
                    else:
                        move_str = f"{piece_type}{from_sq}{to_sq}"
                    moves.append(move_str)
        return moves
    
    def parse_move(self, move_str):
        """
        Parse move notation into (piece_type, from_pos, to_pos, is_capture).
        Returns None if invalid format.
        
        Format: [Piece][From][x?][To]
        Examples: "N24", "R3x6", "K12"
        """
        if not isinstance(move_str, str):
            return None
        move_str = move_str.strip()
        if len(move_str) < 3:
            return None
        
        piece = move_str[0].upper()
        if piece not in ('K', 'N', 'R'):
            return None
        
        # Check for capture notation
        if 'x' in move_str.lower():
            parts = move_str[1:].lower().split('x')
            if len(parts) != 2:
                return None
            try:
                from_sq = int(parts[0])
                to_sq = int(parts[1])
                is_capture = True
            except ValueError:
                return None
        else:
            # Regular move: piece + from + to (e.g., "N24")
            if len(move_str) != 3:
                return None
            try:
                from_sq = int(move_str[1])
                to_sq = int(move_str[2])
                is_capture = False
            except ValueError:
                return None
        
        # Convert 1-8 notation to 0-7 index
        from_pos = from_sq - 1
        to_pos = to_sq - 1
        
        if not (0 <= from_pos < 8 and 0 <= to_pos < 8):
            return None
        
        return (piece, from_pos, to_pos, is_capture)
    
    def is_valid_move(self, move_str, color):
        """Validate a move for the given color."""
        parsed = self.parse_move(move_str)
        if not parsed:
            return False, "Invalid move notation"
        
        piece_type, from_pos, to_pos, is_capture = parsed
        
        # Check piece at from_pos
        piece = self.board[from_pos]
        if not piece:
            return False, f"No piece at square {from_pos + 1}"
        
        if not self._is_own_piece(piece, color):
            return False, "Cannot move opponent's piece"
        
        if self._get_piece_type(piece) != piece_type:
            return False, f"Piece at square {from_pos + 1} is not a {piece_type}"
        
        # Check if move is in valid moves
        valid_moves = self._get_valid_moves_for_piece(from_pos)
        for valid_to, valid_capture in valid_moves:
            if valid_to == to_pos:
                # Verify capture notation matches
                if is_capture != valid_capture:
                    if is_capture:
                        return False, "No piece to capture at destination"
                    else:
                        return False, "Must use capture notation (x) when capturing"
                return True, ""
        
        # Move not found in valid moves
        if self._is_in_check(color):
            return False, "Must escape check"
        return False, "Invalid move for this piece"
    
    def make_move(self, move_str, color):
        """
        Execute a move. Returns (success, message).
        """
        valid, error = self.is_valid_move(move_str, color)
        if not valid:
            return False, error
        
        parsed = self.parse_move(move_str)
        _, from_pos, to_pos, _ = parsed
        
        # Execute move
        self.board[to_pos] = self.board[from_pos]
        self.board[from_pos] = ''
        
        # Record move and position
        self.move_history.append(move_str)
        self._record_position()
        
        # Switch turn
        self.current_turn = self.BLACK if self.current_turn == self.WHITE else self.WHITE
        
        return True, ""
    
    def get_game_state(self):
        """
        Check the current game state.
        Returns: 'ongoing', 'white_wins', 'black_wins', 'draw_stalemate',
                 'draw_repetition', 'draw_material'
        """
        # Check for insufficient material
        if self._is_insufficient_material():
            return 'draw_material'
        
        # Check for threefold repetition
        if self._is_threefold_repetition():
            return 'draw_repetition'
        
        current = self.current_turn
        in_check = self._is_in_check(current)
        has_moves = self._has_legal_moves(current)
        
        if not has_moves:
            if in_check:
                # Checkmate
                return 'white_wins' if current == self.BLACK else 'black_wins'
            else:
                # Stalemate
                return 'draw_stalemate'
        
        return 'ongoing'
    
    def get_board_display(self):
        """Return a string representation of the board."""
        squares = "| " + " | ".join(str(i+1) for i in range(8)) + " |"
        pieces = "| " + " | ".join(p if p else '.' for p in self.board) + " |"
        return f"{squares}\\n{pieces}"


class HumanAgent:
    """Human player that inputs moves via terminal."""
    
    def __init__(self, name, color):
        self.name = name
        self.color = color
    
    def make_move(self, board, move_history):
        """Display board state and prompt for move input."""
        game = OneDChessGame()
        game.board = board[:]
        game.current_turn = self.color
        
        while True:
            # Display current board state
            print()
            print("=" * 40)
            print(f"{self.name}'s turn ({'White' if self.color == 'W' else 'Black'})")
            print("=" * 40)
            print()
            print("Board (squares 1-8):")
            print("| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |")
            print("| " + " | ".join(p if p else '.' for p in board) + " |")
            print()
            print("Pieces: K=King, N=Knight, R=Rook")
            print("        Uppercase=White, lowercase=Black")
            print()
            
            # Show check status
            if game._is_in_check(self.color):
                print("*** YOU ARE IN CHECK! ***")
                print()
            
            # Show available moves
            valid_moves = game.get_all_valid_moves(self.color)
            print(f"Valid moves: {', '.join(valid_moves)}")
            print()
            print("Move format: [Piece][From][To] or [Piece][From]x[To] for captures")
            print("Examples: N24 (Knight from 2 to 4), R3x6 (Rook from 3 captures on 6)")
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
        """Pick a random valid move."""
        game = OneDChessGame()
        game.board = board[:]
        game.current_turn = self.color
        
        valid_moves = game.get_all_valid_moves(self.color)
        if not valid_moves:
            return None
        return random.choice(valid_moves)


def print_board(board):
    """Print the board."""
    print("| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |")
    print("| " + " | ".join(p if p else '.' for p in board) + " |")


if __name__ == "__main__":
    print("=" * 50)
    print("1D CHESS - Human vs Random Bot")
    print("=" * 50)
    print()
    print("Starting position:")
    print("White: King(1), Knight(2), Rook(3)")
    print("Black: rook(6), knight(7), king(8)")
    print()
    
    game = OneDChessGame()
    
    # Randomize starting color
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
        
        # Get move from agent
        try:
            move = current_agent.make_move(game.board[:], game.move_history[:])
        except Exception as e:
            print(f"{current_name} crashed: {e}")
            print(f"{opponent_name} wins!")
            break
        
        if move is None:
            print(f"{current_name} has no valid moves!")
            break
        
        # Execute move
        success, error = game.make_move(move, current_color)
        if not success:
            print(f"{current_name} made invalid move '{move}': {error}")
            print(f"{opponent_name} wins!")
            break
        
        print(f"{current_name} plays: {move}")
        move_count += 1
        
        # Check game state
        state = game.get_game_state()
        if state != 'ongoing':
            print()
            print("Final Board:")
            print_board(game.board)
            print()
            
            if state == 'white_wins':
                print("CHECKMATE! Human (White) wins!")
            elif state == 'black_wins':
                print("CHECKMATE! Bot (Black) wins!")
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


def load_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "games" / "A7-1D_Chess.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()


def find_model_folder(pattern: str) -> str | None:
    """Find a model folder matching the given pattern."""
    if not AGENTS_DIR.exists():
        logger.error("Agents directory not found: %s", AGENTS_DIR)
        return None

    # Exact match first (matchmaker passes full folder names)
    exact = AGENTS_DIR / pattern
    if exact.is_dir():
        return pattern

    # Substring fallback for interactive CLI use
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
    # Rename OneDChessAgent to OneDChessAgent_{agent_idx}
    code = re.sub(r"class\s+OneDChessAgent\b", f"class OneDChessAgent_{agent_idx}", code)
    
    return code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    """Parse agent spec (model:run1:run2) into model pattern and list of runs."""
    parts = spec.split(":")
    model_pattern = parts[0]
    runs = [int(r) for r in parts[1:]]
    return model_pattern, runs


def run_match(game_code: str):
    temp_file = os.path.join(tempfile.gettempdir(), f"chess1d_{uuid.uuid4().hex[:8]}.py")
    try:
        with open(temp_file, "w") as f:
            f.write(game_code)
        result = subprocess.run(["python", temp_file], capture_output=True, text=True, timeout=600)
        return result.stdout
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def run_match_async(
    game_code: str,
    match_id: int,
    run_ids: tuple[int, int],
    log_f: Path,
    folder1: str,
    folder2: str,
):
    """Run a single match and return the score."""
    output = await asyncio.get_event_loop().run_in_executor(None, run_match, game_code)
    
    with open(log_f, "a") as f:
        f.write(f"--- Match {match_id}: {folder1} ({run_ids[0]}) vs {folder2} ({run_ids[1]}) ---\n")
        f.write(output)
        f.write("-" * 40 + "\n\n")

    res_match = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", output)
    if res_match:
        a1, a2 = float(res_match.group(1)), float(res_match.group(2))
        return {"success": True, "a1": a1, "a2": a2, "match_id": match_id}
    else:
        return {"success": False, "error": "Result parsing failed", "match_id": match_id}


async def main_async():
    parser = argparse.ArgumentParser(description="Run 1D Chess matches between stored AI agents")
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

    # Infer runs if not specified
    if not runs1:
        runs1 = get_available_runs(folder1, GAME_NAME)
    if not runs2:
        runs2 = get_available_runs(folder2, GAME_NAME)

    # Match the number of runs
    num_matches = min(len(runs1), len(runs2))
    if len(runs1) != len(runs2):
        logger.warning(
            "Number of runs for %s (%d) and %s (%d) don't match. Using first %d.",
            folder1,
            len(runs1),
            folder2,
            len(runs2),
            num_matches,
        )
    
    runs1 = runs1[:num_matches]
    runs2 = runs2[:num_matches]

    print("\n" + "=" * 60)
    print("1D CHESS MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GAME_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    agent_suffix = f"{folder1}_vs_{folder2}"
    log_f = GAME_LOGS_DIR / f"{ts}_{agent_suffix}_match.txt"

    match_tasks = []
    
    for i in range(num_matches):
        run1 = runs1[i]
        run2 = runs2[i]
        
        code1, imp1 = load_stored_agent(folder1, GAME_NAME, run1, 1)
        code2, imp2 = load_stored_agent(folder2, GAME_NAME, run2, 2)
        
        if not code1 or not code2:
            print(f"  FAILED to prepare match {i+1}: Could not load agent code.")
            continue

        game_code = GAME_CODE_TEMPLATE.format(
            extra_imports="\n".join(set(imp1.split("\n") + imp2.split("\n"))),
            agent1_code=code1,
            agent2_code=code2,
            num_games=NUM_ROUNDS_PER_MATCH,
            move_timeout=MOVE_TIME_LIMIT,
            max_moves=MAX_MOVES_PER_GAME,
        )
        
        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2), log_f, folder1, folder2))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)
    
    # Sort results by match_id for consistent output
    results.sort(key=lambda x: x["match_id"])
    
    total1, total2 = 0.0, 0.0
    for res in results:
        m_id = res["match_id"]
        r1, r2 = runs1[m_id - 1], runs2[m_id - 1]
        if res["success"]:
            a1, a2 = res["a1"], res["a2"]
            total1 += a1
            total2 += a2
            print(f"  Match {m_id} ({folder1}:{r1} vs {folder2}:{r2}): {a1} - {a2}")
        else:
            print(f"  Match {m_id} ({folder1}:{r1} vs {folder2}:{r2}): FAILED - {res.get('error')}")

    print("\nFINAL RESULTS:")
    print(f"  {folder1}: {total1}")
    print(f"  {folder2}: {total2}")
    print(f"\nLogs saved to: {log_f}")


if __name__ == "__main__":
    asyncio.run(main_async())
