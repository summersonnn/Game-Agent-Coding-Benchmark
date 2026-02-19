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

BOARD_SIZE = 8
SHIPS = [5, 4, 3]

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / "battleship"
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / "A1-scoreboard.txt"
AGENTS_DIR = BASE_DIR / "agents"


GAME_NAME = "A1-Battleship"

MODE_TITLES = {
    "humanvsbot": "Human vs Random Bot",
    "humanvshuman": "Human vs Human",
    "humanvsagent": "Human vs Stored Agent",
}


# The game code template with placeholders for agent implementations
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal
from collections import deque

# Move timeout in seconds
# Move timeout in seconds
MOVE_TIMEOUT = {move_timeout}
GAME_MODE = "{game_mode}"

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

# --- Game Configuration ---
BOARD_SIZE = {board_size}
SHIPS = {ships}
NUM_GAMES = {num_games}
# --- Board Representations ---
EMPTY = 'O'
SHIP = 'S'
HIT = 'X'
SUNK = '#'
MISS = 'M'

{extra_imports}

AGENT1_NAME = "{agent1_name}"
AGENT2_NAME = "{agent2_name}"

{agent1_code}

{agent2_code}

class RandomAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships
        self.shots = set()
        self.placed_coords = set()

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            # Random ship placement
            ship_length = state['ships_to_place'][0]
            board = state['my_board']

            while True:
                orientation = random.choice(['horizontal', 'vertical'])
                if orientation == 'horizontal':
                    r = random.randint(0, self.board_size - 1)
                    c = random.randint(0, self.board_size - ship_length)
                    coords = [(r, c + i) for i in range(ship_length)]
                else:
                    r = random.randint(0, self.board_size - ship_length)
                    c = random.randint(0, self.board_size - 1)
                    coords = [(r + i, c) for i in range(ship_length)]

                if all(board[r][c] == EMPTY for r, c in coords):
                    return {{
                        'ship_length': ship_length,
                        'start': coords[0],
                        'orientation': orientation
                    }}
        else:  # bombing phase
            while True:
                r = random.randint(0, self.board_size - 1)
                c = random.randint(0, self.board_size - 1)
                if (r, c) not in self.shots:
                    self.shots.add((r, c))
                    return {{'target': (r, c)}}

class HumanAgent:
    def __init__(self, name, board_size, ships):
        self.name = name
        self.board_size = board_size
        self.ships = ships

    def make_move(self, state, feedback):
        if state['phase'] == 'placement':
            ship_length = state['ships_to_place'][0]
            print(f"\\nPlace ship of length {{ship_length}}")
            while True:
                try:
                    user_input = input("Enter start (row col) and orientation (h/v): ").strip()
                    parts = user_input.split()
                    if len(parts) != 3:
                        print("Invalid format. Use 'row col orientation' (e.g., '0 0 h').")
                        continue
                    r, c = int(parts[0]), int(parts[1])
                    orientation = 'horizontal' if parts[2].lower() == 'h' else 'vertical'
                    return {{
                        'ship_length': ship_length,
                        'start': (r, c),
                        'orientation': orientation
                    }}
                except ValueError:
                    print("Invalid input.")
        else:  # bombing
            while True:
                try:
                    user_input = input(f"Enter move (row col) [0-{{self.board_size-1}}]: ").strip()
                    if not user_input: continue
                    parts = user_input.split()
                    if len(parts) != 2:
                        print("Invalid format. Use 'row col' (e.g., '0 0').")
                        continue
                    r, c = map(int, parts)
                    if 0 <= r < self.board_size and 0 <= c < self.board_size:
                        return {{'target': (r, c)}}
                    else:
                        print("Coordinates out of bounds.")
                except ValueError:
                    print("Invalid input. Please enter integers.")


