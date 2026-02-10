"""
Tic Tac Toe Match Runner: Orchestrates head-to-head matches between two AI models.

Prompts two models to implement TicTacToeAgent, extracts their code, renames
them to TicTacToeAgent_1 and TicTacToeAgent_2, runs games, and reports
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
import logging
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
    NUM_ROUNDS_PER_TICTACTOE_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    NUM_ROUNDS_PER_TICTACTOE_MATCH = 100

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

BOARD_SIZE = 3

# Results directories
TICTACTOE_RESULTS_DIR = Path(__file__).parent.parent / "results" / "tictactoe"
GAME_LOGS_DIR = TICTACTOE_RESULTS_DIR / "game_logs"
MODEL_RESPONSES_DIR = TICTACTOE_RESULTS_DIR / "model_responses"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A2-TicTacToe"

# The game code template with placeholders for agent implementations
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal
# Move timeout in seconds
MOVE_TIMEOUT = {move_timeout}
HUMAN_MODE = {human_mode}

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

# --- Board Representations ---
EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'

{extra_imports}

{agent1_code}

{agent2_code}

class RandomAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        available = [i for i, spot in enumerate(board) if spot == EMPTY]
        if available:
            return random.choice(available)
        return None

class HumanAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        print_board(board)
        while True:
            try:
                user_input = input(f"Enter move [0-8] (You are {{self.symbol}}): ").strip()
                if not user_input: continue
                move = int(user_input)
                if 0 <= move < 9 and board[move] == EMPTY:
                    return move
                print("Invalid move.")
            except ValueError:
                print("Enter a number.")

class TicTacToeGame:
    """Manages the state and rules of the game."""
    def __init__(self):
        self.board = [EMPTY for _ in range(9)]
        self.current_turn = X_MARK

    def make_move(self, position):
        if 0 <= position < 9 and self.board[position] == EMPTY:
            self.board[position] = self.current_turn
            self.current_turn = O_MARK if self.current_turn == X_MARK else X_MARK
            return True
        return False

    def check_winner(self):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8), # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8), # Columns
            (0, 4, 8), (2, 4, 6)             # Diagonals
        ]
        for combo in win_conditions:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != EMPTY:
                return self.board[combo[0]]
        if EMPTY not in self.board:
            return 'DRAW'
        return None

# --- Stats ---
stats = {{
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
}}

def print_board(board):
    print("  0 | 1 | 2")
    print(f" {{board[0]}} | {{board[1]}} | {{board[2]}}")
    print("-----------")
    print(f" {{board[3]}} | {{board[4]}} | {{board[5]}}")
    print("-----------")
    print(f" {{board[6]}} | {{board[7]}} | {{board[8]}}")

def play_game(game_num):
    """Plays a single game of Tic Tac Toe and returns the winner's name or DRAW."""
    game = TicTacToeGame()
    
    # Randomly assign symbols to agents for each game
    # In one game Agent-1 is X, in next Agent-2 is X
    
    if HUMAN_MODE:
        class_1 = HumanAgent
        class_2 = RandomAgent
    else:
        class_1 = TicTacToeAgent_1
        class_2 = TicTacToeAgent_2

    # Randomize starting agent
    if random.random() < 0.5:
        x_agent_class = class_1
        o_agent_class = class_2
        x_name = "Agent-1"
        o_name = "Agent-2"
    else:
        x_agent_class = class_2
        o_agent_class = class_1
        x_name = "Agent-2"
        o_name = "Agent-1"

    print(f"--- GAME {{game_num}} ---")
    print(f"Symbols: {{x_name}} is {{X_MARK}}, {{o_name}} is {{O_MARK}}")

    try:
        agent_x = x_agent_class(x_name, X_MARK)
    except Exception as e:
        stats["c1" if x_name == "Agent-1" else "c2"] += 1
        return o_name
    
    try:
        agent_o = o_agent_class(o_name, O_MARK)
    except Exception as e:
        stats["c1" if o_name == "Agent-1" else "c2"] += 1
        return x_name

    agents = {{X_MARK: agent_x, O_MARK: agent_o}}
    names = {{X_MARK: x_name, O_MARK: o_name}}

    while True:
        current_symbol = game.current_turn
        current_agent = agents[current_symbol]
        current_name = names[current_symbol]
        
        move = None
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(MOVE_TIMEOUT)) # signal.alarm requires integer
            try:
                move = current_agent.make_move(game.board[:])
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            if current_name == "Agent-1": stats["r1_timeout"] += 1
            else: stats["r2_timeout"] += 1
        except Exception:
            if current_name == "Agent-1": stats["r1_crash"] += 1
            else: stats["r2_crash"] += 1

        if move is None or not isinstance(move, int) or not (0 <= move < 9) or game.board[move] != EMPTY:
            if move is not None:
                if current_name == "Agent-1": stats["r1_invalid"] += 1
                else: stats["r2_invalid"] += 1
            # Auto-fallback to random move
            available = [i for i, spot in enumerate(game.board) if spot == EMPTY]
            if available:
                move = random.choice(available)
            else:
                break # Should not happen

        game.make_move(move)
        
        winner = game.check_winner()
        if winner:
            print("Final Board:")
            print_board(game.board)
            if winner == 'DRAW':
                print("Result: DRAW")
                stats["draw"] += 1
                return "DRAW"
            else:
                print(f"Result: {{names[winner]}} wins!")
                stats["normal"] += 1
                return names[winner]

