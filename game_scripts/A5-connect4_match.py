"""
Connect 4 Match Runner: Orchestrates head-to-head matches between two AI models.

Prompts two models to implement Connect4Agent, extracts their code, renames
them to Connect4Agent_1 and Connect4Agent_2, runs games, and reports
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
    NUM_ROUNDS_PER_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    NUM_ROUNDS_PER_MATCH = 100

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

# Results directories
RESULTS_DIR = Path(__file__).parent.parent / "results" / "connect4"
GAME_LOGS_DIR = RESULTS_DIR / "game_logs"
MODEL_RESPONSES_DIR = RESULTS_DIR / "model_responses"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A5-Connect4RandomStart"

# The game code template with placeholders for agent implementations
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal
import copy

# Move timeout in seconds
MOVE_TIMEOUT = {move_timeout}

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

# --- Game Engine Code (from A5-Connect4RandomStart.txt) ---
class Connect4Game:
    ROWS = 6
    COLS = 7
    EMPTY = ' '
    RED = 'R'
    YELLOW = 'Y'

    def __init__(self):
        self.board = [[self.EMPTY for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.winner = None
        # Random start logic:
        # 1. Place Red piece in a random column
        start_col = random.randint(0, self.COLS - 1)
        self.drop_disc(start_col, self.RED)
        # 2. Set current turn to Yellow (since Red "moved")
        self.current_turn = self.YELLOW

    def drop_disc(self, col, disc):
        """Drop a disc into a column. Returns (row, col) or None if full."""
        if not (0 <= col < self.COLS):
            return None
        
        for r in range(self.ROWS - 1, -1, -1):
            if self.board[r][col] == self.EMPTY:
                self.board[r][col] = disc
                return r, col
        return None

    def check_winner(self):
        """Check for 4 in a row."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r][c+1] == self.board[r][c+2] == self.board[r][c+3]:
                    return self.board[r][c]

        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r+1][c] == self.board[r+2][c] == self.board[r+3][c]:
                    return self.board[r][c]

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r-1][c+1] == self.board[r-2][c+2] == self.board[r-3][c+3]:
                    return self.board[r][c]

        # Diagonal \\
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r+1][c+1] == self.board[r+2][c+2] == self.board[r+3][c+3]:
                    return self.board[r][c]

        return None

    def is_full(self):
        return all(self.board[0][c] != self.EMPTY for c in range(self.COLS))
# ---------------------------------------------------------

{extra_imports}

{agent1_code}

{agent2_code}

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
    print(" 0 1 2 3 4 5 6")
    for r in range(6):
        row_str = "|"
        for c in range(7):
            row_str += board[r][c] + "|"
        print(row_str)
    print("---------------")

