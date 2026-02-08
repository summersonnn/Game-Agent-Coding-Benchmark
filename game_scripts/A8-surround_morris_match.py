"""
Surround Morris Match Runner: Orchestrates head-to-head matches for A8-SurroundMorris.

Nine Men's Morris variant where capture uses spatial surrounding instead of mill
formation. 24-spot board, placement then movement phases, with the "overwhelm"
capture rule: a piece is captured when it has zero empty neighbors AND more
opponent neighbors than friendly neighbors.
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
import logging
from dotenv import load_dotenv

# Add utils directory to sys.path
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging

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

# Results directories
RESULTS_DIR = Path(__file__).parent.parent / "results" / "surround_morris"
GAME_LOGS_DIR = RESULTS_DIR / "game_logs"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A8-SurroundMorris"

# The game code template (runs in subprocess)
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

# --- Game Configuration ---
NUM_GAMES = {num_games}
AGENT1_INFO = "{agent1_info}"
AGENT2_INFO = "{agent2_info}"

{extra_imports}

{agent1_code}

{agent2_code}


# --- Board Adjacency ---
ADJACENCY = {{
    0: [1, 9],       1: [0, 2, 4],     2: [1, 14],
    3: [4, 10],      4: [1, 3, 5, 7],  5: [4, 13],
    6: [7, 11],      7: [4, 6, 8],     8: [7, 12],
    9: [0, 10, 21],  10: [3, 9, 11, 18], 11: [6, 10, 15],
    12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
    15: [11, 16],    16: [15, 17, 19],  17: [12, 16],
    18: [10, 19],    19: [16, 18, 20, 22], 20: [13, 19],
    21: [9, 22],     22: [19, 21, 23],  23: [14, 22],
}}


class SurroundMorrisGame:
    """Manages the Surround Morris game state and rules."""

    def __init__(self):
        self.board = [''] * 24
        self.phase = 'placement'
        self.pieces_in_hand = {{'B': 9, 'W': 9}}
        self.pieces_on_board = {{'B': 0, 'W': 0}}
        self.current_player = 'B'
        self.move_count = 0
        self.consecutive_passes = 0

    def opponent(self, color):
        return 'W' if color == 'B' else 'B'

    def is_captured(self, spot, board=None):
        """
        Check if the piece at spot satisfies the capture condition.
        Captured when: zero empty neighbors AND opponent neighbors > friendly neighbors.
        """
        b = board if board is not None else self.board
        piece = b[spot]
        if not piece:
            return False

        opp = self.opponent(piece)
        empty_count = 0
        friendly_count = 0
        opp_count = 0

        for neighbor in ADJACENCY[spot]:
            n = b[neighbor]
            if n == '':
                empty_count += 1
            elif n == piece:
                friendly_count += 1
            else:
                opp_count += 1

        return empty_count == 0 and opp_count > friendly_count

    def validate_placement(self, spot, color):
        """
        Validate a placement move.
        Returns (ok, message, error_code).
        """
        if not isinstance(spot, int) or spot < 0 or spot > 23:
            return False, f"Spot {{spot}} out of range [0, 23]", "INVALID_SPOT_OOB"

        if self.board[spot] != '':
            return False, f"Spot {{spot}} is occupied by '{{self.board[spot]}}'", "INVALID_SPOT_OCCUPIED"

        if self.phase != 'placement':
            return False, "Not in placement phase", "INVALID_WRONG_PHASE"

        # Anti-suicide check: simulate placement, process opponent captures, then
        # check if the placed piece itself would be captured.
        sim_board = self.board[:]
        sim_board[spot] = color
        opp = self.opponent(color)

        # Remove opponent captures first
        for s in range(24):
            if sim_board[s] == opp and self.is_captured(s, sim_board):
                sim_board[s] = ''

        # Now check if placed piece is still captured
        if self.is_captured(spot, sim_board):
            return False, f"Placing at {{spot}} is suicide (piece would be captured)", "INVALID_SUICIDE"

        return True, "Valid", ""

    def validate_movement(self, from_spot, to_spot, color):
        """
        Validate a movement move.
        Returns (ok, message, error_code).
        """
        if self.phase != 'movement':
            return False, "Not in movement phase", "INVALID_WRONG_PHASE"

        if not isinstance(from_spot, int) or from_spot < 0 or from_spot > 23:
            return False, f"Source {{from_spot}} out of range [0, 23]", "INVALID_SPOT_OOB"

        if not isinstance(to_spot, int) or to_spot < 0 or to_spot > 23:
            return False, f"Destination {{to_spot}} out of range [0, 23]", "INVALID_DEST_OOB"

        if self.board[from_spot] != color:
            actual = self.board[from_spot]
            return False, f"Spot {{from_spot}} has '{{actual}}', not your piece '{{color}}'", "INVALID_NOT_YOUR_PIECE"

        if self.board[to_spot] != '':
            return False, f"Destination {{to_spot}} is occupied", "INVALID_DEST_OCCUPIED"

        if to_spot not in ADJACENCY[from_spot]:
            return False, f"Spots {{from_spot}} and {{to_spot}} are not adjacent", "INVALID_NOT_ADJACENT"

        return True, "Valid", ""

    def apply_placement(self, spot, color):
        """Place a piece, process captures, return list of captured spots."""
        self.board[spot] = color
        self.pieces_in_hand[color] -= 1
        self.pieces_on_board[color] += 1

        opp = self.opponent(color)
        captured = []
        for s in range(24):
            if self.board[s] == opp and self.is_captured(s):
                captured.append(s)

        for s in captured:
            self.board[s] = ''
            self.pieces_on_board[opp] -= 1

        return captured

    def apply_movement(self, from_spot, to_spot, color):
        """Move a piece, process captures, return list of captured spots."""
        self.board[from_spot] = ''
        self.board[to_spot] = color

        opp = self.opponent(color)
        captured = []
        for s in range(24):
            if self.board[s] == opp and self.is_captured(s):
                captured.append(s)

        for s in captured:
            self.board[s] = ''
            self.pieces_on_board[opp] -= 1

        return captured

    def get_legal_placements(self, color):
        """Return list of empty spots where placement is not suicide."""
        legal = []
        for spot in range(24):
            ok, _, _ = self.validate_placement(spot, color)
            if ok:
                legal.append(spot)
        return legal

    def get_legal_movements(self, color):
        """Return list of (from_spot, to_spot) pairs for the player's pieces."""
        legal = []
        for from_spot in range(24):
            if self.board[from_spot] != color:
                continue
            for to_spot in ADJACENCY[from_spot]:
                if self.board[to_spot] == '':
                    legal.append((from_spot, to_spot))
        return legal

    def is_game_over(self):
        """
        Check game-over conditions (movement phase only).
        Returns (is_over, result_description).
        """
        if self.phase != 'movement':
            return False, None

        opp = self.opponent(self.current_player)
        if self.pieces_on_board[opp] == 0:
            return True, f"{{self.current_player}} wins (opponent has 0 pieces)"

        if self.pieces_on_board[self.current_player] == 0:
            return True, f"{{opp}} wins (opponent has 0 pieces)"

        if self.move_count >= 200:
            return True, "Draw (200 movement turns reached)"

        if self.consecutive_passes >= 6:
            return True, "Draw (6 consecutive passes)"

        return False, None

    def check_phase_transition(self):
        """Transition from placement to movement when all pieces are placed."""
        if self.phase == 'placement' and self.pieces_in_hand['B'] == 0 and self.pieces_in_hand['W'] == 0:
            self.phase = 'movement'
            self.move_count = 0
            self.consecutive_passes = 0

    def display_board(self):
        """Print ASCII art board visualization."""
        def p(i):
            v = self.board[i]
            return v if v else '.'

        print(f" {{p(0)}}----------{{p(1)}}----------{{p(2)}}")
        print(f" |           |           |")
        print(f" |   {{p(3)}}-------{{p(4)}}-------{{p(5)}}   |")
        print(f" |   |       |       |   |")
        print(f" |   |   {{p(6)}}---{{p(7)}}---{{p(8)}}   |   |")
        print(f" |   |   |       |   |   |")
        print(f" {{p(9)}}---{{p(10)}}---{{p(11)}}       {{p(12)}}---{{p(13)}}---{{p(14)}}")
        print(f" |   |   |       |   |   |")
        print(f" |   |   {{p(15)}}---{{p(16)}}---{{p(17)}}   |   |")
        print(f" |   |       |       |   |")
        print(f" |   {{p(18)}}-------{{p(19)}}-------{{p(20)}}   |")
        print(f" |           |           |")
        print(f" {{p(21)}}----------{{p(22)}}----------{{p(23)}}")

    def get_state_for_agent(self, color):
        """Build the state dict passed to agent.make_move()."""
        return {{
            "board": self.board[:],
            "phase": self.phase,
            "your_color": color,
            "opponent_color": self.opponent(color),
            "pieces_in_hand": dict(self.pieces_in_hand),
            "pieces_on_board": dict(self.pieces_on_board),
            "move_count": self.move_count,
        }}