def validate_ship_placement(placement, board, board_size, expected_length):
    """
    Validates a ship placement. Returns (is_valid, error_code, error_message).

    placement: dict with keys 'ship_length', 'start' (row, col), 'orientation'
    board: current board state (2D list)
    board_size: size of the board
    expected_length: the ship length we expect to place
    """
    try:
        ship_length = placement.get('ship_length')
        start = placement.get('start')
        orientation = placement.get('orientation')

        # Check format
        if not isinstance(ship_length, int) or not isinstance(start, (tuple, list)) or orientation not in ['horizontal', 'vertical']:
            return False, 'INVALID_FORMAT', 'Placement must have ship_length (int), start (row, col), and orientation (horizontal/vertical)'

        if len(start) != 2:
            return False, 'INVALID_FORMAT', 'Start coordinates must be (row, col)'

        row, col = start

        # Check ship length matches expected
        if ship_length != expected_length:
            return False, 'WRONG_SHIP_LENGTH', f'Expected ship length {{expected_length}}, got {{ship_length}}'

        # Calculate ship coordinates
        if orientation == 'horizontal':
            coords = [(row, col + i) for i in range(ship_length)]
        else:  # vertical
            coords = [(row + i, col) for i in range(ship_length)]

        # Check bounds
        for r, c in coords:
            if not (0 <= r < board_size and 0 <= c < board_size):
                return False, 'OUT_OF_BOUNDS', f'Ship extends outside board ({{r}}, {{c}}) is invalid'

        # Check intersections
        for r, c in coords:
            if board[r][c] != EMPTY:
                return False, 'SHIP_INTERSECTION', f'Ship intersects with already placed ship at ({{r}}, {{c}})'

        return True, None, None

    except Exception as e:
        return False, 'INVALID_FORMAT', f'Error parsing placement: {{str(e)}}'


def place_ship_randomly(board, ship_length, board_size):
    """Place a ship randomly on the board, avoiding existing ships."""
    # Detect all empty cells
    empty_cells = []
    for r in range(board_size):
        for c in range(board_size):
            if board[r][c] == EMPTY:
                empty_cells.append((r, c))
    
    # Randomly shuffle empty cells to try them in random order
    random.shuffle(empty_cells)
    tried_cells = set()
    
    for cell in empty_cells:
        if cell in tried_cells:
            continue
        
        tried_cells.add(cell)
        r, c = cell
        
        # Try both orientations for this cell
        orientations = ['horizontal', 'vertical']
        random.shuffle(orientations)
        
        for orientation in orientations:
            if orientation == 'horizontal':
                # Check if ship fits horizontally from this cell
                if c + ship_length <= board_size:
                    coords = [(r, c + i) for i in range(ship_length)]
                    if all(board[r][c] == EMPTY for r, c in coords):
                        for r, c in coords:
                            board[r][c] = SHIP
                        return coords
            else:  # vertical
                # Check if ship fits vertically from this cell
                if r + ship_length <= board_size:
                    coords = [(r + i, c) for i in range(ship_length)]
                    if all(board[r][c] == EMPTY for r, c in coords):
                        for r, c in coords:
                            board[r][c] = SHIP
                        return coords
    
    return None


class BattleshipGame:
    """Manages the state and rules of the game."""
    def __init__(self, size, ships):
        self.size = size
        self.ships = ships

    def _create_empty_board(self):
        return [[EMPTY for _ in range(self.size)] for _ in range(self.size)]

    def is_game_over(self, ships_board):
        """Checks if all ships on a given board have been sunk."""
        return not any(SHIP in row for row in ships_board)


# --- Stats ---

