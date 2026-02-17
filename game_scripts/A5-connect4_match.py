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
from scoreboard import update_scoreboard

logger = setup_logging(__name__)

# Load environment variables
load_dotenv()

# Configuration
try:
    NUM_ROUNDS_PER_MATCH = int(int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100")) / 10)
except (ValueError, TypeError):
    NUM_ROUNDS_PER_MATCH = 10

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0



# Results directories
RESULTS_DIR = Path(__file__).parent.parent / "results" / "connect4"
MODEL_RESPONSES_DIR = RESULTS_DIR / "model_responses"
SCOREBOARD_PATH = Path(__file__).parent.parent / "scoreboard" / "A5-scoreboard.txt"

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

AGENT1_NAME = "{agent1_name}"
AGENT2_NAME = "{agent2_name}"

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")


# --- Game Engine Code (from A5-Connect4RandomStart.txt) ---
def print_board_log(board):
    """Print board with BOARD: prefix for log filtering."""
    print("BOARD:  0 1 2 3 4 5 6")
    for r in range(6):
        row_str = "BOARD: |"
        for c in range(7):
            row_str += board[r][c] + "|"
        print(row_str)
    print("BOARD: ---------------")

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
        """Check for 4 in a row. Returns (winner, start_pos, end_pos) or None."""
        # Horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \
                   self.board[r][c] == self.board[r][c+1] == self.board[r][c+2] == self.board[r][c+3]:
                    return self.board[r][c], (r, c), (r, c+3)

        # Vertical
        for r in range(self.ROWS - 3):
            for c in range(self.COLS):
                if self.board[r][c] != self.EMPTY and \
                   self.board[r][c] == self.board[r+1][c] == self.board[r+2][c] == self.board[r+3][c]:
                    return self.board[r][c], (r, c), (r+3, c)

        # Diagonal /
        for r in range(3, self.ROWS):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \
                   self.board[r][c] == self.board[r-1][c+1] == self.board[r-2][c+2] == self.board[r-3][c+3]:
                    return self.board[r][c], (r, c), (r-3, c+3)

        # Diagonal \\
        for r in range(self.ROWS - 3):
            for c in range(self.COLS - 3):
                if self.board[r][c] != self.EMPTY and \
                   self.board[r][c] == self.board[r+1][c+1] == self.board[r+2][c+2] == self.board[r+3][c+3]:
                    return self.board[r][c], (r, c), (r+3, c+3)

        return None

    def is_full(self):
        return all(self.board[0][c] != self.EMPTY for c in range(self.COLS))
# ---------------------------------------------------------

{extra_imports}

{agent1_code}

{agent2_code}


def print_board(board):
    print("  0 1 2 3 4 5 6")
    for r in range(6):
        row_str = "|"
        for c in range(7):
            row_str += board[r][c] + "|"
        print(row_str)
    print("---------------")

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

def play_game(game_num, match_stats):
    """Plays a single game and returns the winner's name or 'DRAW'."""
    game = Connect4Game()
    
    # Assign agents based on game number for alternating colors
    # Note: Game always starts with Red piece placed (randomly), then Yellow moves.
    # We alternate who plays which color.
    
    # Alternate turns based on game number
    if game_num % 2 != 0:
        # Agent-1 is Red, Agent-2 is Yellow
        red_agent_class = Connect4Agent_1
        yellow_agent_class = Connect4Agent_2
        red_name = "Agent-1"
        yellow_name = "Agent-2"
    else:
        # Agent-2 is Red, Agent-1 is Yellow
        red_agent_class = Connect4Agent_2
        yellow_agent_class = Connect4Agent_1
        red_name = "Agent-2"
        yellow_name = "Agent-1"

    print(f"============================================================")
    print(f"Game {{game_num}}")
    if red_name == "Agent-1":
        print(f"Agent-1: {{AGENT1_NAME}} (RED - has random start)")
        print(f"Agent-2: {{AGENT2_NAME}} (YELLOW)")
    else:
        print(f"Agent-1: {{AGENT1_NAME}} (YELLOW)")
        print(f"Agent-2: {{AGENT2_NAME}} (RED - has random start)")
    print("------------------------------------------------------------")

    # --- Initialize Agents ---
    try:
        agent_red = red_agent_class(red_name, game.RED)
    except Exception as e:
        print(f"{{red_name}} (RED) init crash: {{e}}")
        match_stats[red_name]["other_crash"] += 1
        
        # Forfeit logic
        winner_name = yellow_name
        loser_name = red_name
        
        match_stats[winner_name]["wins"] += 1
        match_stats[winner_name]["points"] += 3
        # Max score calculation: 6x7=42 cells. 1 is occupied by random start.
        # Max possible empty cells = 41.
        match_stats[winner_name]["score"] += 41
        match_stats[loser_name]["losses"] += 1
        match_stats[loser_name]["score"] -= 41
        
        print("Final Position: N/A (initialization crash)")
        print("----------------------------------------")
        print(f"Final Result: {{winner_name}} wins. (opponent crashed)")
        print("----------------------------------------")
        print("Points:")
        print(f"{{winner_name}}: 3")
        print(f"{{loser_name}}: 0")
        print("----------------------------------------")
        print("Scores:")
        print(f"{{winner_name}}: 41")
        print(f"{{loser_name}}: -41")
        print("============================================================")
        return winner_name
    
    try:
        agent_yellow = yellow_agent_class(yellow_name, game.YELLOW)
    except Exception as e:
        print(f"{{yellow_name}} (YELLOW) init crash: {{e}}")
        match_stats[yellow_name]["other_crash"] += 1
        
        # Forfeit logic
        winner_name = red_name
        loser_name = yellow_name
        
        match_stats[winner_name]["wins"] += 1
        match_stats[winner_name]["points"] += 3
        # Max score calculation: 6x7=42 cells. 1 is occupied by random start.
        # Max possible empty cells = 41.
        match_stats[winner_name]["score"] += 41 
        match_stats[loser_name]["losses"] += 1
        match_stats[loser_name]["score"] -= 41
        
        print("Final Position: N/A (initialization crash)")
        print("----------------------------------------")
        print(f"Final Result: {{winner_name}} wins. (opponent crashed)")
        print("----------------------------------------")
        print("Points:")
        print(f"{{winner_name}}: 3")
        print(f"{{loser_name}}: 0")
        print("----------------------------------------")
        print("Scores:")
        print(f"{{winner_name}}: 41")
        print(f"{{loser_name}}: -41")
        print("============================================================")
        return winner_name



    agents = {{game.RED: agent_red, game.YELLOW: agent_yellow}}
    names = {{game.RED: red_name, game.YELLOW: yellow_name}}


    while True:


        current_symbol = game.current_turn
        current_agent = agents[current_symbol]
        current_name = names[current_symbol]
        
        # Deep copy board for agent
        board_copy = [row[:] for row in game.board]
        
        move = None
        error_type = None

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(MOVE_TIMEOUT))
            try:
                move = current_agent.make_move(board_copy)
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            match_stats[current_name]["timeout"] += 1
            error_type = "timeout"
            print(f"{{current_name}} TIMEOUT")
        except Exception as e:
            match_stats[current_name]["make_move_crash"] += 1
            error_type = "crash"
            print(f"{{current_name}} CRASH: {{e}}")

        # Validate move type
        if error_type is None and (move is None or not isinstance(move, int)):
            match_stats[current_name]["invalid"] += 1
            error_type = "invalid"
            print(f"{{current_name}} INVALID MOVE TYPE: {{move}}")

        # Validate logic (column full logic checked in game.drop_disc usually, but we check bounds here)
        if error_type is None:
             if not (0 <= move < game.COLS):
                match_stats[current_name]["invalid"] += 1
                error_type = "invalid"
                print(f"{{current_name}} INVALID MOVE (OOB): {{move}}")
             elif game.board[0][move] != game.EMPTY:
                match_stats[current_name]["invalid"] += 1
                error_type = "invalid"
                print(f"{{current_name}} INVALID MOVE (FULL): {{move}}")

        # Fallback to random if error
        if error_type is not None:
             # Pick random valid column
             valid_cols = [c for c in range(game.COLS) if game.board[0][c] == game.EMPTY]
             if valid_cols:
                 move = random.choice(valid_cols)
                 print(f"{{current_name}} FALLBACK: Random move {{move}}")
             else:
                 # Should not happen unless board is full, which is checked below
                 break

        # Apply move
        if move is not None:
            game.drop_disc(move, current_symbol)
            print(f"{{current_name}} moves {{move}}")
        
        # Check Winner
        win_info = game.check_winner() # Returns (winner, start, end) or None
        winner = win_info[0] if win_info else None
        
        is_full = game.is_full()
        
        if winner or is_full:
            print("Final Position:")
            print_board_log(game.board)
            if winner:
                print()
                print(f"Successfull 4 disc start and end positions: {{win_info[1]}} {{win_info[2]}}")
            print("----------------------------------------")
            
            empty_cells = sum(row.count(game.EMPTY) for row in game.board)
            score_val = max(empty_cells, 3)
            
            if winner: # 'R' or 'Y'
                winner_name = names[winner]
                loser_symbol = game.YELLOW if winner == game.RED else game.RED
                loser_name = names[loser_symbol]
                
                print(f"Final Result: {{winner_name}} wins!")
                print("----------------------------------------")
                print("Points:")
                print(f"{{winner_name}}: 3")
                print(f"{{loser_name}}: 0")
                print("----------------------------------------")
                print("Scores:")
                print(f"{{winner_name}}: {{score_val}}")
                print(f"{{loser_name}}: -{{score_val}}")
                print("============================================================")
                
                match_stats[winner_name]["wins"] += 1
                match_stats[winner_name]["points"] += 3
                match_stats[winner_name]["score"] += score_val
                match_stats[loser_name]["losses"] += 1
                match_stats[loser_name]["score"] -= score_val
                
                return winner_name
            else: # Draw
                print("Final Result: Draw")
                print("----------------------------------------")
                print("Points:")
                print("Agent-1: 1")
                print("Agent-2: 1")
                print("----------------------------------------")
                print("Scores:")
                print("Agent-1: 0")
                print("Agent-2: 0")
                print("============================================================")
                
                match_stats["Agent-1"]["draws"] += 1
                match_stats["Agent-1"]["points"] += 1
                match_stats["Agent-2"]["draws"] += 1
                match_stats["Agent-2"]["points"] += 1
                
                return "DRAW"
        
        # Switch turn
        game.current_turn = game.YELLOW if game.current_turn == game.RED else game.RED