def play_game(game_num):
    """Plays a single game and returns the winner's name or DRAW."""
    game = Connect4Game()
    
    # Assign agents based on game number for alternating colors
    # Note: Game always starts with Red piece placed, then Yellow moves.
    # We alternate who plays which color.
    
    if random.random() < 0.5:
        # Game 1, 3, 5...
        # Agent-1 is Red, Agent-2 is Yellow
        # Since Red moves first (randomly), Agent-2 (Yellow) makes the first CHOICE.
        red_agent_class = Connect4Agent_1
        yellow_agent_class = Connect4Agent_2
        red_name = "Agent-1"
        yellow_name = "Agent-2"
    else:
        # Game 2, 4, 6...
        # Agent-2 is Red, Agent-1 is Yellow
        red_agent_class = Connect4Agent_2
        yellow_agent_class = Connect4Agent_1
        red_name = "Agent-2"
        yellow_name = "Agent-1"

    print(f"--- GAME {{game_num}} ---")
    print(f"Roles: {{red_name}} is RED, {{yellow_name}} is YELLOW")
    print(f"Note: RED has already made a random start move.")

    try:
        agent_red = red_agent_class(red_name, game.RED)
    except Exception as e:
        stats["c1" if red_name == "Agent-1" else "c2"] += 1
        return yellow_name # Crash during init is loss
    
    try:
        agent_yellow = yellow_agent_class(yellow_name, game.YELLOW)
    except Exception as e:
        stats["c1" if yellow_name == "Agent-1" else "c2"] += 1
        return red_name 

    agents = {{game.RED: agent_red, game.YELLOW: agent_yellow}}
    names = {{game.RED: red_name, game.YELLOW: yellow_name}}

    while True:
        current_symbol = game.current_turn
        current_agent = agents[current_symbol]
        current_name = names[current_symbol]
        
        # Deep copy board for agent
        board_copy = [row[:] for row in game.board]
        
        move = None
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(MOVE_TIMEOUT))
            try:
                move = current_agent.make_move(board_copy)
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            if current_name == "Agent-1": stats["r1_timeout"] += 1
            else: stats["r2_timeout"] += 1
            # Timeout is a loss
            print(f"{{current_name}} TIMEOUT")
            return names[game.YELLOW] if current_symbol == game.RED else names[game.RED]
        except Exception as e:
            if current_name == "Agent-1": stats["r1_crash"] += 1
            else: stats["r2_crash"] += 1
            print(f"{{current_name}} CRASH: {{e}}")
            return names[game.YELLOW] if current_symbol == game.RED else names[game.RED]

        # Validate move type
        if move is None or not isinstance(move, int):
            if current_name == "Agent-1": stats["r1_invalid"] += 1
            else: stats["r2_invalid"] += 1
            print(f"{{current_name}} INVALID MOVE TYPE: {{move}}")
            return names[game.YELLOW] if current_symbol == game.RED else names[game.RED]

        # Apply move
        result = game.drop_disc(move, current_symbol)
        
        if result is None:
            # Invalid move (column full or out of bounds)
            if current_name == "Agent-1": stats["r1_invalid"] += 1
            else: stats["r2_invalid"] += 1
            print(f"{{current_name}} INVALID MOVE: {{move}} (Full/OOB)")
            return names[game.YELLOW] if current_symbol == game.RED else names[game.RED]
        
        winner = game.check_winner()
        if winner:
            print("Final Board:")
            print_board(game.board)
            if winner == 'DRAW':
                print("Result: DRAW") # Should not happen from check_winner returning 'DRAW', handles in is_full
                stats["draw"] += 1
                return "DRAW"
            else:
                winner_name = names[winner]
                print(f"Result: {{winner_name}} wins!")
                stats["normal"] += 1
                return winner_name
        
        if game.is_full():
            print("Final Board:")
            print_board(game.board)
            print("Result: DRAW")
            stats["draw"] += 1
            return "DRAW"
        
        # Switch turn
        game.current_turn = game.YELLOW if game.current_turn == game.RED else game.RED

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

