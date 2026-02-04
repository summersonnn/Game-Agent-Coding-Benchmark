"""
Battleship Match Runner: Orchestrates head-to-head matches between two AI models.

Loads pre-generated agents from the agents/ folder, matches them in pairs,
runs games, and reports win/loss statistics.
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

from model_api import ModelAPI
from logging_config import setup_logging

logger = setup_logging(__name__)

# Load environment variables
load_dotenv()

# Configuration
try:
    NUM_ROUNDS_PER_BATTLESHIP_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    NUM_ROUNDS_PER_BATTLESHIP_MATCH = 100

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

BOARD_SIZE = 8
SHIPS = [5, 4, 3]

# Results directories
BATTLESHIP_RESULTS_DIR = Path(__file__).parent.parent / "results" / "battleship"
GAME_LOGS_DIR = BATTLESHIP_RESULTS_DIR / "game_logs"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A1-Battleship"

# The game code template with placeholders for agent implementations
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal
from collections import deque

# Move timeout in seconds
MOVE_TIMEOUT = {move_timeout}

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

# --- Game Configuration ---
BOARD_SIZE = {board_size}
SHIPS = {ships_config}
NUM_GAMES = {num_games}

# --- Board Representations ---
EMPTY = 'O'
SHIP = 'S'
HIT = 'X'
SUNK = '#'
MISS = 'M'

{extra_imports}

{agent1_code}

{agent2_code}


class BattleshipGame:
    """Manages the state and rules of the game."""
    def __init__(self, size, ships_config):
        self.size = size
        self.ships_config = ships_config
        self.player1_ships_board = self._create_ship_board()
        self.player2_ships_board = self._create_ship_board()

    def _create_empty_board(self):
        return [[EMPTY for _ in range(self.size)] for _ in range(self.size)]

    def _create_ship_board(self):
        """Creates a board and places ships on it."""
        board = self._create_empty_board()
        for length in self.ships_config:
            placed = False
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                r = random.randint(0, self.size - (length if orientation == 'vertical' else 1))
                c = random.randint(0, self.size - (length if orientation == 'horizontal' else 1))
                
                if orientation == 'horizontal':
                    if all(board[r][c+i] == EMPTY for i in range(length)):
                        for i in range(length): board[r][c+i] = SHIP
                        placed = True
                else:
                    if all(board[r+i][c] == EMPTY for i in range(length)):
                        for i in range(length): board[r+i][c] = SHIP
                        placed = True
        return board

    def is_game_over(self, ships_board):
        """Checks if all ships on a given board have been sunk."""
        return not any(SHIP in row for row in ships_board)


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

def play_game(game_num, scores):
    """Plays a single game of Battleship and returns the winner's name or crash info."""
    game = BattleshipGame(BOARD_SIZE, SHIPS)
    
    # Try to initialize agents - if one fails, the other wins
    try:
        agent1 = BattleshipAgent_1("Agent-1", BOARD_SIZE, SHIPS)
    except Exception as e:
        return ("Agent-2", "Crash during init (Agent-1): " + str(e)[:100])
    
    try:
        agent2 = BattleshipAgent_2("Agent-2", BOARD_SIZE, SHIPS)
    except Exception as e:
        return ("Agent-1", "Crash during init (Agent-2): " + str(e)[:100])
    
    p1_active_board = [row[:] for row in game.player1_ships_board]
    p2_active_board = [row[:] for row in game.player2_ships_board]
    p1_guess_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    p2_guess_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    players = {{
        agent1: {{'opponent_ships_board': p2_active_board, 'guess_board': p1_guess_board}},
        agent2: {{'opponent_ships_board': p1_active_board, 'guess_board': p2_guess_board}}
    }}
    current_agent, opponent_agent = agent1, agent2
    
    last_shot_coord, last_shot_result = None, None
    turn_continues = False
    move_count = 0
    max_moves = BOARD_SIZE * BOARD_SIZE * 2  # Max moves before draw

    while True:
        move_count += 1
        if move_count > max_moves:
            # Game exceeded max moves - return draw
            stats["draw"] += 1
            return "DRAW"
        
        # Try to get move with timeout - if timeout or crash, use random move
        move = None
        sunk_coords = []
        
        try:
            # Set up signal-based timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            # signal.alarm() requires an integer, use max(1, ...) to ensure at least 1 second
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            
            try:
                move_data = current_agent.make_move(last_shot_result, last_shot_coord)
                if isinstance(move_data, tuple) and len(move_data) == 2:
                    move, sunk_coords = move_data
                else:
                    move, sunk_coords = move_data, []
            finally:
                # Always disable the alarm
                signal.alarm(0)
                
        except MoveTimeoutException:
            # Agent took too long - use random move (any cell)
            move = (random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1))
            sunk_coords = []
            if current_agent.name == "Agent-1": stats["r1_timeout"] += 1
            else: stats["r2_timeout"] += 1
        except Exception as e:
            # Agent crashed - use random move
            move = (random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1))
            sunk_coords = []
            if current_agent.name == "Agent-1": stats["r1_crash"] += 1
            else: stats["r2_crash"] += 1
        
        if move is None:
            # Agent returned None - use random move
            move = (random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1))
            if current_agent.name == "Agent-1": stats["r1_invalid"] += 1
            else: stats["r2_invalid"] += 1
        
        # Validate move coordinates
        try:
            row, col = move
            if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
                # Invalid coordinates - use random move
                row, col = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
                if current_agent.name == "Agent-1": stats["r1_invalid"] += 1
                else: stats["r2_invalid"] += 1
        except Exception:
            row, col = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
            if current_agent.name == "Agent-1": stats["r1_invalid"] += 1
            else: stats["r2_invalid"] += 1
            
        p_data = players[current_agent]
        opponent_ships_board, guess_board = p_data['opponent_ships_board'], p_data['guess_board']
        
        result = opponent_ships_board[row][col]
        
        if result == SHIP:
            opponent_ships_board[row][col] = HIT
            guess_board[row][col] = HIT
            last_shot_result = 'HIT'
            turn_continues = True
        else:
            guess_board[row][col] = MISS
            last_shot_result = 'MISS'
            turn_continues = False
        
        last_shot_coord = move

        if sunk_coords:
            for r, c in sunk_coords:
                guess_board[r][c] = SUNK

        if game.is_game_over(opponent_ships_board):
            stats["normal"] += 1
            return current_agent.name
        
        if not turn_continues:
            current_agent, opponent_agent = opponent_agent, current_agent
            last_shot_coord, last_shot_result = None, None