# --- Stats ---
stats = {{
    "p1_invalid": 0,
    "p2_invalid": 0,
    "p1_timeout": 0,
    "p2_timeout": 0,
    "p1_crash": 0,
    "p2_crash": 0,
    "p1_captures": 0,
    "p2_captures": 0,
    "p1_pass": 0,
    "p2_pass": 0,
    "turns": 0,
}}

MAX_ATTEMPTS = 3


def play_game(game_num, total_scores):
    game = SurroundMorrisGame()

    # Randomize starting agent
    if random.random() < 0.5:
        b_agent_class = SurroundMorrisAgent_1
        w_agent_class = SurroundMorrisAgent_2
        b_name = "Agent-1"
        w_name = "Agent-2"
    else:
        b_agent_class = SurroundMorrisAgent_2
        w_agent_class = SurroundMorrisAgent_1
        b_name = "Agent-2"
        w_name = "Agent-1"

    print()
    print("=" * 60)
    print(f"GAME {{game_num}}")
    print(f"Agent-1: {{AGENT1_INFO}}")
    print(f"Agent-2: {{AGENT2_INFO}}")
    print(f"{{b_name}} plays B (Black), {{w_name}} plays W (White)")
    print("=" * 60)

    # Initialize agents
    try:
        b_agent = b_agent_class(b_name, 'B')
    except Exception as e:
        print(f"{{b_name}} (B) init crash: {{e}}")
        return w_name

    try:
        w_agent = w_agent_class(w_name, 'W')
    except Exception as e:
        print(f"{{w_name}} (W) init crash: {{e}}")
        return b_name

    agents = {{'B': b_agent, 'W': w_agent}}
    names = {{'B': b_name, 'W': w_name}}

    def get_p_prefix(agent_name):
        return "p1" if agent_name == "Agent-1" else "p2"

    def do_random_placement(color):
        """Fallback: random legal placement."""
        legal = game.get_legal_placements(color)
        if legal:
            spot = random.choice(legal)
            captured = game.apply_placement(spot, color)
            return spot, captured
        return None, []

    def do_random_movement(color):
        """Fallback: random legal movement."""
        legal = game.get_legal_movements(color)
        if legal:
            from_s, to_s = random.choice(legal)
            captured = game.apply_movement(from_s, to_s, color)
            return (from_s, to_s), captured
        return None, []

    # --- Placement Phase ---
    placement_turn = 0
    while game.phase == 'placement':
        color = game.current_player
        agent = agents[color]
        agent_name = names[color]
        p_prefix = get_p_prefix(agent_name)
        stats["turns"] += 1
        placement_turn += 1

        state = game.get_state_for_agent(color)
        feedback = None
        move_made = False

        for attempt in range(MAX_ATTEMPTS):
            move = None
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(max(1, int(MOVE_TIMEOUT)))
                try:
                    move = agent.make_move(state, feedback)
                finally:
                    signal.alarm(0)
            except MoveTimeoutException:
                print(f"{{agent_name}} ({{color}}): TIMEOUT")
                stats[f"{{p_prefix}}_timeout"] += 1
                spot, captured = do_random_placement(color)
                if spot is not None:
                    cap_str = f" captured {{captured}}" if captured else ""
                    print(f"{{agent_name}} ({{color}}): random placement at {{spot}}{{cap_str}}")
                    stats[f"{{p_prefix}}_captures"] += len(captured)
                move_made = True
                break
            except Exception as e:
                print(f"{{agent_name}} ({{color}}): CRASH '{{str(e)[:80]}}'")
                stats[f"{{p_prefix}}_crash"] += 1
                spot, captured = do_random_placement(color)
                if spot is not None:
                    cap_str = f" captured {{captured}}" if captured else ""
                    print(f"{{agent_name}} ({{color}}): random placement at {{spot}}{{cap_str}}")
                    stats[f"{{p_prefix}}_captures"] += len(captured)
                move_made = True
                break

            # Validate placement
            if not isinstance(move, int):
                try:
                    move = int(move)
                except (ValueError, TypeError):
                    stats[f"{{p_prefix}}_invalid"] += 1
                    remaining = MAX_ATTEMPTS - attempt - 1
                    print(f"{{agent_name}} ({{color}}): INVALID OUTPUT '{{move}}' ({{remaining}} retries)")
                    feedback = {{
                        "error_code": "INVALID_OUTPUT",
                        "error_message": f"Expected int, got {{type(move).__name__}}: {{move}}",
                        "attempted_move": str(move),
                        "attempt_number": attempt + 1,
                    }}
                    continue

            ok, msg, error_code = game.validate_placement(move, color)
            if not ok:
                stats[f"{{p_prefix}}_invalid"] += 1
                remaining = MAX_ATTEMPTS - attempt - 1
                print(f"{{agent_name}} ({{color}}): INVALID placement at {{move}} - {{msg}} ({{remaining}} retries)")
                feedback = {{
                    "error_code": error_code,
                    "error_message": msg,
                    "attempted_move": move,
                    "attempt_number": attempt + 1,
                }}
                continue

            # Valid placement
            captured = game.apply_placement(move, color)
            cap_str = f" captured {{captured}}" if captured else ""
            print(f"{{agent_name}} ({{color}}): placement at {{move}}{{cap_str}}")
            stats[f"{{p_prefix}}_captures"] += len(captured)
            move_made = True
            break

        # All attempts exhausted
        if not move_made:
            print(f"{{agent_name}} ({{color}}): 3 failed attempts, random fallback")
            spot, captured = do_random_placement(color)
            if spot is not None:
                cap_str = f" captured {{captured}}" if captured else ""
                print(f"{{agent_name}} ({{color}}): random placement at {{spot}}{{cap_str}}")
                stats[f"{{p_prefix}}_captures"] += len(captured)

        # Check phase transition
        game.check_phase_transition()

        # Switch turns
        game.current_player = game.opponent(color)

        # Display board periodically
        if placement_turn % 6 == 0 or game.phase == 'movement':
            game.display_board()
            print(f"Pieces on board: B={{game.pieces_on_board['B']}} W={{game.pieces_on_board['W']}}")
            print(f"Pieces in hand: B={{game.pieces_in_hand['B']}} W={{game.pieces_in_hand['W']}}")

    # --- Movement Phase ---
    if game.phase == 'movement':
        print()
        print("--- MOVEMENT PHASE ---")
        game.display_board()

    while game.phase == 'movement':
        game_over, result_desc = game.is_game_over()
        if game_over:
            break

        color = game.current_player
        agent = agents[color]
        agent_name = names[color]
        p_prefix = get_p_prefix(agent_name)
        stats["turns"] += 1
        game.move_count += 1

        # Check if player has legal moves
        legal_moves = game.get_legal_movements(color)
        if not legal_moves:
            print(f"{{agent_name}} ({{color}}): no legal moves, forced pass")
            stats[f"{{p_prefix}}_pass"] += 1
            game.consecutive_passes += 1
            game.current_player = game.opponent(color)
            continue

        state = game.get_state_for_agent(color)
        feedback = None
        move_made = False

        for attempt in range(MAX_ATTEMPTS):
            move = None
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(max(1, int(MOVE_TIMEOUT)))
                try:
                    move = agent.make_move(state, feedback)
                finally:
                    signal.alarm(0)
            except MoveTimeoutException:
                print(f"{{agent_name}} ({{color}}): TIMEOUT")
                stats[f"{{p_prefix}}_timeout"] += 1
                mv, captured = do_random_movement(color)
                if mv:
                    cap_str = f" captured {{captured}}" if captured else ""
                    print(f"{{agent_name}} ({{color}}): random move {{mv[0]}}->{{mv[1]}}{{cap_str}}")
                    stats[f"{{p_prefix}}_captures"] += len(captured)
                    game.consecutive_passes = 0
                move_made = True
                break
            except Exception as e:
                print(f"{{agent_name}} ({{color}}): CRASH '{{str(e)[:80]}}'")
                stats[f"{{p_prefix}}_crash"] += 1
                mv, captured = do_random_movement(color)
                if mv:
                    cap_str = f" captured {{captured}}" if captured else ""
                    print(f"{{agent_name}} ({{color}}): random move {{mv[0]}}->{{mv[1]}}{{cap_str}}")
                    stats[f"{{p_prefix}}_captures"] += len(captured)
                    game.consecutive_passes = 0
                move_made = True
                break

            # Validate movement output
            if not isinstance(move, (tuple, list)) or len(move) != 2:
                stats[f"{{p_prefix}}_invalid"] += 1
                remaining = MAX_ATTEMPTS - attempt - 1
                print(f"{{agent_name}} ({{color}}): INVALID OUTPUT '{{move}}' ({{remaining}} retries)")
                feedback = {{
                    "error_code": "INVALID_OUTPUT",
                    "error_message": f"Expected (from_spot, to_spot) tuple, got {{type(move).__name__}}",
                    "attempted_move": str(move),
                    "attempt_number": attempt + 1,
                }}
                continue

            try:
                from_spot, to_spot = int(move[0]), int(move[1])
            except (ValueError, TypeError):
                stats[f"{{p_prefix}}_invalid"] += 1
                remaining = MAX_ATTEMPTS - attempt - 1
                print(f"{{agent_name}} ({{color}}): INVALID non-int move {{move}} ({{remaining}} retries)")
                feedback = {{
                    "error_code": "INVALID_OUTPUT",
                    "error_message": f"Could not convert move to integers: {{move}}",
                    "attempted_move": str(move),
                    "attempt_number": attempt + 1,
                }}
                continue

            ok, msg, error_code = game.validate_movement(from_spot, to_spot, color)
            if not ok:
                stats[f"{{p_prefix}}_invalid"] += 1
                remaining = MAX_ATTEMPTS - attempt - 1
                print(f"{{agent_name}} ({{color}}): INVALID move {{from_spot}}->{{to_spot}} - {{msg}} ({{remaining}} retries)")
                feedback = {{
                    "error_code": error_code,
                    "error_message": msg,
                    "attempted_move": (from_spot, to_spot),
                    "attempt_number": attempt + 1,
                }}
                continue

            # Valid movement
            captured = game.apply_movement(from_spot, to_spot, color)
            cap_str = f" captured {{captured}}" if captured else ""
            print(f"{{agent_name}} ({{color}}): move {{from_spot}}->{{to_spot}}{{cap_str}}")
            stats[f"{{p_prefix}}_captures"] += len(captured)
            game.consecutive_passes = 0
            move_made = True
            break

        # All attempts exhausted
        if not move_made:
            print(f"{{agent_name}} ({{color}}): 3 failed attempts, random fallback")
            mv, captured = do_random_movement(color)
            if mv:
                cap_str = f" captured {{captured}}" if captured else ""
                print(f"{{agent_name}} ({{color}}): random move {{mv[0]}}->{{mv[1]}}{{cap_str}}")
                stats[f"{{p_prefix}}_captures"] += len(captured)
                game.consecutive_passes = 0
            else:
                print(f"{{agent_name}} ({{color}}): no legal moves after fallback, forced pass")
                stats[f"{{p_prefix}}_pass"] += 1
                game.consecutive_passes += 1

        # Switch turns
        game.current_player = game.opponent(color)

        # Display board every 10 moves
        if game.move_count % 10 == 0:
            game.display_board()
            print(f"Move {{game.move_count}}: B={{game.pieces_on_board['B']}} W={{game.pieces_on_board['W']}}")

    # Game over
    game_over, result_desc = game.is_game_over()
    if not game_over:
        # Shouldn't happen, but handle placement-only edge case
        result_desc = "Game ended unexpectedly"

    print()
    game.display_board()
    print(f"Pieces: B={{game.pieces_on_board['B']}} W={{game.pieces_on_board['W']}}")
    print(f"GAME {{game_num}} ENDED: {{result_desc}}")

    # Determine winner
    if "wins" in result_desc:
        winner_color = result_desc[0]
        winner = names[winner_color]
    elif "Draw" in result_desc:
        winner = "DRAW"
    else:
        winner = "DRAW"

    print(f"Winner: {{winner}}")

    # Update scores
    if winner == "DRAW":
        total_scores["Agent-1"] += 0.5
        total_scores["Agent-2"] += 0.5
    elif winner in total_scores:
        total_scores[winner] += 1

    print(
        f"Running Total - Agent-1: {{total_scores['Agent-1']}} | "
        f"Agent-2: {{total_scores['Agent-2']}}"
    )
    print("=" * 60)
    sys.stdout.flush()

    return winner