def main():
    match_stats = {{
        "Agent-1": {{
            "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0
        }},
        "Agent-2": {{
            "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0
        }}
    }}
    
    num_games = {num_games}
    
    # Not using standard logging logger in subprocess for simplicity, just print
    # print(f"Match Contenders:")
    # print(f"{{AGENT1_NAME}}")
    # print(f"{{AGENT2_NAME}}")
    # print()

    for i in range(num_games):
        play_game(i + 1, match_stats)
        sys.stdout.flush()

    # Aggregate crash stats
    for agent in ["Agent-1", "Agent-2"]:
        match_stats[agent]['crash'] = match_stats[agent]['make_move_crash'] + match_stats[agent]['other_crash']

    # Final Output
    # Final Output
    print("=" * 60)
    print("=" * 60)
    print(f"Agent-1: {{AGENT1_NAME}}")
    print(f"Agent-2: {{AGENT2_NAME}}")
    print(f"RESULT:Agent-1={{match_stats['Agent-1']['points']}},Agent-2={{match_stats['Agent-2']['points']}}")
    print(f"SCORE:Agent-1={{match_stats['Agent-1']['score']}},Agent-2={{match_stats['Agent-2']['score']}}")
    print(f"WINS:Agent-1={{match_stats['Agent-1']['wins']}},Agent-2={{match_stats['Agent-2']['wins']}}")
    print(f"DRAWS:{{match_stats['Agent-1']['draws']}}")
    print(f"STATS:Agent-1={{match_stats['Agent-1']}}")
    print(f"STATS:Agent-2={{match_stats['Agent-2']}}")
    
    print()
    print("--- MATCH STATISTICS ---")
    print(f"Agent-1 make_move_crash: {{match_stats['Agent-1']['make_move_crash']}}")
    print(f"Agent-2 make_move_crash: {{match_stats['Agent-2']['make_move_crash']}}")
    print(f"Agent-1 other_crash: {{match_stats['Agent-1']['other_crash']}}")
    print(f"Agent-2 other_crash: {{match_stats['Agent-2']['other_crash']}}")
    print(f"Agent-1 Timeouts: {{match_stats['Agent-1']['timeout']}}")
    print(f"Agent-2 Timeouts: {{match_stats['Agent-2']['timeout']}}")
    print(f"Agent-1 Invalid: {{match_stats['Agent-1']['invalid']}}")
    print(f"Agent-2 Invalid: {{match_stats['Agent-2']['invalid']}}")
    print("------------------------------------------------------------")

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
        # Capture BOTH stdout and stderr
        result = subprocess.run(["python", temp_file], capture_output=True, text=True)
        
        # If the return code is non-zero, or stdout is empty but stderr has content, return the error
        if result.returncode != 0:
             return f"CRASH: {result.stderr}"
        
        return result.stdout
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