def main():
    """Main function to run the Battleship simulation."""
    scores = {{"Agent-1": 0, "Agent-2": 0}}
    crash_detected = None

    for i in range(NUM_GAMES):
        result = play_game(i + 1, scores)
        
        # Check if result is a crash tuple, draw, or just winner name
        if isinstance(result, tuple):
            winner, crash_msg = result
            crash_detected = crash_msg
            # Award ALL remaining games to the winner
            remaining = NUM_GAMES - i
            scores[winner] += remaining
            
            # Count crash for the loser
            if winner == "Agent-1": stats["c2"] += 1
            else: stats["c1"] += 1
            
            # Print intermediate progress before breaking
            print(f"PROGRESS:Agent-1={{scores['Agent-1']}},Agent-2={{scores['Agent-2']}},N={{stats['normal']}},D={{stats['draw']}},C1={{stats['c1']}},C2={{stats['c2']}},R1T={{stats['r1_timeout']}},R1C={{stats['r1_crash']}},R1I={{stats['r1_invalid']}},R2T={{stats['r2_timeout']}},R2C={{stats['r2_crash']}},R2I={{stats['r2_invalid']}}")
            sys.stdout.flush()
            break
        elif result == "DRAW":
            # Draw - both get 0.5 points
            scores["Agent-1"] += 0.5
            scores["Agent-2"] += 0.5
        else:
            winner = result
            if winner in scores:
                scores[winner] += 1
        
        # Print intermediate progress for partial result parsing on timeout
        print(f"PROGRESS:Agent-1={{scores['Agent-1']}},Agent-2={{scores['Agent-2']}},N={{stats['normal']}},D={{stats['draw']}},C1={{stats['c1']}},C2={{stats['c2']}},R1T={{stats['r1_timeout']}},R1C={{stats['r1_crash']}},R1I={{stats['r1_invalid']}},R2T={{stats['r2_timeout']}},R2C={{stats['r2_crash']}},R2I={{stats['r2_invalid']}}")
        sys.stdout.flush()
    
    print(f"RESULT:Agent-1={{scores['Agent-1']}},Agent-2={{scores['Agent-2']}}")
    print(f"STATS:Normal={{stats['normal']}},Draw={{stats['draw']}},C1={{stats['c1']}},C2={{stats['c2']}},R1T={{stats['r1_timeout']}},R1C={{stats['r1_crash']}},R1I={{stats['r1_invalid']}},R2T={{stats['r2_timeout']}},R2C={{stats['r2_crash']}},R2I={{stats['r2_invalid']}}")
    if crash_detected:
        print(f"CRASH:{{crash_detected}}")