def main():
    total_scores = {{"Agent-1": 0, "Agent-2": 0}}

    for i in range(NUM_GAMES):
        play_game(i + 1, total_scores)
        sys.stdout.flush()

    print(f"RESULT:Agent-1={{total_scores['Agent-1']}},Agent-2={{total_scores['Agent-2']}}")
    print("--- MATCH STATISTICS ---")
    print(f"Agent-1 Invalid Moves: {{stats['p1_invalid']}}")
    print(f"Agent-2 Invalid Moves: {{stats['p2_invalid']}}")
    print(f"Agent-1 Timeouts: {{stats['p1_timeout']}}")
    print(f"Agent-2 Timeouts: {{stats['p2_timeout']}}")
    print(f"Agent-1 Crashes: {{stats['p1_crash']}}")
    print(f"Agent-2 Crashes: {{stats['p2_crash']}}")
    print(f"Agent-1 Captures: {{stats['p1_captures']}}")
    print(f"Agent-2 Captures: {{stats['p2_captures']}}")
    print(f"Agent-1 Forced Passes: {{stats['p1_pass']}}")
    print(f"Agent-2 Forced Passes: {{stats['p2_pass']}}")
    print(f"Total Turns: {{stats['turns']}}")


if __name__ == "__main__":
    main()
