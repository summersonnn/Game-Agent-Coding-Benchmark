"""
Tic Tac Toe Match Runner: Orchestrates head-to-head matches between two AI agents.

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

# Load environment variables
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

try:
    MATCH_TIME_LIMIT = int(os.getenv("MATCH_TIME_LIMIT", "900"))
except (ValueError, TypeError):
    MATCH_TIME_LIMIT = 900

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / "tictactoe"
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / "A2-scoreboard.txt"
AGENTS_DIR = BASE_DIR / "agents"

GAME_NAME = "A2-TicTacToe"

MODE_TITLES = {
    "humanvsbot": "Human vs Random Bot",
    "humanvshuman": "Human vs Human",
    "humanvsagent": "Human vs Stored Agent",
}


# ============================================================
# Game engine code (constants, TicTacToeGame, board display)
# ============================================================
GAME_ENGINE_CODE = r'''
EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'
BOARD_SIZE = 5

# Max possible tie-breaker score (win at move 5 = 20 empty cells)
FORFEIT_SCORE = 20


class TicTacToeGame:
    """Manages the state and rules of a Tic Tac Toe game."""

    def __init__(self):
        self.board = [EMPTY for _ in range(25)]
        self.current_turn = X_MARK

    def make_move(self, position):
        if 0 <= position < 25 and self.board[position] == EMPTY:
            self.board[position] = self.current_turn
            self.current_turn = O_MARK if self.current_turn == X_MARK else X_MARK
            return True
        return False

    def check_winner(self):
        win_conditions = []
        # Rows
        for r in range(5):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 1, start + 2))
        # Cols
        for c in range(5):
            for r in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 5, start + 10))
        # Diagonals (down-right)
        for r in range(3):
            for c in range(3):
                start = r * 5 + c
                win_conditions.append((start, start + 6, start + 12))
        # Diagonals (down-left)
        for r in range(3):
            for c in range(2, 5):
                start = r * 5 + c
                win_conditions.append((start, start + 4, start + 8))

        for combo in win_conditions:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != EMPTY:
                return self.board[combo[0]]
        if EMPTY not in self.board:
            return 'DRAW'
        return None


def print_board(board):
    """Print board for human players (no BOARD: prefix)."""
    print("   0 |  1 |  2 |  3 |  4")
    print(f"   {board[0]} |  {board[1]} |  {board[2]} |  {board[3]} |  {board[4]}")
    print(" -----------------------")
    print(f"   {board[5]} |  {board[6]} |  {board[7]} |  {board[8]} |  {board[9]}")
    print(" -----------------------")
    print(f"  {board[10]} | {board[11]} | {board[12]} | {board[13]} | {board[14]}")
    print(" -----------------------")
    print(f"  {board[15]} | {board[16]} | {board[17]} | {board[18]} | {board[19]}")
    print(" -----------------------")
    print(f"  {board[20]} | {board[21]} | {board[22]} | {board[23]} | {board[24]}")


def print_board_log(board):
    """Print board with BOARD: prefix for log filtering."""
    print("BOARD:    0 |  1 |  2 |  3 |  4")
    print(f"BOARD:    {board[0]} |  {board[1]} |  {board[2]} |  {board[3]} |  {board[4]}")
    print("BOARD:  -----------------------")
    print(f"BOARD:    {board[5]} |  {board[6]} |  {board[7]} |  {board[8]} |  {board[9]}")
    print("BOARD:  -----------------------")
    print(f"BOARD:   {board[10]} | {board[11]} | {board[12]} | {board[13]} | {board[14]}")
    print("BOARD:  -----------------------")
    print(f"BOARD:   {board[15]} | {board[16]} | {board[17]} | {board[18]} | {board[19]}")
    print("BOARD:  -----------------------")
    print(f"BOARD:   {board[20]} | {board[21]} | {board[22]} | {board[23]} | {board[24]}")


class RandomAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        available = [i for i, spot in enumerate(board) if spot == EMPTY]
        return random.choice(available) if available else None


class HumanAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        print_board(board)
        while True:
            try:
                user_input = input(f"Enter move [0-24] (You are {self.symbol}): ").strip()
                if not user_input:
                    continue
                move = int(user_input)
                if 0 <= move < 25 and board[move] == EMPTY:
                    return move
                print("Invalid move.")
            except ValueError:
                print("Enter a number.")
'''


# ============================================================
# Match runner code (play_game, main, stats, output)
# ============================================================
MATCH_RUNNER_CODE = r'''
class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")


def play_game(game_num, match_stats):
    """Play a single game and update match_stats. Returns winner name or 'DRAW'."""
    game = TicTacToeGame()

    # Determine agent classes based on game mode
    if GAME_MODE == "humanvsbot":
        class_1, class_2 = HumanAgent, RandomAgent
    elif GAME_MODE == "humanvshuman":
        class_1, class_2 = HumanAgent, HumanAgent
    elif GAME_MODE == "humanvsagent":
        class_1, class_2 = HumanAgent, TicTacToeAgent_1
    else:
        class_1, class_2 = TicTacToeAgent_1, TicTacToeAgent_2

    # Alternate who plays X each game (odd games: Agent-1 is X, even: Agent-2)
    if game_num % 2 == 1:
        x_class, o_class = class_1, class_2
        x_name, o_name = "Agent-1", "Agent-2"
    else:
        x_class, o_class = class_2, class_1
        x_name, o_name = "Agent-2", "Agent-1"

    a1_symbol = 'X' if x_name == "Agent-1" else 'O'
    a2_symbol = 'X' if x_name == "Agent-2" else 'O'

    print()
    print("=" * 60)
    print(f"Game {game_num}")
    print(f"Agent-1: {AGENT1_NAME} ({a1_symbol})")
    print(f"Agent-2: {AGENT2_NAME} ({a2_symbol})")
    print("-" * 60)

    # --- Initialize agents (other_crash on failure = forfeit) ---
    try:
        agent_x = x_class(x_name, X_MARK)
    except Exception as e:
        print(f"{x_name} (X) init crash: {e}")
        match_stats[x_name]["other_crash"] += 1
        match_stats[o_name]["wins"] += 1
        match_stats[o_name]["points"] += 3
        match_stats[o_name]["score"] += FORFEIT_SCORE
        match_stats[x_name]["losses"] += 1
        match_stats[x_name]["score"] -= FORFEIT_SCORE

        print("Final Position: N/A (initialization crash)")
        print("-" * 40)
        print(f"Final Result: {o_name} wins. (opponent crashed)")
        print("-" * 40)
        print("Points:")
        print(f"{o_name}: 3")
        print(f"{x_name}: 0")
        print("-" * 40)
        print("Scores:")
        print(f"{o_name}: {FORFEIT_SCORE}")
        print(f"{x_name}: -{FORFEIT_SCORE}")
        print("=" * 60)
        return o_name

    try:
        agent_o = o_class(o_name, O_MARK)
    except Exception as e:
        print(f"{o_name} (O) init crash: {e}")
        match_stats[o_name]["other_crash"] += 1
        match_stats[x_name]["wins"] += 1
        match_stats[x_name]["points"] += 3
        match_stats[x_name]["score"] += FORFEIT_SCORE
        match_stats[o_name]["losses"] += 1
        match_stats[o_name]["score"] -= FORFEIT_SCORE

        print("Final Position: N/A (initialization crash)")
        print("-" * 40)
        print(f"Final Result: {x_name} wins. (opponent crashed)")
        print("-" * 40)
        print("Points:")
        print(f"{x_name}: 3")
        print(f"{o_name}: 0")
        print("-" * 40)
        print("Scores:")
        print(f"{x_name}: {FORFEIT_SCORE}")
        print(f"{o_name}: -{FORFEIT_SCORE}")
        print("=" * 60)
        return x_name

    agents = {X_MARK: agent_x, O_MARK: agent_o}
    names = {X_MARK: x_name, O_MARK: o_name}

    # --- Random first move for X ---
    random_first_pos = random.choice(range(25))
    game.make_move(random_first_pos)
    print(f"Random first move: X plays ({random_first_pos // 5}, {random_first_pos % 5})")

    # --- Game loop ---
    while True:
        current_symbol = game.current_turn
        current_agent = agents[current_symbol]
        current_name = names[current_symbol]
        opponent_symbol = O_MARK if current_symbol == X_MARK else X_MARK
        opponent_name = names[opponent_symbol]

        move = None
        error_type = None

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                move = current_agent.make_move(game.board[:])
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            match_stats[current_name]["timeout"] += 1
            error_type = "timeout"
        except Exception:
            match_stats[current_name]["make_move_crash"] += 1
            error_type = "crash"

        # Validate move
        if error_type is None and move is not None:
            if not isinstance(move, int) or not (0 <= move < 25) or game.board[move] != EMPTY:
                match_stats[current_name]["invalid"] += 1
                error_type = "invalid"
                move = None

        # Random fallback on any error
        if move is None or error_type is not None:
            available = [i for i, spot in enumerate(game.board) if spot == EMPTY]
            if available:
                move = random.choice(available)
            else:
                break

        game.make_move(move)

        winner = game.check_winner()
        if winner:
            empty_cells = game.board.count(EMPTY)

            print("Final Position:")
            print_board_log(game.board)
            print("-" * 40)

            if winner == 'DRAW':
                print("Final Result: Draw.")
                print("-" * 40)
                print("Points:")
                print("Agent-1: 1")
                print("Agent-2: 1")
                print("-" * 40)
                print("Scores:")
                print("Agent-1: 0")
                print("Agent-2: 0")
                print("=" * 60)

                match_stats["Agent-1"]["draws"] += 1
                match_stats["Agent-1"]["points"] += 1
                match_stats["Agent-2"]["draws"] += 1
                match_stats["Agent-2"]["points"] += 1
                return "DRAW"
            else:
                win_name = names[winner]
                lose_symbol = O_MARK if winner == X_MARK else X_MARK
                lose_name = names[lose_symbol]
                game_score = max(empty_cells, 3)

                print(f"Final Result: {win_name} wins.")
                print("-" * 40)
                print("Points:")
                print(f"{win_name}: 3")
                print(f"{lose_name}: 0")
                print("-" * 40)
                print("Scores:")
                print(f"{win_name}: {game_score}")
                print(f"{lose_name}: -{game_score}")
                print("=" * 60)

                match_stats[win_name]["wins"] += 1
                match_stats[win_name]["points"] += 3
                match_stats[win_name]["score"] += game_score
                match_stats[lose_name]["losses"] += 1
                match_stats[lose_name]["score"] -= game_score
                return win_name


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

    # Extract imports before the class
    imports = []
    class_start_idx = None

    for i, line in enumerate(code_lines):
        stripped = line.strip()

        if stripped.startswith("class TicTacToeAgent"):
            class_start_idx = i
            break

        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:
                imports.append(stripped)

    if class_start_idx is None:
        logger.error("No TicTacToeAgent class found in %s", agent_file)
        return "", ""

    # Extract the class body (stop at next top-level definition)
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
    agent_code = re.sub(
        r"\bTicTacToeAgent\b", f"TicTacToeAgent_{agent_idx}", agent_code
    )

    return agent_code.strip(), "\n".join(imports)


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
    game_mode: str = "",
    agent1_name: str = "Agent-1",
    agent2_name: str = "Agent-2",
) -> str:
    """Build the complete game code by concatenating header, agents, engine, and runner."""
    header = (
        "import sys\n"
        "import random\n"
        "import signal\n"
        "import time\n"
        "import collections\n"
        "import math\n"
        "import itertools\n"
        "import copy\n"
        "\n"
        f"MOVE_TIMEOUT = {move_timeout}\n"
        f"NUM_GAMES = {num_games}\n"
        f'GAME_MODE = "{game_mode}"\n'
        f'AGENT1_NAME = "{agent1_name}"\n'
        f'AGENT2_NAME = "{agent2_name}"\n'
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
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = MATCH_TIME_LIMIT
) -> dict:
    """Execute a match subprocess, parse results, and return structured dict."""
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"tictactoe_match_{match_id}_{temp_id}.py"
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
                "log": result.stdout,
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
        tempfile.gettempdir(), f"tictactoe_human_{uuid.uuid4().hex[:8]}.py"
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
    parser = argparse.ArgumentParser(
        description="Run Tic-Tac-Toe matches between stored AI agents"
    )
    parser.add_argument(
        "--agent", nargs="+",
        help="Agent specs: model1[:run1:run2] model2[:run3:run4]",
    )
    human_group = parser.add_mutually_exclusive_group()
    human_group.add_argument(
        "--humanvsbot", action="store_true",
        help="Play interactively against a random bot",
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
        print(f"TIC TAC TOE - {mode_title}")
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
    print("TIC TAC TOE MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

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
            agent1_name=f"{folder1}:{run1}", agent2_name=f"{folder2}:{run2}",
        )

        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)

    # Process results and write per-match log files
    total1, total2 = 0.0, 0.0
    total_pts1, total_pts2 = 0, 0

    for result in sorted(results, key=lambda x: x["match_id"]):
        match_id = result["match_id"]
        run1 = runs1[match_id - 1]
        run2 = runs2[match_id - 1]
        log_f = RESULTS_DIR / f"{ts}_{folder1}:{run1}_vs_{folder2}:{run2}_match.txt"
        p1, p2 = 0, 0

        if result["success"]:
            s1, s2 = result["agent1_score"], result["agent2_score"]
            p1 = result.get("agent1_points", 0)
            p2 = result.get("agent2_points", 0)
            total1 += s1
            total2 += s2
            total_pts1 += p1
            total_pts2 += p2

            status = "Result:\n"
            status += f"{folder1}:{result['agent1_run_id']} : Pts: {p1} - Score: {s1:.1f}\n"
            status += f"{folder2}:{result['agent2_run_id']} : Pts: {p2} - Score: {s2:.1f}\n"

            game_log = result.get("log", "")
            if game_log:
                status += f"\n{game_log}\n"

        else:
            status = f"FAILED: {result.get('error', 'Unknown')}"

        print(f"Match {match_id} Completed. Pts {p1}-{p2}")

        with open(log_f, "w") as f:
            f.write("Match Contenders:\n")
            f.write(f"{folder1}:{run1}\n")
            f.write(f"{folder2}:{run2}\n\n")
            f.write(f"{status}\n")
            f.write("-" * 60 + "\n")

        if result["success"] and args.update_scoreboard:
            agent1_key = f"{folder1}:{result['agent1_run_id']}"
            update_scoreboard(
                SCOREBOARD_PATH, agent1_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=result.get("agent1_wins", 0),
                losses=result.get("agent2_wins", 0),
                draws=result.get("draws", 0),
                score=result["agent1_score"],
                points=result.get("agent1_points", 0),
            )
            agent2_key = f"{folder2}:{result['agent2_run_id']}"
            update_scoreboard(
                SCOREBOARD_PATH, agent2_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=result.get("agent2_wins", 0),
                losses=result.get("agent1_wins", 0),
                draws=result.get("draws", 0),
                score=result["agent2_score"],
                points=result.get("agent2_points", 0),
            )

    runs1_str = ",".join(str(r) for r in runs1)
    runs2_str = ",".join(str(r) for r in runs2)
    print("\nFINAL RESULTS:")
    print(f"  {folder1}:{runs1_str}: Pts {total_pts1}, Score {total1:.1f}")
    print(f"  {folder2}:{runs2_str}: Pts {total_pts2}, Score {total2:.1f}")
    print(f"\nLogs saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    asyncio.run(main_async())