if __name__ == "__main__":
    main()
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


def load_stored_agent(model_folder: str, game: str, run: int, agent_idx: int) -> tuple[str, str]:
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
    
    # Extract imports (before the class)
    imports = []
    class_start_idx = None
    
    for i, line in enumerate(code_lines):
        stripped = line.strip()
        
        # Find where BattleshipAgent class starts
        if stripped.startswith("class BattleshipAgent"):
            class_start_idx = i
            break
            
        # Collect imports before the class
        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped and "collections" not in stripped:
                imports.append(stripped)
    
    if class_start_idx is None:
        logger.error("No BattleshipAgent class found in %s", agent_file)
        return "", ""
    
    # Extract ONLY the BattleshipAgent class (stop at next top-level class/function/main)
    class_lines = []
    in_class = False
    base_indent = 0
    
    for i in range(class_start_idx, len(code_lines)):
        line = code_lines[i]
        stripped = line.strip()
        
        # Class definition line
        if i == class_start_idx:
            class_lines.append(line)
            in_class = True
            # Get the base indentation (should be 0 for top-level class)
            base_indent = len(line) - len(line.lstrip())
            continue
        
        # Always include empty lines and comments
        if not stripped or stripped.startswith("#"):
            class_lines.append(line)
            continue
        
        # Calculate current indentation
        current_indent = len(line) - len(line.lstrip())
        
        # Stop if we hit another top-level (or less indented) definition
        if current_indent <= base_indent:
            # This is a top-level statement - stop here
            break
            
        # We're still inside the class - add the line
        class_lines.append(line)
    
    agent_code = "\n".join(class_lines)
    
    # Rename BattleshipAgent to BattleshipAgent_{agent_idx}
    agent_code = re.sub(r"\bBattleshipAgent\b", f"BattleshipAgent_{agent_idx}", agent_code)
    
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
    num_games: int = NUM_ROUNDS_PER_BATTLESHIP_MATCH,
    board_size: int = BOARD_SIZE,
    ships_config: list[int] = SHIPS,
    move_timeout: float = MOVE_TIME_LIMIT,
) -> str:
    """Build the complete game code with both agent implementations."""
    return GAME_CODE_TEMPLATE.format(
        num_games=num_games,
        board_size=board_size,
        ships_config=ships_config,
        move_timeout=move_timeout,
        extra_imports=extra_imports,
        agent1_code=agent1_code,
        agent2_code=agent2_code,
    )