'''

# --- Human play mode ---
HUMAN_GAME_CODE = '''
import random

# --- Board Adjacency ---
ADJACENCY = {
    0: [1, 9],       1: [0, 2, 4],     2: [1, 14],
    3: [4, 10],      4: [1, 3, 5, 7],  5: [4, 13],
    6: [7, 11],      7: [4, 6, 8],     8: [7, 12],
    9: [0, 10, 21],  10: [3, 9, 11, 18], 11: [6, 10, 15],
    12: [8, 13, 17], 13: [5, 12, 14, 20], 14: [2, 13, 23],
    15: [11, 16],    16: [15, 17, 19],  17: [12, 16],
    18: [10, 19],    19: [16, 18, 20, 22], 20: [13, 19],
    21: [9, 22],     22: [19, 21, 23],  23: [14, 22],
}


class SurroundMorrisGame:
    """Manages the Surround Morris game state and rules."""

    def __init__(self):
        self.board = [''] * 24
        self.phase = 'placement'
        self.pieces_in_hand = {'B': 9, 'W': 9}
        self.pieces_on_board = {'B': 0, 'W': 0}
        self.current_player = 'B'
        self.move_count = 0
        self.consecutive_passes = 0

    def opponent(self, color):
        return 'W' if color == 'B' else 'B'

    def is_captured(self, spot, board=None):
        """
        Check if the piece at spot satisfies the capture condition.
        Captured when: zero empty neighbors AND opponent neighbors > friendly neighbors.
        """
        b = board if board is not None else self.board
        piece = b[spot]
        if not piece:
            return False

        opp = self.opponent(piece)
        empty_count = 0
        friendly_count = 0
        opp_count = 0

        for neighbor in ADJACENCY[spot]:
            n = b[neighbor]
            if n == '':
                empty_count += 1
            elif n == piece:
                friendly_count += 1
            else:
                opp_count += 1

        return empty_count == 0 and opp_count > friendly_count

    def validate_placement(self, spot, color):
        """
        Validate a placement move.
        Returns (ok, message, error_code).
        """
        if not isinstance(spot, int) or spot < 0 or spot > 23:
            return False, f"Spot {spot} out of range [0, 23]", "INVALID_SPOT_OOB"

        if self.board[spot] != '':
            return False, f"Spot {spot} is occupied by '{self.board[spot]}'", "INVALID_SPOT_OCCUPIED"

        if self.phase != 'placement':
            return False, "Not in placement phase", "INVALID_WRONG_PHASE"

        # Anti-suicide check
        sim_board = self.board[:]
        sim_board[spot] = color
        opp = self.opponent(color)

        for s in range(24):
            if sim_board[s] == opp and self.is_captured(s, sim_board):
                sim_board[s] = ''

        if self.is_captured(spot, sim_board):
            return False, f"Placing at {spot} is suicide (piece would be captured)", "INVALID_SUICIDE"

        return True, "Valid", ""

    def validate_movement(self, from_spot, to_spot, color):
        """Validate a movement move."""
        if self.phase != 'movement':
            return False, "Not in movement phase", "INVALID_WRONG_PHASE"

        if not isinstance(from_spot, int) or from_spot < 0 or from_spot > 23:
            return False, f"Source {from_spot} out of range [0, 23]", "INVALID_SPOT_OOB"

        if not isinstance(to_spot, int) or to_spot < 0 or to_spot > 23:
            return False, f"Destination {to_spot} out of range [0, 23]", "INVALID_DEST_OOB"

        if self.board[from_spot] != color:
            actual = self.board[from_spot]
            return False, f"Spot {from_spot} has '{actual}', not your piece '{color}'", "INVALID_NOT_YOUR_PIECE"

        if self.board[to_spot] != '':
            return False, f"Destination {to_spot} is occupied", "INVALID_DEST_OCCUPIED"

        if to_spot not in ADJACENCY[from_spot]:
            return False, f"Spots {from_spot} and {to_spot} are not adjacent", "INVALID_NOT_ADJACENT"

        return True, "Valid", ""

    def apply_placement(self, spot, color):
        """Place a piece, process captures, return list of captured spots."""
        self.board[spot] = color
        self.pieces_in_hand[color] -= 1
        self.pieces_on_board[color] += 1

        opp = self.opponent(color)
        captured = []
        for s in range(24):
            if self.board[s] == opp and self.is_captured(s):
                captured.append(s)

        for s in captured:
            self.board[s] = ''
            self.pieces_on_board[opp] -= 1

        return captured

    def apply_movement(self, from_spot, to_spot, color):
        """Move a piece, process captures, return list of captured spots."""
        self.board[from_spot] = ''
        self.board[to_spot] = color

        opp = self.opponent(color)
        captured = []
        for s in range(24):
            if self.board[s] == opp and self.is_captured(s):
                captured.append(s)

        for s in captured:
            self.board[s] = ''
            self.pieces_on_board[opp] -= 1

        return captured

    def get_legal_placements(self, color):
        """Return list of empty spots where placement is not suicide."""
        legal = []
        for spot in range(24):
            ok, _, _ = self.validate_placement(spot, color)
            if ok:
                legal.append(spot)
        return legal

    def get_legal_movements(self, color):
        """Return list of (from_spot, to_spot) pairs for the player's pieces."""
        legal = []
        for from_spot in range(24):
            if self.board[from_spot] != color:
                continue
            for to_spot in ADJACENCY[from_spot]:
                if self.board[to_spot] == '':
                    legal.append((from_spot, to_spot))
        return legal

    def is_game_over(self):
        """Check game-over conditions."""
        if self.phase != 'movement':
            return False, None

        opp = self.opponent(self.current_player)
        if self.pieces_on_board[opp] == 0:
            return True, f"{self.current_player} wins (opponent has 0 pieces)"

        if self.pieces_on_board[self.current_player] == 0:
            return True, f"{opp} wins (opponent has 0 pieces)"

        if self.move_count >= 200:
            return True, "Draw (200 movement turns reached)"

        if self.consecutive_passes >= 6:
            return True, "Draw (6 consecutive passes)"

        return False, None

    def check_phase_transition(self):
        """Transition from placement to movement when all pieces are placed."""
        if self.phase == 'placement' and self.pieces_in_hand['B'] == 0 and self.pieces_in_hand['W'] == 0:
            self.phase = 'movement'
            self.move_count = 0
            self.consecutive_passes = 0

    def display_board(self):
        """Print ASCII art board visualization with spot numbers."""
        def p(i):
            v = self.board[i]
            return v if v else '.'

        print()
        print("Board Layout (spot numbers for reference):")
        print()
        print(f" {p(0)}----------{p(1)}----------{p(2)}        0----------1----------2")
        print(f" |           |           |        |           |           |")
        print(f" |   {p(3)}-------{p(4)}-------{p(5)}   |        |   3-------4-------5   |")
        print(f" |   |       |       |   |        |   |       |       |   |")
        print(f" |   |   {p(6)}---{p(7)}---{p(8)}   |   |        |   |   6---7---8   |   |")
        print(f" |   |   |       |   |   |        |   |   |       |   |   |")
        print(f" {p(9)}---{p(10)}---{p(11)}       {p(12)}---{p(13)}---{p(14)}        9---10--11      12--13--14")
        print(f" |   |   |       |   |   |        |   |   |       |   |   |")
        print(f" |   |   {p(15)}---{p(16)}---{p(17)}   |   |        |   |   15--16--17  |   |")
        print(f" |   |       |       |   |        |   |       |       |   |")
        print(f" |   {p(18)}-------{p(19)}-------{p(20)}   |        |   18------19------20  |")
        print(f" |           |           |        |           |           |")
        print(f" {p(21)}----------{p(22)}----------{p(23)}        21---------22---------23")
        print()

    def get_state_for_agent(self, color):
        """Build the state dict passed to agent.make_move()."""
        return {
            "board": self.board[:],
            "phase": self.phase,
            "your_color": color,
            "opponent_color": self.opponent(color),
            "pieces_in_hand": dict(self.pieces_in_hand),
            "pieces_on_board": dict(self.pieces_on_board),
            "move_count": self.move_count,
        }