def play_game(game_num, match_stats):
    """Plays a single game of Battleship and returns the winner's name or crash info, and the winning score."""
    game = BattleshipGame(BOARD_SIZE, SHIPS)

    # Try to initialize agents
    if GAME_MODE == "humanvsbot":
        # Alternate Human assignment each game
        if game_num % 2 == 1:
             try:
                agent1 = HumanAgent(AGENT1_NAME, BOARD_SIZE, SHIPS)
             except Exception as e:
                return (AGENT2_NAME, "Crash during init (Human): " + str(e)[:100]), 0
             try:
                agent2 = RandomAgent(AGENT2_NAME, BOARD_SIZE, SHIPS)
             except Exception as e:
                 return (AGENT1_NAME, "Crash during init (RandomBot): " + str(e)[:100]), 0
        else:
             try:
                agent1 = RandomAgent(AGENT1_NAME, BOARD_SIZE, SHIPS)
             except Exception as e:
                 return (AGENT2_NAME, "Crash during init (RandomBot): " + str(e)[:100]), 0
             try:
                agent2 = HumanAgent(AGENT2_NAME, BOARD_SIZE, SHIPS)
             except Exception as e:
                return (AGENT1_NAME, "Crash during init (Human): " + str(e)[:100]), 0

    elif GAME_MODE == "humanvshuman":
        try:
            agent1 = HumanAgent(AGENT1_NAME, BOARD_SIZE, SHIPS)
        except Exception as e:
            return (AGENT2_NAME, "Crash during init (Player 1): " + str(e)[:100]), 0
        try:
            agent2 = HumanAgent(AGENT2_NAME, BOARD_SIZE, SHIPS)
        except Exception as e:
            return (AGENT1_NAME, "Crash during init (Player 2): " + str(e)[:100]), 0

    elif GAME_MODE == "humanvsagent":
         # One agent is human, other is loaded from file (BattleshipAgent_1)
         # Alternate assignment each game
         if game_num % 2 == 1:
              try:
                 agent1 = HumanAgent(AGENT1_NAME, BOARD_SIZE, SHIPS)
              except Exception as e:
                 return (AGENT2_NAME, "Crash during init (Human): " + str(e)[:100]), 0
              try:
                 agent2 = BattleshipAgent_1(AGENT2_NAME, BOARD_SIZE, SHIPS)
              except Exception as e:
                  return (AGENT1_NAME, "Crash during init (Agent): " + str(e)[:100]), 0
         else:
              try:
                 agent1 = BattleshipAgent_1(AGENT1_NAME, BOARD_SIZE, SHIPS)
              except Exception as e:
                  return (AGENT2_NAME, "Crash during init (Agent): " + str(e)[:100]), 0
              try:
                 agent2 = HumanAgent(AGENT2_NAME, BOARD_SIZE, SHIPS)
              except Exception as e:
                 return (AGENT1_NAME, "Crash during init (Human): " + str(e)[:100]), 0

    else: # Agent vs Agent (default)
        try:
            agent1 = BattleshipAgent_1(AGENT1_NAME, BOARD_SIZE, SHIPS)
        except Exception as e:
            return (AGENT2_NAME, "Crash during init (Agent-1): " + str(e)[:100]), 0

        try:
            agent2 = BattleshipAgent_2(AGENT2_NAME, BOARD_SIZE, SHIPS)
        except Exception as e:
            return (AGENT1_NAME, "Crash during init (Agent-2): " + str(e)[:100]), 0

    # Create empty boards for both players
    p1_ships_board = game._create_empty_board()
    p2_ships_board = game._create_empty_board()

    # --- PLACEMENT PHASE ---
    p1_ships_coords = []
    p2_ships_coords = []
    agents_setup = [
        (agent1, p1_ships_board, AGENT1_NAME, p1_ships_coords),
        (agent2, p2_ships_board, AGENT2_NAME, p2_ships_coords)
    ]

    for agent, board, agent_name, ship_tracker in agents_setup:
        remaining_ships = list(SHIPS)

        for i, ship_length in enumerate(remaining_ships):
            placement_successful = False

            state = {{
                'phase': 'placement',
                'board_size': BOARD_SIZE,
                'ships_to_place': remaining_ships[i:],
                'ships_placed': i,
                'my_board': [row[:] for row in board]
            }}

            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(max(1, int(MOVE_TIMEOUT)))

                try:
                    placement = agent.make_move(state, None)
                finally:
                    signal.alarm(0)

                # Validate placement
                is_valid, error_code, error_message = validate_ship_placement(
                    placement, board, BOARD_SIZE, ship_length
                )

                if is_valid:
                    # Place the ship
                    start = placement['start']
                    orientation = placement['orientation']
                    if orientation == 'horizontal':
                        coords = [(start[0], start[1] + j) for j in range(ship_length)]
                    else:
                        coords = [(start[0] + j, start[1]) for j in range(ship_length)]

                    for r, c in coords:
                        board[r][c] = SHIP
                    ship_tracker.append(coords)

                    placement_successful = True
                else:
                    if agent_name == AGENT1_NAME:
                        match_stats[AGENT1_NAME]["invalid"] += 1
                    else:
                        match_stats[AGENT2_NAME]["invalid"] += 1

            except MoveTimeoutException:
                if agent_name == AGENT1_NAME:
                    match_stats[AGENT1_NAME]["timeout"] += 1
                else:
                    match_stats[AGENT2_NAME]["timeout"] += 1
            except Exception as e:
                if agent_name == AGENT1_NAME:
                    match_stats[AGENT1_NAME]["make_move_crash"] += 1
                else:
                    match_stats[AGENT2_NAME]["make_move_crash"] += 1

            if not placement_successful:
                ship_coords = place_ship_randomly(board, ship_length, BOARD_SIZE)
                if ship_coords is None:
                    opponent_name = AGENT2_NAME if agent_name == AGENT1_NAME else AGENT1_NAME
                    return (opponent_name, f"Forfeit: Impossible board state for random placement of ship length {{ship_length}}"), 0
                ship_tracker.append(ship_coords)

    # --- BOMBING PHASE ---
    p1_guess_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    p2_guess_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    players = {{
        agent1: {{
            'opponent_ships_board': p2_ships_board,
            'guess_board': p1_guess_board,
            'opponent_ships': p2_ships_coords,
            'last_shot_coord': None,
            'last_shot_result': None,
            'shot_history': []
        }},
        agent2: {{
            'opponent_ships_board': p1_ships_board,
            'guess_board': p2_guess_board,
            'opponent_ships': p1_ships_coords,
            'last_shot_coord': None,
            'last_shot_result': None,
            'shot_history': []
        }}
    }}

    # Alternate who shoots first each game
    if game_num % 2 == 1:
        current_agent, opponent_agent = agent1, agent2
    else:
        current_agent, opponent_agent = agent2, agent1
    
    turn_continues = False
    move_count = 0
    # --- HUMAN MODE VISUALIZATION HELPER ---
    def print_state(player_agent, opponent_agent, players):
        if not isinstance(player_agent, HumanAgent):
             return # Only show for human

        p_data = players[player_agent]
        opp_data = players[opponent_agent]
        
        # We want to show:
        # 1. Human's hits/misses on enemy (guess_board)
        # 2. Human's ships and enemy hits on them (opponent_ships_board for the enemy is current agent's ships?)
        # Wait. 
        # players[current] has 'opponent_ships_board' (the board they are shooting AT)
        # players[opponent] has 'opponent_ships_board' (the board the opponent is shooting AT -> which is CURRENT agent's ships)
        
        my_ships = players[opponent_agent]['opponent_ships_board'] 
        my_guesses = players[player_agent]['guess_board']
        
        # Also, for full state, we might want to see the ENEMY ships (cheating/debug mode) as requested: "full state info"
        enemy_ships = players[player_agent]['opponent_ships_board'] 

        print(f"")
        print(f"--- Turn: {{player_agent.name}} ---")
        print("   YOUR SHIPS (S=Ship, X=Hit, O=Empty)       YOUR GUESSES (X=Hit, M=Miss, #=Sunk)")
        print("   0 1 2 3 4 5 6 7                           0 1 2 3 4 5 6 7")
        for r in range(BOARD_SIZE):
            # Your ships
            row1 = []
            for c in range(BOARD_SIZE):
                cell = my_ships[r][c]
                row1.append(cell)
            
            # Your guesses
            row2 = []
            for c in range(BOARD_SIZE):
                cell = my_guesses[r][c]
                row2.append(cell) # X, M, # or O (empty)

            print(f"{{r}}  {{' '.join(row1)}}                         {{r}}  {{' '.join(row2)}}")


    max_moves = BOARD_SIZE * BOARD_SIZE * 2
    
    while True:
        move_count += 1
        
        if GAME_MODE != "":
             print_state(current_agent, opponent_agent, players)

        if move_count > max_moves:
            # Game exceeded max moves - return draw
            return "DRAW", 0
        
        # Create state for bombing phase
        p_data = players[current_agent]
        state = {{
            'phase': 'bombing',
            'board_size': BOARD_SIZE,
            'last_shot_result': p_data['last_shot_result'],
            'last_shot_coord': p_data['last_shot_coord'],
            'shot_history': [h.copy() for h in p_data['shot_history']],
            'turn_continues': turn_continues
        }}

        # Try to get move with timeout
        move = None

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))

            try:
                move_data = current_agent.make_move(state, None)

                # Parse response - support dict and list/tuple formats
                if isinstance(move_data, dict):
                    move = move_data.get('target')
                elif isinstance(move_data, (tuple, list)) and len(move_data) >= 2:
                    if isinstance(move_data[0], (int, float)):
                        # Format: (row, col)
                        move = move_data
                    elif isinstance(move_data[0], (tuple, list)):
                        # Format: ((row, col), ...) for backward compatibility
                        move = move_data[0]
                elif isinstance(move_data, (tuple, list)) and len(move_data) == 1:
                    # Format: [(row, col)]
                    move = move_data[0]
                else:
                    move = None

            finally:
                signal.alarm(0)

        except MoveTimeoutException:
            move = None
            if current_agent.name == AGENT1_NAME: match_stats[AGENT1_NAME]["timeout"] += 1
            else: match_stats[AGENT2_NAME]["timeout"] += 1
        except Exception as e:
            move = None
            if current_agent.name == AGENT1_NAME: match_stats[AGENT1_NAME]["make_move_crash"] += 1
            else: match_stats[AGENT2_NAME]["make_move_crash"] += 1

        # Validate and fallback to random if invalid
        if move is None or not isinstance(move, (tuple, list)) or len(move) != 2:
            move = (random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1))
            if current_agent.name == AGENT1_NAME: match_stats[AGENT1_NAME]["invalid"] += 1
            else: match_stats[AGENT2_NAME]["invalid"] += 1
        else:
            try:
                row, col = move
                if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
                    move = (random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1))
                    if current_agent.name == AGENT1_NAME: match_stats[AGENT1_NAME]["invalid"] += 1
                    else: match_stats[AGENT2_NAME]["invalid"] += 1
            except Exception:
                move = (random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1))
                if current_agent.name == AGENT1_NAME: match_stats[AGENT1_NAME]["invalid"] += 1
                else: match_stats[AGENT2_NAME]["invalid"] += 1

        row, col = move
            
        opponent_ships_board, guess_board = p_data['opponent_ships_board'], p_data['guess_board']
        opponent_ships = p_data['opponent_ships']

        result = opponent_ships_board[row][col]

        if result == SHIP:
            opponent_ships_board[row][col] = HIT
            guess_board[row][col] = HIT
            last_shot_result = 'HIT'
            turn_continues = True

            # Auto-detect if ship is fully sunk for visualization
            for ship in opponent_ships:
                if (row, col) in ship:
                    if all(opponent_ships_board[r][c] == HIT for r, c in ship):
                        # Mark as sunk on boards
                        for r, c in ship:
                            opponent_ships_board[r][c] = SUNK
                            guess_board[r][c] = SUNK
                    break
        elif result in [HIT, SUNK]:
            # Already hit, return 'MISS' to agent and end turn (waste of move)
            last_shot_result = 'MISS'
            turn_continues = False
        else:
            if guess_board[row][col] == EMPTY:
                guess_board[row][col] = MISS
            last_shot_result = 'MISS'
            turn_continues = False
        
        # Update agent's history and last shot info
        p_data['last_shot_coord'] = move
        p_data['last_shot_result'] = last_shot_result
        p_data['shot_history'].append({{
            'coord': move,
            'result': last_shot_result
        }})

        if game.is_game_over(opponent_ships_board):
            # Calculate winner's score (remaining ship segments)
            # Current agent wins; calculate points from their remaining ships.
            # Winner's ships are found in players[opponent_agent]['opponent_ships_board'].
            
            opponent_agent = agent2 if current_agent == agent1 else agent1
            my_ships_board = players[opponent_agent]['opponent_ships_board']
            score = sum(row.count(SHIP) for row in my_ships_board)

            # Print final board state
            print("Final Position:")
            print(f"BOARD: {{AGENT1_NAME}} Ships:")
            print("BOARD:    0 1 2 3 4 5 6 7")
            for r in range(BOARD_SIZE):
                print(f"BOARD: {{r}}  {{' '.join(p1_ships_board[r])}}")
            print()
            print(f"BOARD: {{AGENT2_NAME}} Ships:")
            print("BOARD:    0 1 2 3 4 5 6 7")
            for r in range(BOARD_SIZE):
                print(f"BOARD: {{r}}  {{' '.join(p2_ships_board[r])}}")

            return current_agent.name, score
        
        if not turn_continues:
            current_agent, opponent_agent = opponent_agent, current_agent