async def run_match_async(game_code: str, match_id: int, run_ids: tuple[int, int], folder1: str, folder2: str):
    """Run a single match and return the score."""
    output = await asyncio.get_event_loop().run_in_executor(None, run_match, game_code)
    
    res_match = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", output)
    
    if res_match:
        wins_match = re.search(r"WINS:Agent-1=(\d+),Agent-2=(\d+)", output)
        draws_match = re.search(r"DRAWS:(\d+)", output)
        score_match = re.search(r"SCORE:Agent-1=(-?[\d.]+),Agent-2=(-?[\d.]+)", output)
        
        agent1_wins = int(wins_match.group(1)) if wins_match else 0
        agent2_wins = int(wins_match.group(2)) if wins_match else 0
        draws = int(draws_match.group(1)) if draws_match else 0
        agent1_points = int(float(res_match.group(1)))
        agent2_points = int(float(res_match.group(2)))
        agent1_score = float(score_match.group(1)) if score_match else 0.0
        agent2_score = float(score_match.group(2)) if score_match else 0.0

        return {
            "success": True, 
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "agent1_wins": agent1_wins,
            "agent2_wins": agent2_wins,
            "draws": draws,
            "agent1_points": agent1_points,
            "agent2_points": agent2_points,
            "agent1_score": agent1_score,
            "agent2_score": agent2_score,
            "log": output
        }
    else:
        return {"success": False, "error": "Result parsing failed", "match_id": match_id, "log": output}


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
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    agent_suffix = f"{folder1}_vs_{folder2}"
    log_f = RESULTS_DIR / f"{ts}_{agent_suffix}_match.txt"

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

            agent1_name=f"{folder1}:{run1}",
            agent2_name=f"{folder2}:{run2}"
        )
        
        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2), folder1, folder2))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)
    
    # Sort results by match_id for consistent output
    results.sort(key=lambda x: x["match_id"])
    
    total1, total2 = 0.0, 0.0
    
    # Open file for writing (overwrite)
    with open(log_f, "w") as f:
        # Header
        f.write(f"Match Contenders:\n")
        if runs1:
             f.write(f"{folder1}:{runs1[0]}\n")
        if runs2:
             f.write(f"{folder2}:{runs2[0]}\n\n")

        for res in results:
            m_id = res["match_id"]
            r1, r2 = runs1[m_id-1], runs2[m_id-1]
            
            if res["success"]:
                a1_pts, a2_pts = res["agent1_points"], res["agent2_points"]
                total1 += a1_pts
                total2 += a2_pts
                
                print(f"  Match {m_id} ({folder1}:{r1} vs {folder2}:{r2}): {a1_pts} - {a2_pts}")
                
                 # Result section for log
                status = "Result:\n"
                status += f"{folder1}:{res['agent1_run_id']} : Pts: {res['agent1_points']} - Score: {res['agent1_score']}\n"
                status += f"{folder2}:{res['agent2_run_id']} : Pts: {res['agent2_points']} - Score: {res['agent2_score']}\n"
                
                if res.get("log"):
                    status += f"\n{res['log'].strip()}"

                f.write(f"{status}\n")
                
                # SCOREBOARD INTEGRATION
                # Agent 1
                agent1_key = f"{folder1}:{res['agent1_run_id']}"
                update_scoreboard(
                    SCOREBOARD_PATH, agent1_key,
                    games_played=NUM_ROUNDS_PER_MATCH,
                    wins=res["agent1_wins"],
                    losses=res["agent2_wins"],
                    draws=res["draws"],
                    score=res["agent1_score"],
                    points=res["agent1_points"]
                )
                
                # Agent 2
                agent2_key = f"{folder2}:{res['agent2_run_id']}"
                update_scoreboard(
                    SCOREBOARD_PATH, agent2_key,
                    games_played=NUM_ROUNDS_PER_MATCH,
                    wins=res["agent2_wins"],
                    losses=res["agent1_wins"],
                    draws=res["draws"],
                    score=res["agent2_score"],
                    points=res["agent2_points"]
                )
                
            else:
                print(f"  Match {m_id} ({folder1}:{r1} vs {folder2}:{r2}): FAILED - {res.get('error')}")
                f.write(f"FAILED Match {m_id}: {res.get('error')}\n")
                if res.get("log"):
                     f.write(f"\nLog:\n{res['log']}\n")

    print("\nFINAL RESULTS:")
    print(f"  {folder1}: {total1}")
    print(f"  {folder2}: {total2}")
    print(f"\nLogs saved to: {log_f}")

if __name__ == "__main__":
    asyncio.run(main_async())