class HumanAgent:
    """Human player that inputs moves via terminal."""

    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
        """Display board state and prompt for move input."""
        game = SurroundMorrisGame()
        game.board = state["board"][:]
        game.phase = state["phase"]
        game.pieces_in_hand = state["pieces_in_hand"].copy()
        game.pieces_on_board = state["pieces_on_board"].copy()

        while True:
            print()
            print("=" * 60)
            print(f"{self.name}'s turn ({self.color})")
            print(f"Phase: {state['phase'].upper()}")
            print("=" * 60)

            game.display_board()

            print(f"Pieces on board: B={state['pieces_on_board']['B']} W={state['pieces_on_board']['W']}")
            print(f"Pieces in hand: B={state['pieces_in_hand']['B']} W={state['pieces_in_hand']['W']}")
            print()

            if feedback:
                print(f"Previous error: {feedback.get('error_message', 'Unknown')}")
                print()

            if state["phase"] == "placement":
                legal = game.get_legal_placements(self.color)
                print(f"Legal placement spots: {legal}")
                print()
                print("Enter a spot number (0-23) to place your piece:")
                
                try:
                    move = input("> ").strip()
                    spot = int(move)
                    ok, msg, _ = game.validate_placement(spot, self.color)
                    if ok:
                        return spot
                    else:
                        print(f"Invalid: {msg}")
                except ValueError:
                    print("Please enter a valid number.")
            else:
                legal = game.get_legal_movements(self.color)
                print(f"Legal moves: {legal}")
                print()
                print("Enter move as 'from to' (e.g., '3 4'):")
                
                try:
                    move = input("> ").strip()
                    parts = move.split()
                    if len(parts) != 2:
                        print("Please enter two numbers separated by space.")
                        continue
                    from_spot, to_spot = int(parts[0]), int(parts[1])
                    ok, msg, _ = game.validate_movement(from_spot, to_spot, self.color)
                    if ok:
                        return (from_spot, to_spot)
                    else:
                        print(f"Invalid: {msg}")
                except ValueError:
                    print("Please enter valid numbers.")


