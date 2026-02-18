"""
WordMatrix Match Runner: Orchestrates head-to-head matches for A6-WordMatrixGame.

Loads pre-generated agents from agents/, matches them in pairs, runs games via
subprocess, and reports win/loss/draw statistics with scoreboard integration.
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

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / "word_matrix"
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / "A6-scoreboard.txt"
AGENTS_DIR = BASE_DIR / "agents"

GAME_NAME = "A6-WordMatrixGame"
WORDS_FILE = BASE_DIR / "game_scripts" / "words_small.txt"

# Penalty for invalid move / crash / timeout (no random fallback for this game)
INVALID_PENALTY = 10

# Max tie-breaker score used for forfeit games
FORFEIT_SCORE = 12

MODE_TITLES = {
    "humanvsbot": "Human vs Random Bot",
    "humanvshuman": "Human vs Human",
    "humanvsagent": "Human vs Stored Agent",
}


# ============================================================
# Game engine code (WordMatrixGame class, board display, load_words)
# ============================================================
GAME_ENGINE_CODE = r'''
WORDS_FILE_PATH = r"{words_file_path}"
_WORDS_CACHE = None


def load_words():
    """Load dictionary from words_small.txt (cached per process)."""
    global _WORDS_CACHE
    if _WORDS_CACHE is not None:
        return _WORDS_CACHE
    try:
        with open(WORDS_FILE_PATH, 'r') as f:
            _WORDS_CACHE = {
                line.strip().lower()
                for line in f
                if line.strip() and line.strip().isalpha()
            }
    except Exception as e:
        print(f"ERROR: Could not load words from {WORDS_FILE_PATH}: {e}")
        sys.exit(1)
    return _WORDS_CACHE


class WordMatrixGame:
    """Manages the WordMatrix game state and validation."""

    def __init__(self, words_set):
        self.words_set = words_set
        self.board = [
            [random.choice(string.ascii_lowercase) for _ in range(4)]
            for _ in range(4)
        ]
        self.scores = {"Agent-1": 0, "Agent-2": 0}
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
        """Validate a path. Returns (ok, reason)."""
        if not isinstance(path, (list, tuple)) or len(path) < 2:
            return False, "Path must be a list/tuple of at least 2 cells"

        visited = set()
        for i, cell in enumerate(path):
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                return False, f"Cell {i} is not a valid (row, col) pair"

            try:
                r, c = int(cell[0]), int(cell[1])
            except (ValueError, TypeError):
                return False, f"Cell {i} has non-integer coordinates"

            if not (0 <= r < 4 and 0 <= c < 4):
                return False, f"Cell ({r},{c}) is out of bounds"

            if (r, c) in visited:
                return False, f"Cell ({r},{c}) visited twice"

            if self.board[r][c] == "":
                return False, f"Cell ({r},{c}) is empty"

            if i > 0:
                pr, pc = int(path[i - 1][0]), int(path[i - 1][1])
                if abs(r - pr) + abs(c - pc) != 1:
                    return False, f"Cells ({pr},{pc}) and ({r},{c}) are not adjacent"

            visited.add((r, c))

        return True, "Valid"

    def get_path_letters(self, path):
        """Extract letters along the path."""
        return [self.board[int(r)][int(c)] for r, c in path]

    def validate_word(self, word, path):
        """Validate a word against a path. Returns (ok, reason, extra_letters)."""
        if not isinstance(word, str) or not word:
            return False, "Word must be a non-empty string", []

        word = word.lower()
        path_letters = self.get_path_letters(path)
        path_len = len(path_letters)

        if len(word) > 2 * path_len:
            return False, f"Word length {len(word)} exceeds 2 * path length {path_len}", []

        if len(word) < path_len:
            return False, f"Word length {len(word)} less than path length {path_len}", []

        # Subsequence check
        path_idx = 0
        extra_letters = []
        for ch in word:
            if path_idx < path_len and ch == path_letters[path_idx]:
                path_idx += 1
            else:
                extra_letters.append(ch)

        if path_idx < path_len:
            return False, f"Path letters not found as subsequence in word (matched {path_idx}/{path_len})", []

        if word not in self.words_set:
            return False, f"Word '{word}' not in dictionary", []

        return True, "Valid", extra_letters

    def apply_move(self, agent_name, path, word):
        """Apply a valid move: update board and score. Returns (points, cleared_cells)."""
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
        """Apply a point penalty to the given agent."""
        self.scores[agent_name] -= amount

    def apply_pass(self):
        """Record a pass (no point change)."""
        self.total_passes += 1

    def display_board(self):
        """Print the board in a readable format (no BOARD: prefix, for human modes)."""
        print("    0  1  2  3")
        print("   -----------")
        for r in range(4):
            row_str = " ".join(
                f" {self.board[r][c]}" if self.board[r][c] else " ."
                for c in range(4)
            )
            print(f"{r} |{row_str}")

    def display_board_log(self):
        """Print the board with BOARD: prefix for log filtering."""
        print("BOARD:     0  1  2  3")
        print("BOARD:    -----------")
        for r in range(4):
            row_str = " ".join(
                f" {self.board[r][c]}" if self.board[r][c] else " ."
                for c in range(4)
            )
            print(f"BOARD: {r} |{row_str}")


class RandomAgent:
    """Simple bot that always passes (no meaningful random move for word games)."""
    def __init__(self, name):
        self.name = name

    def make_move(self, board, scores, total_passes):
        return "PASS"


class HumanAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, board, scores, total_passes):
        print(f"\nYour turn ({self.name})")
        print(f"Scores: {scores}")
        print(f"Passes remaining: {6 - total_passes}")
        print()

        print("    0  1  2  3")
        print("   -----------")
        for r in range(4):
            row_str = " ".join(
                f" {board[r][c]}" if board[r][c] else " ."
                for c in range(4)
            )
            print(f"{r} |{row_str}")
        print()

        path_input = input("Enter path (e.g., '0,0 0,1 1,1') or PASS: ").strip()

        if path_input.upper() == "PASS":
            return "PASS"

        try:
            cells = path_input.split()
            path = []
            for cell_str in cells:
                parts = cell_str.split(",")
                path.append((int(parts[0]), int(parts[1])))
        except (ValueError, IndexError):
            print("Invalid format. Use 'row,col row,col ...' (e.g., '0,0 0,1 1,1')")
            return ([], "")

        path_letters = [board[r][c] for r, c in path if 0 <= r < 4 and 0 <= c < 4 and board[r][c]]
        print(f"Path letters: {path_letters}")

        word_input = input("Enter word: ").strip()
        return (path, word_input.lower())
'''


# ============================================================
# Match runner code (play_game, main, stats, output)
# ============================================================
MATCH_RUNNER_CODE = r'''
class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

INVALID_PENALTY = 10
FORFEIT_SCORE = {forfeit_score}


def play_game(game_num, match_stats):
    """Play a single game and update match_stats. Returns winner name or 'DRAW'."""
    words_set = load_words()
    game = WordMatrixGame(words_set)

    # Determine agent classes based on game mode
    if GAME_MODE == "humanvsbot":
        class_1, class_2 = HumanAgent, RandomAgent
    elif GAME_MODE == "humanvshuman":
        class_1, class_2 = HumanAgent, HumanAgent
    elif GAME_MODE == "humanvsagent":
        class_1, class_2 = HumanAgent, WordMatrixAgent_1
    else:
        class_1, class_2 = WordMatrixAgent_1, WordMatrixAgent_2

    # Determine agent labels and starting order
    # Agent-1 is always class_1 (Model 1), Agent-2 is always class_2 (Model 2)
    # Turn order alternates based on game_num
    if game_num % 2 == 1:
        a1_class, a2_class = class_1, class_2
        turn_order = ["Agent-1", "Agent-2"]
    else:
        a1_class, a2_class = class_1, class_2
        turn_order = ["Agent-2", "Agent-1"]

    print()
    print("=" * 60)
    print(f"Game {game_num}")
    print(f"Agent-1: {AGENT1_NAME}")
    print(f"Agent-2: {AGENT2_NAME}")
    print(f"Starting Player: {turn_order[0]}")
    print("-" * 60)

    # --- Initialize agents (other_crash on failure = forfeit) ---
    try:
        agent1 = class_1("Agent-1")
    except Exception as e:
        print(f"Agent-1 init crash: {e}")
        match_stats["Agent-1"]["other_crash"] += 1
        match_stats["Agent-2"]["wins"] += 1
        match_stats["Agent-2"]["points"] += 3
        match_stats["Agent-2"]["score"] += FORFEIT_SCORE
        match_stats["Agent-1"]["losses"] += 1
        match_stats["Agent-1"]["score"] -= FORFEIT_SCORE

        print("Final Position: N/A (initialization crash)")
        print("-" * 40)
        print("Final Result: Agent-2 wins. (opponent crashed)")
        print("-" * 40)
        print("Points:")
        print("Agent-1: 0")
        print("Agent-2: 3")
        print("-" * 40)
        print("Scores:")
        print(f"Agent-2: {FORFEIT_SCORE}")
        print(f"Agent-1: -{FORFEIT_SCORE}")
        print("=" * 60)
        return "Agent-2"

    try:
        agent2 = class_2("Agent-2")
    except Exception as e:
        print(f"Agent-2 init crash: {e}")
        match_stats["Agent-2"]["other_crash"] += 1
        match_stats["Agent-1"]["wins"] += 1
        match_stats["Agent-1"]["points"] += 3
        match_stats["Agent-1"]["score"] += FORFEIT_SCORE
        match_stats["Agent-2"]["losses"] += 1
        match_stats["Agent-2"]["score"] -= FORFEIT_SCORE

        print("Final Position: N/A (initialization crash)")
        print("-" * 40)
        print("Final Result: Agent-1 wins. (opponent crashed)")
        print("-" * 40)
        print("Points:")
        print("Agent-1: 3")
        print("Agent-2: 0")
        print("-" * 40)
        print("Scores:")
        print(f"Agent-1: {FORFEIT_SCORE}")
        print(f"Agent-2: -{FORFEIT_SCORE}")
        print("=" * 60)
        return "Agent-1"

    agents = {"Agent-1": agent1, "Agent-2": agent2}
    current_idx = 0

    game.display_board()

    # --- Game loop ---
    while not game.is_game_over():
        agent_name = turn_order[current_idx]
        current_agent = agents[agent_name]

        move = None
        error_type = None

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                move = current_agent.make_move(
                    game.board_copy(), dict(game.scores), game.total_passes
                )
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            match_stats[agent_name]["timeout"] += 1
            error_type = "timeout"
            print(f"{agent_name}: TIMEOUT (-{INVALID_PENALTY})")
        except Exception as e:
            match_stats[agent_name]["make_move_crash"] += 1
            error_type = "crash"
            print(f"{agent_name}: CRASH '{str(e)[:80]}' (-{INVALID_PENALTY})")

        if error_type is not None:
            game.apply_penalty(agent_name, INVALID_PENALTY)
            game.apply_pass()
            current_idx = 1 - current_idx
            continue

        # Handle PASS
        if isinstance(move, str) and move.strip().upper() == "PASS":
            print(f"{agent_name}: PASS")
            game.apply_pass()
            current_idx = 1 - current_idx
            continue

        # Validate move structure
        if not isinstance(move, (tuple, list)) or len(move) != 2:
            print(f"{agent_name}: INVALID OUTPUT (expected (path, word) or 'PASS', got {type(move).__name__}) (-{INVALID_PENALTY})")
            match_stats[agent_name]["invalid"] += 1
            game.apply_penalty(agent_name, INVALID_PENALTY)
            game.apply_pass()
            current_idx = 1 - current_idx
            continue

        path, word = move[0], move[1]

        # Validate path
        path_ok, path_reason = game.validate_path(path)
        if not path_ok:
            print(f"{agent_name}: INVALID PATH '{path_reason}' (-{INVALID_PENALTY})")
            match_stats[agent_name]["invalid"] += 1
            game.apply_penalty(agent_name, INVALID_PENALTY)
            game.apply_pass()
            current_idx = 1 - current_idx
            continue

        # Validate word
        word_ok, word_reason, extra_letters = game.validate_word(word, path)
        if not word_ok:
            print(f"{agent_name}: INVALID WORD '{word_reason}' (-{INVALID_PENALTY})")
            match_stats[agent_name]["invalid"] += 1
            game.apply_penalty(agent_name, INVALID_PENALTY)
            game.apply_pass()
            current_idx = 1 - current_idx
            continue

        # Valid move
        path_str = " -> ".join(f"({int(r)},{int(c)})" for r, c in path)
        points, cleared = game.apply_move(agent_name, path, word)
        print(f"{agent_name}: path=[{path_str}] word='{word}' cleared={cleared} points=+{points}")
        game.display_board()
        current_idx = 1 - current_idx

    # --- Game over ---
    if game.total_passes >= 6:
        end_reason = "6 consecutive passes reached"
    else:
        end_reason = "No valid paths remaining"

    # Determine winner
    s1, s2 = game.scores["Agent-1"], game.scores["Agent-2"]

    print("Final Position:")
    game.display_board_log()
    print(f"Scores: Agent-1={s1} Agent-2={s2}")
    print("-" * 40)

    if s1 > s2:
        winner = "Agent-1"
        loser = "Agent-2"
        game_score = abs(s1 - s2)
        print(f"Final Result: Agent-1 wins. ({end_reason})")
        print("-" * 40)
        print("Points:")
        print("Agent-1: 3")
        print("Agent-2: 0")
        print("-" * 40)
        print("Scores:")
        print(f"Agent-1: {game_score}")
        print(f"Agent-2: -{game_score}")

        match_stats["Agent-1"]["wins"] += 1
        match_stats["Agent-1"]["points"] += 3
        match_stats["Agent-1"]["score"] += game_score
        match_stats["Agent-2"]["losses"] += 1
        match_stats["Agent-2"]["score"] -= game_score

    elif s2 > s1:
        winner = "Agent-2"
        loser = "Agent-1"
        game_score = abs(s2 - s1)
        print(f"Final Result: Agent-2 wins. ({end_reason})")
        print("-" * 40)
        print("Points:")
        print("Agent-1: 0")
        print("Agent-2: 3")
        print("-" * 40)
        print("Scores:")
        print(f"Agent-1: -{game_score}")
        print(f"Agent-2: {game_score}")

        match_stats["Agent-2"]["wins"] += 1
        match_stats["Agent-2"]["points"] += 3
        match_stats["Agent-2"]["score"] += game_score
        match_stats["Agent-1"]["losses"] += 1
        match_stats["Agent-1"]["score"] -= game_score

    else:
        winner = "DRAW"
        print(f"Final Result: Draw. ({end_reason})")
        print("-" * 40)
        print("Points:")
        print("Agent-1: 1")
        print("Agent-2: 1")
        print("-" * 40)
        print("Scores:")
        print("Agent-1: 0")
        print("Agent-2: 0")

        match_stats["Agent-1"]["draws"] += 1
        match_stats["Agent-1"]["points"] += 1
        match_stats["Agent-2"]["draws"] += 1
        match_stats["Agent-2"]["points"] += 1

    print("=" * 60)
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
    print(f"Agent-1: {AGENT1_NAME}")
    print(f"Agent-2: {AGENT2_NAME}")
    print(f"RESULT:Agent-1={float(match_stats['Agent-1']['points'])},Agent-2={float(match_stats['Agent-2']['points'])}")
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
    print("-" * 60)


if __name__ == "__main__":
    main()
'''


# ============================================================
# Outer layer: agent loading, subprocess orchestration, logging
# ============================================================

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
    move_timeout: float,
    words_file_path: str,
    forfeit_score: int = FORFEIT_SCORE,
    game_mode: str = "",
    agent1_name: str = "Agent-1",
    agent2_name: str = "Agent-2",
) -> str:
    """Build the complete game code by concatenating header, agents, engine, and runner."""
    header = (
        "import sys\n"
        "import random\n"
        "import signal\n"
        "import string\n"
        "\n"
        f"MOVE_TIMEOUT = {move_timeout}\n"
        f"NUM_GAMES = {num_games}\n"
        f'GAME_MODE = "{game_mode}"\n'
        f'AGENT1_NAME = "{agent1_name}"\n'
        f'AGENT2_NAME = "{agent2_name}"\n'
    )

    engine = GAME_ENGINE_CODE.replace("{words_file_path}", str(words_file_path))
    runner = MATCH_RUNNER_CODE.replace("{forfeit_score}", str(forfeit_score))

    return "\n\n".join([
        header,
        extra_imports,
        agent1_code,
        agent2_code,
        engine,
        runner,
    ])


def run_match(
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = 900
) -> dict:
    """Execute a match subprocess, parse results, and return structured dict."""
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

        # Parse structured output lines
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

            # Log filtering: keep only meaningful lines
            log_lines = []
            for line in result.stdout.splitlines():
                stripped = line.lstrip()
                if stripped.startswith((
                    "Agent-1:", "Agent-2:", "Game ",
                    "=====", "----",
                    "Final", "Scores:", "Points:",
                    "BOARD:",
                    "CRASH", "RESULT", "SCORE", "WINS", "DRAWS", "STATS",
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


def run_match_human(game_code: str) -> None:
    """Run a match in human mode (interactive, stdin/stdout passthrough)."""
    temp_file = os.path.join(
        tempfile.gettempdir(), f"wordmatrix_human_{uuid.uuid4().hex[:8]}.py"
    )
    try:
        with open(temp_file, "w") as f:
            f.write(game_code)
        subprocess.run(
            ["python", temp_file],
            stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
        )
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def run_match_async(
    game_code: str, match_id: int, run_ids: tuple[int, int]
) -> dict:
    """Run a match in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    """Main entry point for all match modes."""
    parser = argparse.ArgumentParser(
        description="Run WordMatrixGame matches between stored AI agents"
    )
    parser.add_argument(
        "--agent", nargs="+",
        help="Agent specs: model1[:run1:run2] model2[:run3:run4]",
    )
    human_group = parser.add_mutually_exclusive_group()
    human_group.add_argument(
        "--humanvsbot", action="store_true",
        help="Play interactively against a bot that always passes",
    )
    human_group.add_argument(
        "--humanvshuman", action="store_true",
        help="Two humans play at the same terminal",
    )
    human_group.add_argument(
        "--humanvsagent", action="store_true",
        help="Play against a stored agent (requires --agent with 1 spec)",
    )
    parser.add_argument(
        "--update-scoreboard", action="store_true",
        help="Write results to scoreboard (default: off; enabled by matchmaker)",
    )
    args = parser.parse_args()

    # --- Human play modes ---
    human_mode = None
    if args.humanvsbot:
        human_mode = "humanvsbot"
    elif args.humanvshuman:
        human_mode = "humanvshuman"
    elif args.humanvsagent:
        human_mode = "humanvsagent"

    if human_mode:
        print("\n" + "=" * 60)
        mode_title = MODE_TITLES.get(human_mode, human_mode)
        print(f"WORD MATRIX GAME - {mode_title}")
        print("=" * 60)

        agent1_code = ""
        agent2_code = ""
        agent_imports = ""

        if human_mode == "humanvsagent":
            if not args.agent or len(args.agent) != 1:
                print("ERROR: --humanvsagent requires exactly 1 --agent spec.")
                print("Example: --humanvsagent --agent mistral:1")
                sys.exit(1)

            model_pattern, runs = parse_agent_spec(args.agent[0])
            folder = find_model_folder(model_pattern)
            if not folder:
                sys.exit(1)
            if not runs:
                runs = get_available_runs(folder, GAME_NAME)
            if not runs:
                print(f"ERROR: No runs found for {folder}/{GAME_NAME}")
                sys.exit(1)

            agent_code, agent_imports = load_stored_agent(
                folder, GAME_NAME, runs[0], 1
            )
            if not agent_code:
                print(f"ERROR: Failed to load agent from {folder}")
                sys.exit(1)
            agent1_code = agent_code
        elif args.agent:
            print("ERROR: --agent is not used with --humanvsbot or --humanvshuman.")
            sys.exit(1)

        game_code = build_game_code(
            agent1_code=agent1_code,
            agent2_code=agent2_code,
            extra_imports=agent_imports,
            num_games=1,
            move_timeout=99999,
            words_file_path=str(WORDS_FILE),
            game_mode=human_mode,
            agent1_name="Human",
            agent2_name="Bot" if human_mode == "humanvsbot" else "Agent",
        )
        run_match_human(game_code)
        return

    # --- Agent vs Agent mode ---
    if not args.agent or len(args.agent) != 2:
        print("ERROR: Need exactly 2 agent specifications.")
        print("Example: --agent mistral:1:2 gpt-5-mini:1:4")
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
    if len(runs1) != len(runs2):
        logger.warning(
            "Number of runs for %s (%d) and %s (%d) don't match. Using first %d.",
            folder1, len(runs1), folder2, len(runs2), num_matches,
        )

    runs1 = runs1[:num_matches]
    runs2 = runs2[:num_matches]

    print("\n" + "=" * 60)
    print("WORD MATRIX MATCH - STORED AGENTS")
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
            print(f"  FAILED to load match {i + 1}: Could not load agent code.")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        game_code = build_game_code(
            code1, code2, extra_imports,
            NUM_GAMES_PER_MATCH, MOVE_TIME_LIMIT,
            str(WORDS_FILE),
            agent1_name=f"{folder1}:{run1}", agent2_name=f"{folder2}:{run2}",
        )

        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)

    # Process results and write individual log files (one per match)
    total1, total2 = 0.0, 0.0
    total_pts1, total_pts2 = 0, 0

    for result in sorted(results, key=lambda x: x["match_id"]):
        match_id = result["match_id"]
        run1 = result["agent1_run_id"]
        run2 = result["agent2_run_id"]
        p1, p2 = 0, 0

        if result["success"]:
            s1, s2 = result["agent1_score"], result["agent2_score"]
            p1 = result.get("agent1_points", 0)
            p2 = result.get("agent2_points", 0)
            total1 += s1
            total2 += s2
            total_pts1 += p1
            total_pts2 += p2

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_f = RESULTS_DIR / f"{ts}_{folder1}:{run1}_vs_{folder2}:{run2}_match.txt"

        with open(log_f, "w") as f:
            f.write("Match Contenders:\n")
            f.write(f"{folder1}:{run1}\n")
            f.write(f"{folder2}:{run2}\n\n")

            if result["success"]:
                f.write("Result:\n")
                f.write(f"{folder1}:{run1} : Pts: {p1} - Score: {s1:.1f}\n")
                f.write(f"{folder2}:{run2} : Pts: {p2} - Score: {s2:.1f}\n\n")

                game_log = result.get("log", "")
                if game_log:
                    f.write(f"{game_log}\n")
                if result.get("stats_block"):
                    f.write(f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n")
                f.write("\n" + "-" * 60 + "\n")
            else:
                f.write(f"FAILED: {result.get('error', 'Unknown')}\n")

        print(f"Match {match_id} Completed. Pts {p1}-{p2}")

    # Update global scoreboard
    for result in results:
        if not result["success"]:
            continue

        run1 = result["agent1_run_id"]
        run2 = result["agent2_run_id"]
        agent1_key = f"{folder1}:{run1}"
        agent2_key = f"{folder2}:{run2}"

        a1_wins = result.get("agent1_wins", 0)
        a2_wins = result.get("agent2_wins", 0)
        match_draws = result.get("draws", 0)

        if args.update_scoreboard:
            update_scoreboard(
                SCOREBOARD_PATH, agent1_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=a1_wins, losses=a2_wins, draws=match_draws,
                score=result["agent1_score"],
                points=result.get("agent1_points", 0),
            )
            update_scoreboard(
                SCOREBOARD_PATH, agent2_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=a2_wins, losses=a1_wins, draws=match_draws,
                score=result["agent2_score"],
                points=result.get("agent2_points", 0),
            )

    runs1_str = ",".join(str(r) for r in runs1)
    runs2_str = ",".join(str(r) for r in runs2)
    print("\nFINAL RESULTS:")
    print(f"  {folder1}:{runs1_str}: Pts {total_pts1}, Score {total1:.1f}")
    print(f"  {folder2}:{runs2_str}: Pts {total_pts2}, Score {total2:.1f}")
    print(f"\nLogs saved to: {RESULTS_DIR}")
    if args.update_scoreboard:
        print(f"Scoreboard updated: {SCOREBOARD_PATH}")


if __name__ == "__main__":
    asyncio.run(main_async())
