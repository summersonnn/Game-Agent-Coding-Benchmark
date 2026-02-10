"""
WordMatrix Match Runner: Orchestrates head-to-head matches for A6-WordMatrixGame.

Game Rules: (2 Players)
1. 4x4 board of random lowercase letters.
2. Players take turns selecting a path of adjacent cells and providing a word
   whose letters contain the path letters as a subsequence.
3. Valid moves clear cells and score 10 + 10 * cleared_cells.
4. Invalid path/word: -25 per attempt, up to 3 attempts per turn with error feedback.
   Valid path + invalid word locks the path; subsequent retries only accept a word string.
5. CANCEL: -10, ends turn. Timeout/crash/invalid message: -50, ends turn (no retry).
6. Game ends when no valid path exists or 6 total passes accumulate.
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
import random
import signal
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
    NUM_GAMES_PER_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "10"))
except (ValueError, TypeError):
    NUM_GAMES_PER_MATCH = 10

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0")) * 5
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 5.0

# Results directories
RESULTS_DIR = Path(__file__).parent.parent / "results" / "word_matrix"
GAME_LOGS_DIR = RESULTS_DIR / "game_logs"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A6-WordMatrixGame"

# Dictionary path
WORDS_FILE = Path(__file__).parent.parent / "games" / "words.txt"

# The game code template (runs in subprocess)
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal
import time
import string

# Move timeout in seconds
MOVE_TIMEOUT = {move_timeout}

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

# --- Game Configuration ---
NUM_GAMES = {num_games}
WORDS_FILE_PATH = r"{words_file_path}"
AGENT1_INFO = "{agent1_info}"
AGENT2_INFO = "{agent2_info}"

{extra_imports}

{agent1_code}

{agent2_code}


def load_words():
    """Load dictionary: alphabetic-only words (no hyphens)."""
    try:
        with open(WORDS_FILE_PATH, 'r') as f:
            return {{
                line.strip().lower()
                for line in f
                if line.strip() and line.strip().isalpha()
            }}
    except Exception as e:
        print(f"ERROR: Could not load words from {{WORDS_FILE_PATH}}: {{e}}")
        sys.exit(1)


class WordMatrixGame:
    """Manages the WordMatrix game state and validation."""

    def __init__(self, words_set):
        self.words_set = words_set
        self.board = [
            [random.choice(string.ascii_lowercase) for _ in range(4)]
            for _ in range(4)
        ]
        self.scores = {{"Agent-1": 0, "Agent-2": 0}}
        self.total_passes = 0

    def has_valid_path(self):
        """Check if any path of at least 2 adjacent non-empty cells exists."""
        for r in range(4):
            for c in range(4):
                if self.board[r][c] == "":
                    continue
                for dr, dc in [(0, 1), (1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 4 and 0 <= nc < 4 and self.board[nr][nc] != "":
                        return True
        return False

    def is_game_over(self):
        """Game ends when no valid path exists or 6 total passes."""
        return not self.has_valid_path() or self.total_passes >= 6

    def board_copy(self):
        """Return a deep copy of the board."""
        return [row[:] for row in self.board]

    def validate_path(self, path):
        """Validate a path. Returns (ok, reason, error_code)."""
        if not isinstance(path, (list, tuple)) or len(path) < 2:
            return False, "Path must be a list/tuple of at least 2 cells", "INVALID_PATH_TOO_SHORT"

        visited = set()
        for i, cell in enumerate(path):
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                return False, f"Cell {{i}} is not a valid (row, col) pair", "INVALID_PATH_BAD_CELL"

            try:
                r, c = int(cell[0]), int(cell[1])
            except (ValueError, TypeError):
                return False, f"Cell {{i}} has non-integer coordinates", "INVALID_PATH_BAD_CELL"

            if not (0 <= r < 4 and 0 <= c < 4):
                return False, f"Cell ({{}},{{}}) is out of bounds".format(r, c), "INVALID_PATH_OOB"

            if (r, c) in visited:
                return False, f"Cell ({{}},{{}}) visited twice".format(r, c), "INVALID_PATH_REVISIT"

            if self.board[r][c] == "":
                return False, f"Cell ({{}},{{}}) is empty".format(r, c), "INVALID_PATH_EMPTY"

            if i > 0:
                pr, pc = int(path[i - 1][0]), int(path[i - 1][1])
                if abs(r - pr) + abs(c - pc) != 1:
                    return False, (
                        f"Cells ({{}},{{}}) and ({{}},{{}}) are not adjacent"
                        .format(pr, pc, r, c)
                    ), "INVALID_PATH_NOT_ADJACENT"

            visited.add((r, c))

        return True, "Valid", ""

    def get_path_letters(self, path):
        """Extract letters along the path."""
        return [self.board[int(r)][int(c)] for r, c in path]

    def validate_word(self, word, path):
        """
        Validate a word against a path.
        Returns (ok, reason, extra_letters, error_code).
        """
        if not isinstance(word, str) or not word:
            return False, "Word must be a non-empty string", [], "INVALID_WORD_EMPTY"

        word = word.lower()
        path_letters = self.get_path_letters(path)
        path_len = len(path_letters)

        # Length constraint
        if len(word) > 2 * path_len:
            return False, (
                f"Word length {{len(word)}} exceeds 2 * path length {{path_len}}"
            ), [], "INVALID_WORD_TOO_LONG"

        if len(word) < path_len:
            return False, (
                f"Word length {{len(word)}} less than path length {{path_len}}"
            ), [], "INVALID_WORD_TOO_SHORT"

        # Subsequence check: path letters must appear as subsequence of word
        path_idx = 0
        extra_letters = []
        for ch in word:
            if path_idx < path_len and ch == path_letters[path_idx]:
                path_idx += 1
            else:
                extra_letters.append(ch)

        if path_idx < path_len:
            return False, (
                f"Path letters not found as subsequence in word "
                f"(matched {{path_idx}}/{{path_len}})"
            ), [], "INVALID_WORD_SUBSEQUENCE"

        # Dictionary check
        if word not in self.words_set:
            return False, f"Word '{{word}}' not in dictionary", [], "INVALID_WORD_NOT_IN_DICT"

        return True, "Valid", extra_letters, ""

    def apply_move(self, agent_name, path, word):
        """
        Apply a valid move: update board and score.
        Returns (points, cleared_cells).
        """
        word = word.lower()
        path_letters = self.get_path_letters(path)
        path_len = len(path_letters)

        # Compute extra letters via subsequence walk
        path_idx = 0
        extra_letters = []
        for ch in word:
            if path_idx < path_len and ch == path_letters[path_idx]:
                path_idx += 1
            else:
                extra_letters.append(ch)

        # Shuffle path cell indices
        cell_indices = [(int(r), int(c)) for r, c in path]
        random.shuffle(cell_indices)

        # Place extra letters, clear the rest
        for i, (r, c) in enumerate(cell_indices):
            if i < len(extra_letters):
                self.board[r][c] = extra_letters[i]
            else:
                self.board[r][c] = ""

        cleared = path_len - len(extra_letters)
        points = 10 + 10 * cleared
        self.scores[agent_name] += points
        self.total_passes = 0
        return points, cleared

    def apply_penalty(self, agent_name, amount):
        """Apply a point penalty to the given agent."""
        self.scores[agent_name] -= amount

    def apply_pass(self):
        """Record a pass (no point change)."""
        self.total_passes += 1

    def display_board(self):
        """Print the board in a readable format."""
        print("    0  1  2  3")
        print("   -----------")
        for r in range(4):
            row_str = " ".join(
                f" {{self.board[r][c]}}" if self.board[r][c] else " ."
                for c in range(4)
            )
            print(f"{{r}} |{{row_str}}")


# --- Stats ---
stats = {{
    "p1_invalid_path": 0,
    "p2_invalid_path": 0,
    "p1_invalid_word": 0,
    "p2_invalid_word": 0,
    "p1_timeout": 0,
    "p2_timeout": 0,
    "p1_crash": 0,
    "p2_crash": 0,
    "p1_invalid_message": 0,
    "p2_invalid_message": 0,
    "p1_pass": 0,
    "p2_pass": 0,
    "p1_cancel": 0,
    "p2_cancel": 0,
    "p1_retry_success": 0,
    "p2_retry_success": 0,
    "normal_end": 0,
    "pass_end": 0,
    "turns": 0,
}}


def play_game(game_num, total_scores):
    words_set = load_words()
    game = WordMatrixGame(words_set)

    # Initialize agents
    try:
        agent1 = WordMatrixAgent_1("Agent-1")
    except Exception as e:
        print(f"Agent-1 init crash: {{e}}")
        return "Agent-2"

    try:
        agent2 = WordMatrixAgent_2("Agent-2")
    except Exception as e:
        print(f"Agent-2 init crash: {{e}}")
        return "Agent-1"

    current_agent, other_agent = (
        (agent1, agent2) if random.random() < 0.5 else (agent2, agent1)
    )

    print()
    print("=" * 60)
    print(f"GAME {{game_num}}")
    print(f"Agent-1: {{AGENT1_INFO}}")
    print(f"Agent-2: {{AGENT2_INFO}}")
    print("=" * 60)

    game.display_board()

    MAX_ATTEMPTS = 3
    PENALTY_INVALID = 25
    PENALTY_CANCEL = 10
    PENALTY_FATAL = 50

    while not game.is_game_over():
        stats["turns"] += 1
        agent_name = current_agent.name
        p_prefix = "p1" if agent_name == "Agent-1" else "p2"

        failed_attempts = []
        turn_penalty = 0
        turn_resolved = False
        locked_path = None

        for attempt in range(MAX_ATTEMPTS):
            feedback = None
            if attempt > 0:
                feedback = {{
                    "error_code": failed_attempts[-1]["error_code"],
                    "error_message": failed_attempts[-1]["error_message"],
                    "failed_attempts": list(failed_attempts),
                    "locked_path": [list(cell) for cell in locked_path] if locked_path else None,
                }}

            # Get move with timeout
            move = None
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(max(1, int(MOVE_TIMEOUT)))
                try:
                    move = current_agent.make_move(
                        game.board_copy(), dict(game.scores), game.total_passes, feedback
                    )
                finally:
                    signal.alarm(0)

            except MoveTimeoutException:
                print(f"{{agent_name}}: TIMEOUT (-{{PENALTY_FATAL}})")
                stats[f"{{p_prefix}}_timeout"] += 1
                turn_penalty += PENALTY_FATAL
                game.apply_penalty(agent_name, turn_penalty)
                game.apply_pass()
                turn_resolved = True
                break

            except Exception as e:
                print(f"{{agent_name}}: CRASH '{{str(e)[:80]}}' (-{{PENALTY_FATAL}})")
                stats[f"{{p_prefix}}_crash"] += 1
                turn_penalty += PENALTY_FATAL
                game.apply_penalty(agent_name, turn_penalty)
                game.apply_pass()
                turn_resolved = True
                break

            # Handle PASS (only valid on first attempt)
            if isinstance(move, str) and move.strip().upper() == "PASS":
                if attempt == 0:
                    print(f"{{agent_name}}: PASS")
                    stats[f"{{p_prefix}}_pass"] += 1
                    game.apply_pass()
                else:
                    print(f"{{agent_name}}: PASS during retry (invalid) (-{{PENALTY_FATAL}})")
                    stats[f"{{p_prefix}}_invalid_message"] += 1
                    turn_penalty += PENALTY_FATAL
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                turn_resolved = True
                break

            # Handle CANCEL (only valid during retries)
            if isinstance(move, str) and move.strip().upper() == "CANCEL":
                if attempt > 0:
                    # Valid CANCEL during retry
                    print(f"{{agent_name}}: CANCEL (-{{PENALTY_CANCEL}})")
                    stats[f"{{p_prefix}}_cancel"] += 1
                    turn_penalty += PENALTY_CANCEL
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                else:
                    # Invalid: CANCEL on first attempt
                    print(f"{{agent_name}}: CANCEL on first attempt (invalid) (-{{PENALTY_FATAL}})")
                    stats[f"{{p_prefix}}_invalid_message"] += 1
                    turn_penalty += PENALTY_FATAL
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                turn_resolved = True
                break

            # Locked-path retry: agent must return a word string or CANCEL
            if locked_path is not None:
                if not isinstance(move, str):
                    print(
                        f"{{agent_name}}: INVALID OUTPUT during locked-path retry "
                        f"(expected word string or 'CANCEL', "
                        f"got {{type(move).__name__}}) (-{{PENALTY_FATAL}})"
                    )
                    stats[f"{{p_prefix}}_invalid_message"] += 1
                    turn_penalty += PENALTY_FATAL
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                    turn_resolved = True
                    break

                word = move.strip()
                word_ok, word_reason, extra_letters, word_error_code = game.validate_word(word, locked_path)
                if word_ok:
                    if turn_penalty > 0:
                        game.apply_penalty(agent_name, turn_penalty)
                    stats[f"{{p_prefix}}_retry_success"] += 1
                    path_str = " -> ".join(f"({{int(r)}},{{int(c)}})" for r, c in locked_path)
                    points, cleared = game.apply_move(agent_name, locked_path, word)
                    penalty_note = f" (penalty: -{{turn_penalty}})" if turn_penalty > 0 else ""
                    print(
                        f"{{agent_name}}: path=[{{path_str}}] word='{{word}}' "
                        f"cleared={{cleared}} points=+{{points}}{{penalty_note}}"
                    )
                    game.display_board()
                    turn_resolved = True
                    break
                else:
                    turn_penalty += PENALTY_INVALID
                    stats[f"{{p_prefix}}_invalid_word"] += 1
                    failed_attempts.append({{
                        "path": [list(cell) for cell in locked_path],
                        "word": word,
                        "error_code": word_error_code,
                        "error_message": word_reason,
                    }})
                    remaining = MAX_ATTEMPTS - attempt - 1
                    print(
                        f"{{agent_name}}: INVALID WORD '{{word_reason}}' "
                        f"(-{{PENALTY_INVALID}}, {{remaining}} retries left)"
                    )
                    continue

            # Validate move structure
            if not isinstance(move, (tuple, list)) or len(move) != 2:
                print(
                    f"{{agent_name}}: INVALID OUTPUT "
                    f"(expected (path, word), 'PASS', or 'CANCEL', "
                    f"got {{type(move).__name__}}) (-{{PENALTY_FATAL}})"
                )
                stats[f"{{p_prefix}}_invalid_message"] += 1
                turn_penalty += PENALTY_FATAL
                game.apply_penalty(agent_name, turn_penalty)
                game.apply_pass()
                turn_resolved = True
                break

            path, word = move[0], move[1]

            # Validate path
            path_ok, path_reason, path_error_code = game.validate_path(path)
            if not path_ok:
                turn_penalty += PENALTY_INVALID
                stats[f"{{p_prefix}}_invalid_path"] += 1
                failed_attempts.append({{
                    "path": [list(cell) for cell in path] if isinstance(path, (list, tuple)) else str(path),
                    "word": word if isinstance(word, str) else str(word),
                    "error_code": path_error_code,
                    "error_message": path_reason,
                }})
                remaining = MAX_ATTEMPTS - attempt - 1
                print(
                    f"{{agent_name}}: INVALID PATH '{{path_reason}}' "
                    f"(-{{PENALTY_INVALID}}, {{remaining}} retries left)"
                )
                continue

            # Validate word
            word_ok, word_reason, extra_letters, word_error_code = game.validate_word(word, path)
            if not word_ok:
                turn_penalty += PENALTY_INVALID
                stats[f"{{p_prefix}}_invalid_word"] += 1
                locked_path = path
                failed_attempts.append({{
                    "path": [list(cell) for cell in path],
                    "word": word if isinstance(word, str) else str(word),
                    "error_code": word_error_code,
                    "error_message": word_reason,
                }})
                remaining = MAX_ATTEMPTS - attempt - 1
                print(
                    f"{{agent_name}}: INVALID WORD '{{word_reason}}' "
                    f"(-{{PENALTY_INVALID}}, {{remaining}} retries left)"
                )
                continue

            # Valid move — apply accumulated penalty then score
            if turn_penalty > 0:
                game.apply_penalty(agent_name, turn_penalty)
            if attempt > 0:
                stats[f"{{p_prefix}}_retry_success"] += 1
            path_str = " -> ".join(f"({{int(r)}},{{int(c)}})" for r, c in path)
            points, cleared = game.apply_move(agent_name, path, word)
            penalty_note = f" (penalty: -{{turn_penalty}})" if turn_penalty > 0 else ""
            print(
                f"{{agent_name}}: path=[{{path_str}}] word='{{word}}' "
                f"cleared={{cleared}} points=+{{points}}{{penalty_note}}"
            )
            game.display_board()
            turn_resolved = True
            break

        # Loop exhausted (3 invalid attempts, no break)
        if not turn_resolved:
            print(f"{{agent_name}}: 3 failed attempts (-{{turn_penalty}})")
            game.apply_penalty(agent_name, turn_penalty)
            game.apply_pass()

        current_agent, other_agent = other_agent, current_agent

    # Game over
    if game.total_passes >= 6:
        stats["pass_end"] += 1
        end_reason = "6 passes reached"
    else:
        stats["normal_end"] += 1
        end_reason = "No valid paths remaining"

    print()
    print(f"GAME {{game_num}} ENDED: {{end_reason}}")
    print(
        f"Scores - Agent-1: {{game.scores['Agent-1']}} | "
        f"Agent-2: {{game.scores['Agent-2']}}"
    )

    total_scores["Agent-1"] += game.scores["Agent-1"]
    total_scores["Agent-2"] += game.scores["Agent-2"]

    if game.scores["Agent-1"] > game.scores["Agent-2"]:
        winner = "Agent-1"
    elif game.scores["Agent-2"] > game.scores["Agent-1"]:
        winner = "Agent-2"
    else:
        winner = "DRAW"

    print(f"Winner: {{winner}}")
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

    print(
        f"RESULT:Agent-1={{total_scores['Agent-1']}}"
        f",Agent-2={{total_scores['Agent-2']}}"
    )
    print("--- MATCH STATISTICS ---")
    print(f"Agent-1 Invalid Paths: {{stats['p1_invalid_path']}}")
    print(f"Agent-2 Invalid Paths: {{stats['p2_invalid_path']}}")
    print(f"Agent-1 Invalid Words: {{stats['p1_invalid_word']}}")
    print(f"Agent-2 Invalid Words: {{stats['p2_invalid_word']}}")
    print(f"Agent-1 Timeouts: {{stats['p1_timeout']}}")
    print(f"Agent-2 Timeouts: {{stats['p2_timeout']}}")
    print(f"Agent-1 Crashes: {{stats['p1_crash']}}")
    print(f"Agent-2 Crashes: {{stats['p2_crash']}}")
    print(f"Agent-1 Invalid Messages: {{stats['p1_invalid_message']}}")
    print(f"Agent-2 Invalid Messages: {{stats['p2_invalid_message']}}")
    print(f"Agent-1 Passes: {{stats['p1_pass']}}")
    print(f"Agent-2 Passes: {{stats['p2_pass']}}")
    print(f"Agent-1 Cancels: {{stats['p1_cancel']}}")
    print(f"Agent-2 Cancels: {{stats['p2_cancel']}}")
    print(f"Agent-1 Retry Successes: {{stats['p1_retry_success']}}")
    print(f"Agent-2 Retry Successes: {{stats['p2_retry_success']}}")
    print(f"Normal Ends: {{stats['normal_end']}}")
    print(f"Pass Ends: {{stats['pass_end']}}")
    print(f"Total Turns: {{stats['turns']}}")


if __name__ == "__main__":
    main()
'''


# --- Human play mode ---
HUMAN_GAME_CODE = '''
import sys
import random
import string

WORDS_FILE_PATH = r"{words_file_path}"


def load_words():
    """Load dictionary: alphabetic-only words (no hyphens)."""
    try:
        with open(WORDS_FILE_PATH, 'r') as f:
            return {{
                line.strip().lower()
                for line in f
                if line.strip() and line.strip().isalpha()
            }}
    except Exception as e:
        print(f"ERROR: Could not load words from {{WORDS_FILE_PATH}}: {{e}}")
        sys.exit(1)


class WordMatrixGame:
    """Manages the WordMatrix game state and validation."""

    def __init__(self, words_set):
        self.words_set = words_set
        self.board = [
            [random.choice(string.ascii_lowercase) for _ in range(4)]
            for _ in range(4)
        ]
        self.scores = {{"Human": 0, "Bot": 0}}
        self.total_passes = 0

    def has_valid_path(self):
        """Check if any path of at least 2 adjacent non-empty cells exists."""
        for r in range(4):
            for c in range(4):
                if self.board[r][c] == "":
                    continue
                for dr, dc in [(0, 1), (1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 4 and 0 <= nc < 4 and self.board[nr][nc] != "":
                        return True
        return False

    def is_game_over(self):
        return not self.has_valid_path() or self.total_passes >= 6

    def board_copy(self):
        return [row[:] for row in self.board]

    def validate_path(self, path):
        if not isinstance(path, (list, tuple)) or len(path) < 2:
            return False, "Path must have at least 2 cells", "INVALID_PATH_TOO_SHORT"
        visited = set()
        for i, cell in enumerate(path):
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                return False, f"Cell {{i}} is not a valid (row, col) pair", "INVALID_PATH_BAD_CELL"
            r, c = int(cell[0]), int(cell[1])
            if not (0 <= r < 4 and 0 <= c < 4):
                return False, f"Cell ({{r}},{{c}}) out of bounds", "INVALID_PATH_OOB"
            if (r, c) in visited:
                return False, f"Cell ({{r}},{{c}}) visited twice", "INVALID_PATH_REVISIT"
            if self.board[r][c] == "":
                return False, f"Cell ({{r}},{{c}}) is empty", "INVALID_PATH_EMPTY"
            if i > 0:
                pr, pc = int(path[i - 1][0]), int(path[i - 1][1])
                if abs(r - pr) + abs(c - pc) != 1:
                    return False, f"Cells ({{pr}},{{pc}}) and ({{r}},{{c}}) not adjacent", "INVALID_PATH_NOT_ADJACENT"
            visited.add((r, c))
        return True, "Valid", ""

    def get_path_letters(self, path):
        return [self.board[int(r)][int(c)] for r, c in path]

    def validate_word(self, word, path):
        if not isinstance(word, str) or not word:
            return False, "Word must be a non-empty string", [], "INVALID_WORD_EMPTY"
        word = word.lower()
        path_letters = self.get_path_letters(path)
        path_len = len(path_letters)
        if len(word) > 2 * path_len:
            return False, f"Word too long ({{len(word)}} > 2*{{path_len}})", [], "INVALID_WORD_TOO_LONG"
        if len(word) < path_len:
            return False, f"Word too short ({{len(word)}} < {{path_len}})", [], "INVALID_WORD_TOO_SHORT"
        path_idx = 0
        extra_letters = []
        for ch in word:
            if path_idx < path_len and ch == path_letters[path_idx]:
                path_idx += 1
            else:
                extra_letters.append(ch)
        if path_idx < path_len:
            return False, "Path letters not found as subsequence in word", [], "INVALID_WORD_SUBSEQUENCE"
        if word not in self.words_set:
            return False, f"Word '{{word}}' not in dictionary", [], "INVALID_WORD_NOT_IN_DICT"
        return True, "Valid", extra_letters, ""

    def apply_move(self, agent_name, path, word):
        word = word.lower()
        path_letters = self.get_path_letters(path)
        path_len = len(path_letters)
        path_idx = 0
        extra_letters = []
        for ch in word:
            if path_idx < path_len and ch == path_letters[path_idx]:
                path_idx += 1
            else:
                extra_letters.append(ch)
        cell_indices = [(int(r), int(c)) for r, c in path]
        random.shuffle(cell_indices)
        for i, (r, c) in enumerate(cell_indices):
            if i < len(extra_letters):
                self.board[r][c] = extra_letters[i]
            else:
                self.board[r][c] = ""
        cleared = path_len - len(extra_letters)
        points = 10 + 10 * cleared
        self.scores[agent_name] += points
        self.total_passes = 0
        return points, cleared

    def apply_penalty(self, agent_name, amount):
        self.scores[agent_name] -= amount

    def apply_pass(self):
        self.total_passes += 1

    def display_board(self):
        print("    0  1  2  3")
        print("   -----------")
        for r in range(4):
            row_str = " ".join(
                f" {{self.board[r][c]}}" if self.board[r][c] else " ."
                for c in range(4)
            )
            print(f"{{r}} |{{row_str}}")
        print()


class HumanAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, board, scores, total_passes=0, feedback=None):
        print(f"\\nYour turn ({{self.name}})")
        print(f"Scores: {{scores}}")
        print(f"Passes remaining: {{6 - total_passes}}")

        if feedback:
            print()
            print(f"  Last error: [{{feedback['error_code']}}] {{feedback['error_message']}}")
            for i, fa in enumerate(feedback["failed_attempts"]):
                print(f"  Attempt {{i + 1}}: path={{fa['path']}} word='{{fa['word']}}' -> {{fa['error_code']}}")

        print()

        # Display board
        print("    0  1  2  3")
        print("   -----------")
        for r in range(4):
            row_str = " ".join(
                f" {{board[r][c]}}" if board[r][c] else " ."
                for c in range(4)
            )
            print(f"{{r}} |{{row_str}}")
        print()

        # Locked-path retry: path is fixed, only prompt for word
        if feedback and feedback.get("locked_path"):
            lp = feedback["locked_path"]
            path_letters = [board[int(r)][int(c)] for r, c in lp if 0 <= int(r) < 4 and 0 <= int(c) < 4 and board[int(r)][int(c)]]
            path_str = " -> ".join(f"({{int(r)}},{{int(c)}})" for r, c in lp)
            print(f"  Path LOCKED: [{{path_str}}]")
            print(f"  Path letters: {{path_letters}}")
            print()
            word_input = input("Enter word for locked path (or CANCEL): ").strip()
            if word_input.upper() == "CANCEL":
                return "CANCEL"
            return word_input.lower()

        if feedback:
            path_input = input("Enter path (e.g., '0,0 0,1 1,1') or CANCEL: ").strip()
        else:
            path_input = input("Enter path (e.g., '0,0 0,1 1,1') or PASS: ").strip()

        if path_input.upper() == "PASS":
            return "PASS"

        if path_input.upper() == "CANCEL":
            return "CANCEL"

        # Parse path — format failures return invalid move for game engine to penalize
        try:
            cells = path_input.split()
            path = []
            for cell_str in cells:
                parts = cell_str.split(",")
                path.append((int(parts[0]), int(parts[1])))
        except (ValueError, IndexError):
            print("Invalid format. Use 'row,col row,col ...' (e.g., '0,0 0,1 1,1')")
            return ([], "")

        # Show path letters (raw, pre-validation)
        path_letters = [board[r][c] for r, c in path if 0 <= r < 4 and 0 <= c < 4 and board[r][c]]
        print(f"Path letters: {{path_letters}}")

        word_input = input("Enter word (or CANCEL): ").strip()

        if word_input.upper() == "CANCEL":
            return "CANCEL"

        return (path, word_input.lower())


class BotAgent:
    """Simple bot that always passes."""
    def __init__(self, name):
        self.name = name

    def make_move(self, board, scores, total_passes=0, feedback=None):
        return "PASS"


def main():
    print("=== WordMatrixGame - Human Play Mode ===")
    print("Loading dictionary...")
    words_set = load_words()
    print(f"Dictionary loaded: {{len(words_set)}} words")
    print()

    game = WordMatrixGame(words_set)
    human = HumanAgent("Human")
    bot = BotAgent("Bot")

    current_agent = human
    other_agent = bot

    game.display_board()

    MAX_ATTEMPTS = 3
    PENALTY_INVALID = 25
    PENALTY_CANCEL = 10
    PENALTY_FATAL = 50

    while not game.is_game_over():
        agent_name = current_agent.name

        if isinstance(current_agent, BotAgent):
            print(f"{{agent_name}}: PASS")
            game.apply_pass()
            print(f"Scores: {{game.scores}}")
            current_agent, other_agent = other_agent, current_agent
            continue

        failed_attempts = []
        turn_penalty = 0
        turn_resolved = False
        locked_path = None

        for attempt in range(MAX_ATTEMPTS):
            feedback = None
            if attempt > 0:
                feedback = {{
                    "error_code": failed_attempts[-1]["error_code"],
                    "error_message": failed_attempts[-1]["error_message"],
                    "failed_attempts": list(failed_attempts),
                    "locked_path": [list(cell) for cell in locked_path] if locked_path else None,
                }}

            print(f"\\n--- Attempt {{attempt + 1}}/{{MAX_ATTEMPTS}} | Penalty so far: -{{turn_penalty}} ---")

            move = current_agent.make_move(
                game.board_copy(), dict(game.scores), game.total_passes, feedback
            )

            # Handle PASS (only valid on first attempt)
            if isinstance(move, str) and move.strip().upper() == "PASS":
                if attempt == 0:
                    print(f"{{agent_name}}: PASS")
                    game.apply_pass()
                else:
                    print(f"{{agent_name}}: PASS during retry (invalid) (-{{PENALTY_FATAL}})")
                    turn_penalty += PENALTY_FATAL
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                print(f"Scores: {{game.scores}}")
                turn_resolved = True
                break

            # Handle CANCEL (only valid during retries)
            if isinstance(move, str) and move.strip().upper() == "CANCEL":
                if attempt > 0:
                    # Valid CANCEL during retry
                    turn_penalty += PENALTY_CANCEL
                    print(f"{{agent_name}}: CANCEL (-{{PENALTY_CANCEL}})")
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                else:
                    # Invalid: CANCEL on first attempt
                    print(f"{{agent_name}}: CANCEL on first attempt (invalid) (-{{PENALTY_FATAL}})")
                    turn_penalty += PENALTY_FATAL
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                print(f"Scores: {{game.scores}}")
                turn_resolved = True
                break

            # Locked-path retry: agent must return a word string or CANCEL
            if locked_path is not None:
                if not isinstance(move, str):
                    print(
                        f"{{agent_name}}: INVALID OUTPUT during locked-path retry "
                        f"(expected word string or 'CANCEL', "
                        f"got {{type(move).__name__}}) (-{{PENALTY_FATAL}})"
                    )
                    turn_penalty += PENALTY_FATAL
                    game.apply_penalty(agent_name, turn_penalty)
                    game.apply_pass()
                    print(f"Scores: {{game.scores}}")
                    turn_resolved = True
                    break

                word = move.strip()
                word_ok, word_reason, extra_letters, word_error_code = game.validate_word(word, locked_path)
                if word_ok:
                    if turn_penalty > 0:
                        game.apply_penalty(agent_name, turn_penalty)
                    path_str = " -> ".join(f"({{int(r)}},{{int(c)}})" for r, c in locked_path)
                    points, cleared = game.apply_move(agent_name, locked_path, word)
                    penalty_note = f" (penalty: -{{turn_penalty}})" if turn_penalty > 0 else ""
                    print(
                        f"\\n{{agent_name}}: path=[{{path_str}}] word='{{word}}' "
                        f"cleared={{cleared}} points=+{{points}}{{penalty_note}}"
                    )
                    print(f"Scores: {{game.scores}}")
                    print()
                    game.display_board()
                    turn_resolved = True
                    break
                else:
                    turn_penalty += PENALTY_INVALID
                    failed_attempts.append({{
                        "path": [list(cell) for cell in locked_path],
                        "word": word,
                        "error_code": word_error_code,
                        "error_message": word_reason,
                    }})
                    remaining = MAX_ATTEMPTS - attempt - 1
                    print(
                        f"INVALID WORD: {{word_reason}} "
                        f"(-{{PENALTY_INVALID}}, {{remaining}} retries left)"
                    )
                    print(f"Scores: {{game.scores}}")
                    continue

            # Validate move structure
            if not isinstance(move, (tuple, list)) or len(move) != 2:
                print(
                    f"{{agent_name}}: INVALID OUTPUT "
                    f"(expected (path, word), 'PASS', or 'CANCEL', "
                    f"got {{type(move).__name__}}) (-{{PENALTY_FATAL}})"
                )
                turn_penalty += PENALTY_FATAL
                game.apply_penalty(agent_name, turn_penalty)
                game.apply_pass()
                print(f"Scores: {{game.scores}}")
                turn_resolved = True
                break

            path, word = move[0], move[1]

            # Validate path
            path_ok, path_reason, path_error_code = game.validate_path(path)
            if not path_ok:
                turn_penalty += PENALTY_INVALID
                failed_attempts.append({{
                    "path": [list(cell) for cell in path],
                    "word": word if isinstance(word, str) else str(word),
                    "error_code": path_error_code,
                    "error_message": path_reason,
                }})
                remaining = MAX_ATTEMPTS - attempt - 1
                print(
                    f"INVALID PATH: {{path_reason}} "
                    f"(-{{PENALTY_INVALID}}, {{remaining}} retries left)"
                )
                print(f"Scores: {{game.scores}}")
                continue

            # Validate word
            word_ok, word_reason, extra_letters, word_error_code = game.validate_word(word, path)
            if not word_ok:
                turn_penalty += PENALTY_INVALID
                locked_path = path
                failed_attempts.append({{
                    "path": [list(cell) for cell in path],
                    "word": word if isinstance(word, str) else str(word),
                    "error_code": word_error_code,
                    "error_message": word_reason,
                }})
                remaining = MAX_ATTEMPTS - attempt - 1
                print(
                    f"INVALID WORD: {{word_reason}} "
                    f"(-{{PENALTY_INVALID}}, {{remaining}} retries left)"
                )
                print(f"Scores: {{game.scores}}")
                continue

            # Valid move — apply accumulated penalty then score
            if turn_penalty > 0:
                game.apply_penalty(agent_name, turn_penalty)
            path_str = " -> ".join(f"({{int(r)}},{{int(c)}})" for r, c in path)
            points, cleared = game.apply_move(agent_name, path, word)
            penalty_note = f" (penalty: -{{turn_penalty}})" if turn_penalty > 0 else ""
            print(
                f"\\n{{agent_name}}: path=[{{path_str}}] word='{{word}}' "
                f"cleared={{cleared}} points=+{{points}}{{penalty_note}}"
            )
            print(f"Scores: {{game.scores}}")
            print()
            game.display_board()
            turn_resolved = True
            break

        # Loop exhausted (3 invalid attempts, no break)
        if not turn_resolved:
            print(f"{{agent_name}}: 3 failed attempts (-{{turn_penalty}})")
            game.apply_penalty(agent_name, turn_penalty)
            game.apply_pass()
            print(f"Scores: {{game.scores}}")

        current_agent, other_agent = other_agent, current_agent

    print()
    print("=== GAME OVER ===")
    print(f"Final Scores: {{game.scores}}")
    if game.scores["Human"] > game.scores["Bot"]:
        print("You win!")
    elif game.scores["Bot"] > game.scores["Human"]:
        print("Bot wins!")
    else:
        print("Draw!")


if __name__ == "__main__":
    main()
'''


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


def load_stored_agent(
    model_folder: str, game: str, run: int, agent_idx: int
) -> tuple[str, str]:
    """Load agent code from a stored file and extract ONLY the agent class."""
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

        if stripped.startswith("class WordMatrixAgent"):
            class_start_idx = i
            break

        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped and "time" not in stripped:
                imports.append(stripped)

    if class_start_idx is None:
        logger.error("No WordMatrixAgent class found in %s", agent_file)
        return "", ""

    # Extract ONLY the WordMatrixAgent class
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

    # Rename WordMatrixAgent to WordMatrixAgent_{agent_idx}
    agent_code = re.sub(
        r"\bWordMatrixAgent\b", f"WordMatrixAgent_{agent_idx}", agent_code
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
    words_file_path: str,
    move_timeout: float,
    agent1_info: str,
    agent2_info: str,
) -> str:
    """Build the complete game code with both agent implementations."""
    return GAME_CODE_TEMPLATE.format(
        num_games=num_games,
        words_file_path=words_file_path,
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
        tempfile.gettempdir(), f"wordmatrix_match_{match_id}_{temp_id}.py"
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
            r"RESULT:Agent-1=([-\d.]+),Agent-2=([-\d.]+)", result.stdout
        )

        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            log_lines = []
            for line in result.stdout.splitlines():
                if line.startswith((
                    "Agent-1:", "Agent-2:", "GAME ", "Reason:",
                    "Scores", "Winner:", "Result:", "Running Total",
                    "==========",
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
    parser = argparse.ArgumentParser(description="Run WordMatrixGame matches")
    parser.add_argument(
        "--agent", nargs="+",
        help="Agent specs: model1[:run1:run2] model2[:run3:run4]",
    )
    parser.add_argument(
        "--human", action="store_true",
        help="Play interactively against a bot",
    )
    args = parser.parse_args()

    # Human play mode
    if args.human:
        human_code = HUMAN_GAME_CODE.format(words_file_path=str(WORDS_FILE))
        temp_id = uuid.uuid4().hex[:8]
        temp_file = os.path.join(
            tempfile.gettempdir(), f"wordmatrix_human_{temp_id}.py"
        )
        try:
            with open(temp_file, "w") as f:
                f.write(human_code)
            subprocess.run(
                ["python", temp_file],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return

    # Agent match mode
    if not args.agent or len(args.agent) != 2:
        print("ERROR: Need exactly 2 agent specifications.")
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
    print("WORDMATRIX MATCH - STORED AGENTS")
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
            print(f"  FAILED to load match {i + 1}")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        agent1_info = f"{folder1} (Run {run1})"
        agent2_info = f"{folder2} (Run {run2})"

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_GAMES_PER_MATCH,
            str(WORDS_FILE), MOVE_TIME_LIMIT,
            agent1_info, agent2_info,
        )

        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)

    total1, total2 = 0.0, 0.0

    with open(log_f, "w") as f:
        f.write(f"WordMatrix Match - {ts}\n")
        f.write("=" * 60 + "\n\n")

        for result in sorted(results, key=lambda x: x["match_id"]):
            match_id = result["match_id"]
            if result["success"]:
                s1, s2 = result["agent1_score"], result["agent2_score"]
                total1 += s1
                total2 += s2
                status = f"Result: {s1:.0f} - {s2:.0f}"
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

    print("\nFINAL RESULTS (Total Score):")
    print(f"  {folder1}: {total1:.0f}")
    print(f"  {folder2}: {total2:.0f}")
    print(f"\nLogs saved to: {log_f}")


if __name__ == "__main__":
    asyncio.run(main_async())