class RandomAgent:
    """Bot that plays random valid moves."""

    def __init__(self, name, color):
        self.name = name
        self.color = color

    def make_move(self, state, feedback=None):
        """Pick a random valid move."""
        game = SurroundMorrisGame()
        game.board = state["board"][:]
        game.phase = state["phase"]
        game.pieces_in_hand = state["pieces_in_hand"].copy()
        game.pieces_on_board = state["pieces_on_board"].copy()

        if state["phase"] == "placement":
            legal = game.get_legal_placements(self.color)
            if legal:
                return random.choice(legal)
            return 0
        else:
            legal = game.get_legal_movements(self.color)
            if legal:
                return random.choice(legal)
            return None


if __name__ == "__main__":
    print("=" * 60)
    print("SURROUND MORRIS - Human vs Random Bot")
    print("=" * 60)
    print()
    print("Capture Rule: A piece is captured when it has zero empty")
    print("neighbors AND more opponent neighbors than friendly neighbors.")
    print()
    if random.random() < 0.5:
        human = HumanAgent("Human", "B")
        bot = RandomAgent("Bot", "W")
        print("You are B (Black, moves first)")
    else:
        human = HumanAgent("Human", "W")
        bot = RandomAgent("Bot", "B")
        print("You are W (White, moves second)")

    agents = {"B": human if human.color == "B" else bot, "W": human if human.color == "W" else bot}
    names = {"B": agents["B"].name, "W": agents["W"].name}

    # --- Placement Phase ---
    print("--- PLACEMENT PHASE ---")
    print("Each player places 9 pieces.")
    
    while game.phase == 'placement':
        color = game.current_player
        agent = agents[color]
        agent_name = names[color]
        
        state = game.get_state_for_agent(color)
        move = agent.make_move(state, None)
        
        ok, msg, _ = game.validate_placement(move, color)
        if not ok:
            print(f"{agent_name} ({color}): Invalid placement {move} - {msg}")
            # Random fallback for bot
            if agent_name == "Bot":
                legal = game.get_legal_placements(color)
                if legal:
                    move = random.choice(legal)
                    captured = game.apply_placement(move, color)
                    cap_str = f" - captured {captured}" if captured else ""
                    print(f"{agent_name} ({color}): placed at {move}{cap_str}")
        else:
            captured = game.apply_placement(move, color)
            cap_str = f" - captured {captured}" if captured else ""
            print(f"{agent_name} ({color}): placed at {move}{cap_str}")
        
        game.check_phase_transition()
        game.current_player = game.opponent(color)

    # --- Movement Phase ---
    print()
    print("=" * 60)
    print("--- MOVEMENT PHASE ---")
    print("=" * 60)
    game.display_board()

    while game.phase == 'movement':
        game_over, result_desc = game.is_game_over()
        if game_over:
            break
        
        color = game.current_player
        agent = agents[color]
        agent_name = names[color]
        game.move_count += 1
        
        # Check if player has legal moves
        legal_moves = game.get_legal_movements(color)
        if not legal_moves:
            print(f"{agent_name} ({color}): no legal moves, forced pass")
            game.consecutive_passes += 1
            game.current_player = game.opponent(color)
            continue
        
        state = game.get_state_for_agent(color)
        move = agent.make_move(state, None)
        
        if move is None:
            print(f"{agent_name} ({color}): no move returned, pass")
            game.consecutive_passes += 1
            game.current_player = game.opponent(color)
            continue
        
        from_spot, to_spot = move
        ok, msg, _ = game.validate_movement(from_spot, to_spot, color)
        if not ok:
            print(f"{agent_name} ({color}): Invalid move {from_spot}->{to_spot} - {msg}")
            # Random fallback for bot
            if agent_name == "Bot" and legal_moves:
                from_spot, to_spot = random.choice(legal_moves)
                captured = game.apply_movement(from_spot, to_spot, color)
                cap_str = f" - captured {captured}" if captured else ""
                print(f"{agent_name} ({color}): moved {from_spot}->{to_spot}{cap_str}")
                game.consecutive_passes = 0
        else:
            captured = game.apply_movement(from_spot, to_spot, color)
            cap_str = f" - captured {captured}" if captured else ""
            print(f"{agent_name} ({color}): moved {from_spot}->{to_spot}{cap_str}")
            game.consecutive_passes = 0
        
        game.current_player = game.opponent(color)

    # Game over
    print()
    print("=" * 60)
    game.display_board()
    print(f"Pieces: B={game.pieces_on_board['B']} W={game.pieces_on_board['W']}")
    
    game_over, result_desc = game.is_game_over()
    if result_desc:
        print(f"GAME ENDED: {result_desc}")
    else:
        print("GAME ENDED")
    
    print()
    print("Thanks for playing!")