def run_match(game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = 900) -> dict:
    """
    Execute the match and parse results.

    Returns:
        Dict with keys: success, agent1_wins, agent2_wins, error, match_id, agent1_run_id, agent2_run_id
    """
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"battleship_match_{match_id}_{temp_id}.py"
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
                "agent1_wins": 0,
                "agent2_wins": 0,
                "error": result.stderr[:500],
            }

        # Parse results
        match = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout)
        if match:
            # Check for crash info
            crash_match = re.search(r"CRASH:(.+)", result.stdout)
            crash_info = crash_match.group(1) if crash_match else None
            
            # Parse stats
            stats = {
                "normal": 0, "draw": 0, "c1": 0, "c2": 0,
                "r1_timeout": 0, "r1_crash": 0, "r1_invalid": 0,
                "r2_timeout": 0, "r2_crash": 0, "r2_invalid": 0
            }
            stats_match = re.search(r"STATS:Normal=(\d+),Draw=(\d+),C1=(\d+),C2=(\d+),R1T=(\d+),R1C=(\d+),R1I=(\d+),R2T=(\d+),R2C=(\d+),R2I=(\d+)", result.stdout)
            if stats_match:
                stats = {
                    "normal": int(stats_match.group(1)),
                    "draw": int(stats_match.group(2)),
                    "c1": int(stats_match.group(3)),
                    "c2": int(stats_match.group(4)),
                    "r1_timeout": int(stats_match.group(5)),
                    "r1_crash": int(stats_match.group(6)),
                    "r1_invalid": int(stats_match.group(7)),
                    "r2_timeout": int(stats_match.group(8)),
                    "r2_crash": int(stats_match.group(9)),
                    "r2_invalid": int(stats_match.group(10)),
                }

            return {
                "match_id": match_id,
                "agent1_run_id": run_ids[0],
                "agent2_run_id": run_ids[1],
                "success": True,
                "agent1_wins": float(match.group(1)),
                "agent2_wins": float(match.group(2)),
                "error": None,
                "crash_info": crash_info,
                "stats": stats,
            }

        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": False,
            "agent1_wins": 0,
            "agent2_wins": 0,
            "error": "Could not parse results from output",
        }

    except Exception as e:
        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": False,
            "agent1_wins": 0,
            "agent2_wins": 0,
            "error": str(e),
        }
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def run_match_async(game_code: str, match_id: int, run_ids: tuple[int, int]) -> dict:
    """Run a match in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    parser = argparse.ArgumentParser(description="Run Battleship matches between stored AI agents")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4]")
    args = parser.parse_args()

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
    print("BATTLESHIP MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    BATTLESHIP_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
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
            print(f"  FAILED to load match {i+1}: Could not load agent code.")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_ROUNDS_PER_BATTLESHIP_MATCH, BOARD_SIZE, SHIPS, MOVE_TIME_LIMIT
        )
        
        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)
    
    # Process results and log
    total1, total2 = 0.0, 0.0
    
    with open(log_f, "w") as f:
        f.write(f"Battleship Stored Agent Match - {ts}\n")
        f.write("=" * 60 + "\n\n")
        
        for result in sorted(results, key=lambda x: x["match_id"]):
            match_id = result["match_id"]
            r1, r2 = result["agent1_run_id"], result["agent2_run_id"]
            
            if result["success"]:
                a1, a2 = result["agent1_wins"], result["agent2_wins"]
                total1 += a1
                total2 += a2
                status = f"Result: {a1} - {a2}"
                if result.get("crash_info"):
                    status += f" ({result['crash_info']})"
            else:
                status = f"FAILED: {result.get('error', 'Unknown error')}"
                
            print(f"  Match {match_id} ({folder1}:{r1} vs {folder2}:{r2}): {status}")
            f.write(f"Match {match_id}: {folder1} (run {r1}) vs {folder2} (run {r2})\n")
            f.write(f"{status}\n")
            if "stats" in result:
                f.write(f"Stats: {result['stats']}\n")
            f.write("-" * 40 + "\n\n")

    print("\nFINAL RESULTS:")
    print(f"  {folder1}: {total1}")
    print(f"  {folder2}: {total2}")
    print(f"\nLogs saved to: {log_f}")

if __name__ == "__main__":
    asyncio.run(main_async())