def main():
    """Main function to run the Battleship simulation."""
    match_stats = {{
        AGENT1_NAME: {{"wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0, "make_move_crash": 0, "other_crash": 0, "crash": 0, "timeout": 0, "invalid": 0}},
        AGENT2_NAME: {{"wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0, "make_move_crash": 0, "other_crash": 0, "crash": 0, "timeout": 0, "invalid": 0}},
    }}
    
    for i in range(NUM_GAMES):
        print("=" * 60)
        print(f"Game {{i+1}}")
        print(f"Agent-1: {{AGENT1_NAME}}")
        print(f"Agent-2: {{AGENT2_NAME}}")
        print("-" * 60)
        
        result, game_score = play_game(i + 1, match_stats)
        
        if isinstance(result, tuple): # Crash
            winner_id, crash_msg = result
            
            # Record statistics for the crash game
            # The crasher loses, the other wins
            winner_id_key = winner_id
            loser_id_key = AGENT2_NAME if winner_id == AGENT1_NAME else AGENT1_NAME
            
            match_stats[winner_id_key]["wins"] += 1
            match_stats[winner_id_key]["points"] += 3
            match_stats[loser_id_key]["losses"] += 1
            # Crash score (max possible score for winner, negative for loser)
            max_score = sum(SHIPS)
            match_stats[winner_id_key]["score"] += max_score
            match_stats[loser_id_key]["score"] -= max_score
            
            # Count crash in global stats
            if winner_id == AGENT1_NAME: match_stats[AGENT2_NAME]["other_crash"] += 1
            else: match_stats[AGENT1_NAME]["other_crash"] += 1
            
            print("Final Position: N/A (crash)")
            print("-" * 40)
            print(f"Final Result: {{winner_id}} wins. (opponent crashed)")
            print("-" * 40)
            print("Points:")
            if winner_id == AGENT1_NAME:
                print("Agent-1: 3")
                print("Agent-2: 0")
            else:
                print("Agent-1: 0")
                print("Agent-2: 3")
            print("-" * 40)
            print("Scores:")
            if winner_id == AGENT1_NAME:
                print(f"Agent-1: {{max_score}}")
                print(f"Agent-2: -{{max_score}}")
            else:
                print(f"Agent-1: -{{max_score}}")
                print(f"Agent-2: {{max_score}}")

        elif result == "DRAW":
            match_stats[AGENT1_NAME]["draws"] += 1
            match_stats[AGENT1_NAME]["points"] += 1
            match_stats[AGENT2_NAME]["draws"] += 1
            match_stats[AGENT2_NAME]["points"] += 1
            
            print("-" * 40)
            print("Final Result: Draw by Turn Limit.")
            print("-" * 40)
            print("Points:")
            print("Agent-1: 1")
            print("Agent-2: 1")
            print("-" * 40)
            print("Scores:")
            print("Agent-1: 0")
            print("Agent-2: 0")

        else:
            winner_id = result # AGENT1_NAME or AGENT2_NAME
            loser_id = AGENT2_NAME if winner_id == AGENT1_NAME else AGENT1_NAME
            
            match_stats[winner_id]["wins"] += 1
            match_stats[winner_id]["points"] += 3
            match_stats[winner_id]["score"] += game_score
            match_stats[loser_id]["losses"] += 1
            match_stats[loser_id]["score"] -= game_score
            
            print("-" * 40)
            print(f"Final Result: {{winner_id}} wins by Elimination.")
            print("-" * 40)
            print("Points:")
            if winner_id == AGENT1_NAME:
                print("Agent-1: 3")
                print("Agent-2: 0")
            else:
                print("Agent-1: 0")
                print("Agent-2: 3")
            print("-" * 40)
            print("Scores:")
            if winner_id == AGENT1_NAME:
                print(f"Agent-1: {{game_score}}")
                print(f"Agent-2: -{{game_score}}")
            else:
                print(f"Agent-1: -{{game_score}}")
                print(f"Agent-2: {{game_score}}")
        
        print("=" * 60)
        sys.stdout.flush()
    
    print("=" * 60)
    print(f"Agent-1: {{AGENT1_NAME}}")
    print(f"Agent-2: {{AGENT2_NAME}}")
    print(f"RESULT:Agent-1={{float(match_stats[AGENT1_NAME]['points'])}},Agent-2={{float(match_stats[AGENT2_NAME]['points'])}}")
    print(f"SCORE:Agent-1={{float(match_stats[AGENT1_NAME]['score'])}},Agent-2={{float(match_stats[AGENT2_NAME]['score'])}}")
    print(f"WINS:Agent-1={{match_stats[AGENT1_NAME]['wins']}},Agent-2={{match_stats[AGENT2_NAME]['wins']}}")
    print(f"DRAWS:{{match_stats[AGENT1_NAME]['draws']}}")
    # Aggregate crash stat for backward compatibility
    for agent_key in [AGENT1_NAME, AGENT2_NAME]:
        match_stats[agent_key]['crash'] = match_stats[agent_key]['make_move_crash'] + match_stats[agent_key]['other_crash']

    print(f"STATS:Agent-1={{match_stats[AGENT1_NAME]}}")
    print(f"STATS:Agent-2={{match_stats[AGENT2_NAME]}}")

    print("--- MATCH STATISTICS ---")
    print(f"Agent-1 make_move_crash: {{match_stats[AGENT1_NAME]['make_move_crash']}}")
    print(f"Agent-2 make_move_crash: {{match_stats[AGENT2_NAME]['make_move_crash']}}")
    print(f"Agent-1 other_crash: {{match_stats[AGENT1_NAME]['other_crash']}}")
    print(f"Agent-2 other_crash: {{match_stats[AGENT2_NAME]['other_crash']}}")
    print(f"Agent-1 crash (total): {{match_stats[AGENT1_NAME]['crash']}}")
    print(f"Agent-2 crash (total): {{match_stats[AGENT2_NAME]['crash']}}")
    print(f"Agent-1 Timeouts: {{match_stats[AGENT1_NAME]['timeout']}}")
    print(f"Agent-2 Timeouts: {{match_stats[AGENT2_NAME]['timeout']}}")
    print(f"Agent-1 Invalid: {{match_stats[AGENT1_NAME]['invalid']}}")
    print(f"Agent-2 Invalid: {{match_stats[AGENT2_NAME]['invalid']}}")


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
    num_games: int = NUM_GAMES_PER_MATCH,
    board_size: int = BOARD_SIZE,
    ships: list[int] = SHIPS,
    move_timeout: float = MOVE_TIME_LIMIT,
    human_mode: bool = False,
    game_mode: str = "",
    agent1_name: str = "Agent-1",
    agent2_name: str = "Agent-2",
) -> str:
    """Build the complete game code with both agent implementations."""
    return GAME_CODE_TEMPLATE.format(
        num_games=num_games,
        board_size=board_size,
        ships=ships,
        move_timeout=move_timeout,
        extra_imports=extra_imports,
        agent1_code=agent1_code,
        agent2_code=agent2_code,
        human_mode=human_mode,
        game_mode=game_mode,
        agent1_name=agent1_name,
        agent2_name=agent2_name,
    )


def run_match(game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = MATCH_TIME_LIMIT) -> dict:
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
                "agent1_score": 0,
                "agent2_score": 0,
                "error": result.stderr[:500],
            }

        # Parse results
        match = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout)
        
        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            wins_match = re.search(r"WINS:Agent-1=(\d+),Agent-2=(\d+)", result.stdout)
            draws_match = re.search(r"DRAWS:(\d+)", result.stdout)
            score_match = re.search(r"SCORE:Agent-1=([-\d.]+),Agent-2=([-\d.]+)", result.stdout)
            
            agent1_wins = int(wins_match.group(1)) if wins_match else 0
            agent2_wins = int(wins_match.group(2)) if wins_match else 0
            draws = int(draws_match.group(1)) if draws_match else 0
            agent1_points = int(float(match.group(1))) if match else 0
            agent2_points = int(float(match.group(2))) if match else 0
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
            "error": "Could not parse results from output",
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
    """Run a match in human mode (interactive)."""
    temp_file = os.path.join(tempfile.gettempdir(), f"battleship_human_match.py")
    debug_file = "/tmp/debug_battleship.py"
    try:
        with open(temp_file, "w") as f:
            f.write(game_code)
        
        # Copy to debug file for inspection
        with open(debug_file, "w") as f:
            f.write(game_code)
            
        # Run interactively - result will be printed to stdout by the game script itself
        subprocess.call(["python", temp_file])
    finally:
        for file_path in [temp_file, debug_file]:
            if os.path.exists(file_path):
                os.remove(file_path)


async def run_match_async(game_code: str, match_id: int, run_ids: tuple[int, int]) -> dict:
    """Run a match in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    parser = argparse.ArgumentParser(description="Run Battleship matches between stored AI agents")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4]")
    
    human_group = parser.add_mutually_exclusive_group()
    human_group.add_argument("--humanvsbot", action="store_true", help="Play interactively against a random bot")
    human_group.add_argument("--humanvshuman", action="store_true", help="Two humans play at the same terminal")
    human_group.add_argument("--humanvsagent", action="store_true", help="Play against a stored agent (requires --agent with 1 spec)")
    parser.add_argument(
        "--update-scoreboard", action="store_true",
        help="Write results to scoreboard (default: off; enabled by matchmaker)",
    )

    args = parser.parse_args()

    game_mode = ""
    if args.humanvsbot:
        game_mode = "humanvsbot"
    elif args.humanvshuman:
        game_mode = "humanvshuman"
    elif args.humanvsagent:
        game_mode = "humanvsagent"

    if game_mode:
        print("\n" + "=" * 60)
        mode_title = MODE_TITLES.get(game_mode, game_mode)
        print(f"BATTLESHIP - {mode_title}")
        print("=" * 60)
        
        agent1_code = ""
        agent2_code = ""
        agent_imports = ""

        if game_mode == "humanvsagent":
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
             
             agent_code, agent_imports = load_stored_agent(folder, GAME_NAME, runs[0], 1)
             if not agent_code:
                 print(f"ERROR: Failed to load agent from {folder}")
                 sys.exit(1)
             
             # Pass as agent1_code (logic in template handles assignment)
             agent1_code = agent_code

        # We construct the game code with empty strings for agents if they are human/random
        # The template logic handles instantiation based on GAME_MODE
        game_code = build_game_code(
            agent1_code=agent1_code,
            agent2_code=agent2_code,
            extra_imports=agent_imports,
            num_games=1, 
            board_size=BOARD_SIZE, 
            ships=SHIPS, 
            move_timeout=99999, # Unlimited time for human
            human_mode=True, # Keeps compatibility
            game_mode=game_mode,
            agent1_name="Human" if game_mode != "humanvsbot" else "Human",
            agent2_name="Bot" if game_mode == "humanvsbot" else "Agent"
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
    print("BATTLESHIP MATCH - STORED AGENTS")
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
            print(f"  FAILED to load match {i+1}: Could not load agent code.")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        agent1_name = f"{folder1}:{run1}"
        agent2_name = f"{folder2}:{run2}"

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_GAMES_PER_MATCH, BOARD_SIZE, SHIPS, MOVE_TIME_LIMIT,
            agent1_name=agent1_name, agent2_name=agent2_name
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
            status += f"{folder1}:{run1} : Pts: {p1} - Score: {s1:.1f}\n"
            status += f"{folder2}:{run2} : Pts: {p2} - Score: {s2:.1f}\n"

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

        # Update scoreboard once per match
        if result["success"] and args.update_scoreboard:
            agent1_key = f"{folder1}:{run1}"
            update_scoreboard(
                SCOREBOARD_PATH, agent1_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=result["agent1_wins"],
                losses=result["agent2_wins"],
                draws=result.get("draws", 0),
                score=result["agent1_score"],
                points=result.get("agent1_points", 0),
            )
            agent2_key = f"{folder2}:{run2}"
            update_scoreboard(
                SCOREBOARD_PATH, agent2_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=result["agent2_wins"],
                losses=result["agent1_wins"],
                draws=result.get("draws", 0),
                score=result["agent2_score"],
                points=result.get("agent2_points", 0),
            )

    print("\nFINAL RESULTS:")
    print(f"  {folder1}: Pts {total_pts1}, Score {total1:.1f}")
    print(f"  {folder2}: Pts {total_pts2}, Score {total2:.1f}")
    print(f"\nLogs saved to: {RESULTS_DIR}")

if __name__ == "__main__":
    asyncio.run(main_async())