'''


def find_model_folder(pattern: str) -> str | None:
    """Find a model folder matching the given pattern."""
    if not AGENTS_DIR.exists():
        logger.error("Agents directory not found: %s", AGENTS_DIR)
        return None

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


def load_stored_agent(
    model_folder: str, game: str, run: int, agent_idx: int
) -> tuple[str, str]:
    """Load agent code from a stored file and extract the agent class."""
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

    # Extract imports and find class
    imports = []
    class_start_idx = None

    for i, line in enumerate(code_lines):
        stripped = line.strip()

        if stripped.startswith("class SurroundMorrisAgent"):
            class_start_idx = i
            break

        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:
                imports.append(stripped)

    if class_start_idx is None:
        logger.error("No SurroundMorrisAgent class found in %s", agent_file)
        return "", ""

    # Extract ONLY the SurroundMorrisAgent class
    class_lines = []
    base_indent = 0

    for i in range(class_start_idx, len(code_lines)):
        line = code_lines[i]
        stripped = line.strip()

        if i == class_start_idx:
            class_lines.append(line)
            base_indent = len(line) - len(line.lstrip())
            continue

        if not stripped or stripped.startswith("#"):
            class_lines.append(line)
            continue

        current_indent = len(line) - len(line.lstrip())

        if current_indent <= base_indent:
            break

        class_lines.append(line)

    agent_code = "\n".join(class_lines)

    # Rename SurroundMorrisAgent to SurroundMorrisAgent_{agent_idx}
    agent_code = re.sub(
        r"\bSurroundMorrisAgent\b", f"SurroundMorrisAgent_{agent_idx}", agent_code
    )

    return agent_code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    """Parse agent spec like 'model1:1:2' into (pattern, [run_ids])."""
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
    agent1_info: str,
    agent2_info: str,
) -> str:
    """Build the complete game code with both agent implementations."""
    return GAME_CODE_TEMPLATE.format(
        num_games=num_games,
        move_timeout=move_timeout,
        extra_imports=extra_imports,
        agent1_code=agent1_code,
        agent2_code=agent2_code,
        agent1_info=agent1_info,
        agent2_info=agent2_info,
    )


def run_match(
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = 600
) -> dict:
    """Run a single match in a subprocess."""
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"surround_morris_match_{match_id}_{temp_id}.py"
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

        # Parse results
        match = re.search(
            r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout
        )

        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            log_lines = []
            for line in result.stdout.splitlines():
                if line.startswith((
                    "Agent-1:", "Agent-2:", "GAME ", "Winner:",
                    "Running Total", "==========", "--- MOVEMENT",
                )) or "ENDED" in line or line.strip() == "":
                    log_lines.append(line)

            return {
                "match_id": match_id,
                "agent1_run_id": run_ids[0],
                "agent2_run_id": run_ids[1],
                "success": True,
                "agent1_score": float(match.group(1)),
                "agent2_score": float(match.group(2)),
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
    """Run a match asynchronously via executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    """Main entry point for agent-vs-agent matches."""
    parser = argparse.ArgumentParser(description="Run Surround Morris matches")
    parser.add_argument(
        "--agent", nargs="+",
        help="Agent specs: model1[:run1:run2] model2[:run3:run4]",
    )
    parser.add_argument(
        "--human", action="store_true",
        help="Play interactively against a random bot",
    )
    args = parser.parse_args()

    # Human play mode
    if args.human:
        temp_file = os.path.join(
            tempfile.gettempdir(), f"surround_morris_human_{uuid.uuid4().hex[:8]}.py"
        )
        try:
            with open(temp_file, "w") as f:
                f.write(HUMAN_GAME_CODE)
            subprocess.run(
                ["python", temp_file], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr
            )
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return

    if not args.agent or len(args.agent) != 2:
        print("ERROR: Need exactly 2 agent specifications.")
        print("Example: --agent mistral:1 gpt-5-mini:1")
        sys.exit(1)

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
    runs1 = runs1[:num_matches]
    runs2 = runs2[:num_matches]

    print("\n" + "=" * 60)
    print("SURROUND MORRIS MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GAME_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_f = GAME_LOGS_DIR / f"{ts}_match.txt"

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

        agent1_info = f"{folder1} (Run {run1})"
        agent2_info = f"{folder2} (Run {run2})"

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_GAMES_PER_MATCH,
            MOVE_TIME_LIMIT, agent1_info, agent2_info,
        )

        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)

    total1, total2 = 0.0, 0.0

    with open(log_f, "w") as f:
        f.write(f"Surround Morris Match - {ts}\n")
        f.write("=" * 60 + "\n\n")

        for result in sorted(results, key=lambda x: x["match_id"]):
            match_id = result["match_id"]
            if result["success"]:
                s1, s2 = result["agent1_score"], result["agent2_score"]
                total1 += s1
                total2 += s2
                status = f"Result: {s1:.1f} - {s2:.1f}"
                game_log = result.get("log", "")
                if game_log:
                    status += f"\n{game_log}\n"
                if result.get("stats_block"):
                    status += (
                        f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n"
                    )
            else:
                status = f"FAILED: {result.get('error', 'Unknown')}"

            print(f"  Match {match_id}: {status}")
            f.write(f"Match {match_id}: {status}\n")
            if result.get("stats_block"):
                f.write(
                    f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n"
                )
                f.write("-" * 60 + "\n\n")

    print("\nFINAL RESULTS:")
    print(f"  {folder1}: {total1:.1f}")
    print(f"  {folder2}: {total2:.1f}")
    print(f"\nLogs saved to: {log_f}")


if __name__ == "__main__":
    asyncio.run(main_async())