def main():
    scores = {{AGENT1_NAME: 0, AGENT2_NAME: 0}}
    num_games = {num_games}

    for i in range(num_games):
        result = play_game(i + 1)
        if result == "DRAW":
            scores["Agent-1"] += 0.5
            scores["Agent-2"] += 0.5
        elif result in scores:
            scores[result] += 1
        
        sys.stdout.flush()

    print(f"RESULT:Agent-1={{scores[AGENT1_NAME]}},Agent-2={{scores[AGENT2_NAME]}}")
    print(f"STATS:Normal={{stats['normal']}},Draw={{stats['draw']}},C1={{stats['c1']}},C2={{stats['c2']}},R1T={{stats['r1_timeout']}},R1C={{stats['r1_crash']}},R1I={{stats['r1_invalid']}},R2T={{stats['r2_timeout']}},R2C={{stats['r2_crash']}},R2I={{stats['r2_invalid']}}")

if __name__ == "__main__":
    main()
'''

def load_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "games" / "A2-TicTacToe.txt"
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
    # Rename TicTacToeAgent to TicTacToeAgent_{agent_idx}
    code = re.sub(r"class\s+TicTacToeAgent\b", f"class TicTacToeAgent_{agent_idx}", code)
    
    return code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    """Parse agent spec (model:run1:run2) into model pattern and list of runs."""
    parts = spec.split(":")
    model_pattern = parts[0]
    runs = [int(r) for r in parts[1:]]
    return model_pattern, runs

def run_match(game_code: str):
    temp_file = os.path.join(tempfile.gettempdir(), f"ttt_{uuid.uuid4().hex[:8]}.py")
    try:
        with open(temp_file, "w") as f: f.write(game_code)
        result = subprocess.run(["python", temp_file], capture_output=True, text=True, timeout=300)
        return result.stdout
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

def run_match_human(game_code: str):
    temp_file = os.path.join(tempfile.gettempdir(), f"ttt_human_{uuid.uuid4().hex[:8]}.py")
    try:
        with open(temp_file, "w") as f: f.write(game_code)
        subprocess.call(["python", temp_file])
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

async def run_match_async(game_code: str, match_id: int, run_ids: tuple[int, int], log_f: Path, folder1: str, folder2: str):
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
    parser = argparse.ArgumentParser(description="Run Tic-Tac-Toe matches between stored AI agents")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4]")
    parser.add_argument("--human", action="store_true", help="Play interactively against a random bot")
    args = parser.parse_args()

    if args.human:
        print("\n" + "=" * 60)
        print("TIC TAC TOE HUMAN MODE")
        print("You are playing against a RandomBot.")
        print("=" * 60)
        
        game_code = GAME_CODE_TEMPLATE.format(
            extra_imports="",
            agent1_code="",
            agent2_code="",
            move_timeout=99999,
            num_games=NUM_ROUNDS_PER_TICTACTOE_MATCH, # Or just 1? Loop will run many.
            human_mode=True
        )
        # We might want fewer games for human play? The loop in main runs num_games.
        # But run_match_human runs the WHOLE script which contains the loop.
        # So we should set num_games=1 or let the user ctrl-c.
        # Let's set num_games=10? Or just 1.
        # The user probably wants one game or continuous. The script accepts num_games.
        # Let's override num_games in the template call.
        
        game_code = GAME_CODE_TEMPLATE.format(
            extra_imports="",
            agent1_code="",
            agent2_code="",
            move_timeout=99999,
            num_games=10, # Play 10 games
            human_mode=True
        )
        run_match_human(game_code)
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
        logger.warning("Number of runs for %s (%d) and %s (%d) don't match. Using first %d.", 
                       folder1, len(runs1), folder2, len(runs2), num_matches)
    
    runs1 = runs1[:num_matches]
    runs2 = runs2[:num_matches]

    print("\n" + "=" * 60)
    print("TIC TAC TOE MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    TICTACTOE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
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
            num_games=NUM_ROUNDS_PER_TICTACTOE_MATCH,
            move_timeout=MOVE_TIME_LIMIT,
            human_mode=False
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
        r1, r2 = runs1[m_id-1], runs2[m_id-1]
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