HUMAN_GAME_CODE = '''
import sys
import random

class Connect4Game:
    ROWS = 6
    COLS = 7
    EMPTY = ' '
    RED = 'R'
    YELLOW = 'Y'

    def __init__(self):
        self.board = [[self.EMPTY for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.winner = None
        # Random start logic:
        # 1. Place Red piece in a random column
        start_col = random.randint(0, self.COLS - 1)
        self.drop_disc(start_col, self.RED)
        # 2. Set current turn to Yellow (since Red "moved")
        self.current_turn = self.YELLOW

    def drop_disc(self, col, disc):
        """Drop a disc into a column. Returns (row, col) or None if full."""
        if not (0 <= col < self.COLS):
            return None
        
        for r in range(self.ROWS - 1, -1, -1):
            if self.board[r][col] == self.EMPTY:
                self.board[r][col] = disc
                return r, col
        return None

    def check_winner(self):
        """Check for 4 in a row."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r][c+1] == self.board[r][c+2] == self.board[r][c+3]:
                    return self.board[r][c]

        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r+1][c] == self.board[r+2][c] == self.board[r+3][c]:
                    return self.board[r][c]

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r-1][c+1] == self.board[r-2][c+2] == self.board[r-3][c+3]:
                    return self.board[r][c]

        # Diagonal \\
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \\
                   self.board[r][c] == self.board[r+1][c+1] == self.board[r+2][c] == self.board[r+3][c]:
                    return self.board[r][c]

        return None

    def is_full(self):
        return all(self.board[0][c] != self.EMPTY for c in range(self.COLS))

    def play_game(self, agent_red, agent_yellow):
        """
        Run a game between two agents.
        Remember: Game starts with one Red piece already placed (randomly).
        So the first call is to agent_yellow.
        """
        agents = {self.RED: agent_red, self.YELLOW: agent_yellow}
        
        while True:
            current_agent = agents[self.current_turn]
            # Copy board to prevent agents from modifying state
            board_copy = [row[:] for row in self.board]
            
            try:
                col = current_agent.make_move(board_copy)
                result = self.drop_disc(col, self.current_turn)
                
                if result is None:
                    # Invalid move (column full or out of bounds)
                    # Opponent wins
                    return self.YELLOW if self.current_turn == self.RED else self.RED
                
                winner = self.check_winner()
                if winner:
                    return winner
                
                if self.is_full():
                    return "DRAW"
                
                # Switch turn
                self.current_turn = self.YELLOW if self.current_turn == self.RED else self.RED

            except Exception as e:
                # Crash means automatic loss
                print(f"Agent {self.current_turn} crashed: {e}")
                return self.YELLOW if self.current_turn == self.RED else self.RED

class HumanAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        """Ask user for column input."""
        while True:
            try:
                # Basic board display for the human player
                print(f"\\n{self.name}'s turn ({self.symbol})")
                print(" 0 1 2 3 4 5 6")
                for r in range(6):
                    row_str = "|"
                    for c in range(7):
                        cell = board[r][c]
                        row_str += cell + "|"
                    print(row_str)
                print("---------------")
                
                col_str = input(f"Choose column (0-6): ")
                col = int(col_str)
                if 0 <= col < 7:
                    # Check if column is full (top row is empty)
                    if board[0][col] == ' ':
                        return col
                    else:
                        print(f"Column {col} is full. Try another.")
                else:
                    print("Invalid column. Must be 0-6.")
            except ValueError:
                print("Invalid input. Please enter a number.")

class RandomAgent:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

    def make_move(self, board):
        """Pick a random valid column."""
        valid_cols = [c for c in range(7) if board[0][c] == ' ']
        if not valid_cols:
            return 0
        return random.choice(valid_cols)

if __name__ == "__main__":
    game = Connect4Game()
    
    p1, p2 = None, None
    if random.random() < 0.5:
        human = HumanAgent("Human", game.RED)
        bot = RandomAgent("Bot", game.YELLOW)
        p1, p2 = human, bot
        print(f"You are Red ({human.symbol}). Bot is Yellow ({bot.symbol}).")
    else:
        bot = RandomAgent("Bot", game.RED)
        human = HumanAgent("Human", game.YELLOW)
        p1, p2 = bot, human
        print(f"Bot is Red ({bot.symbol}). You are Yellow ({human.symbol}).")
    
    print("Starting Connect 4 Random Start!")
    print("Be aware: Red player's first piece is placed randomly.")
    
    winner = game.play_game(p1, p2)
    
    print("\\nFinal Board:")
    print(" 0 1 2 3 4 5 6")
    for r in range(game.ROWS):
        print("|" + "|".join(game.board[r]) + "|")
    print("---------------")
        
    if winner == "DRAW":
        print("Game Over: Draw!")
    else:
        print(f"Game Over: Winner is {winner}!")
'''

def load_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "games" / "A5-Connect4RandomStart.txt"
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
    # Rename Connect4Agent to Connect4Agent_{agent_idx}
    code = re.sub(r"class\s+Connect4Agent\b", f"class Connect4Agent_{agent_idx}", code)
    
    return code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    """Parse agent spec (model:run1:run2) into model pattern and list of runs."""
    parts = spec.split(":")
    model_pattern = parts[0]
    runs = [int(r) for r in parts[1:]]
    return model_pattern, runs

def run_match(game_code: str):
    temp_file = os.path.join(tempfile.gettempdir(), f"c4_{uuid.uuid4().hex[:8]}.py")
    try:
        with open(temp_file, "w") as f: f.write(game_code)
        result = subprocess.run(["python", temp_file], capture_output=True, text=True, timeout=300)
        return result.stdout
    except Exception as e:
        return f"ERROR: {e}"
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
    parser = argparse.ArgumentParser(description="Run Connect 4 matches between stored AI agents")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4]")
    parser.add_argument("--human", action="store_true", help="Play interactively against a bot")
    args = parser.parse_args()

    if args.human:
        temp_file = os.path.join(tempfile.gettempdir(), f"connect4_human_{uuid.uuid4().hex[:8]}.py")
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
        logger.warning("Number of runs for %s (%d) and %s (%d) don't match. Using first %d.", 
                       folder1, len(runs1), folder2, len(runs2), num_matches)
    
    runs1 = runs1[:num_matches]
    runs2 = runs2[:num_matches]

    print("\n" + "=" * 60)
    print("CONNECT 4 MATCH - STORED AGENTS")
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
            move_timeout=MOVE_TIME_LIMIT
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
