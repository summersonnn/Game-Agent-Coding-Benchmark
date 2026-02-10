"""
WordFinder Match Runner: Orchestrates Head-to-Head matches for A4-WordFinder.

Game Rules: (2 Players)
1. Start with a random word from dictionary.
2. Players take turns finding a new word that:
    - Contains first and last letter of previous word.
    - Does NOT have those letters at start or end.
    - Has not been used yet.
    - Is in dictionary.
3. Scoring: Points = (length of word) / (seconds taken for move).
4. Penalty: Invalid move -> GAME OVER.
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

# Load environment variables
load_dotenv()

# Configuration
try:
    NUM_GAMES_PER_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "10"))
except (ValueError, TypeError):
    NUM_GAMES_PER_MATCH = 10

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0")) * 5
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

# Results directories
RESULTS_DIR = Path(__file__).parent.parent / "results" / "word_finder"
GAME_LOGS_DIR = RESULTS_DIR / "game_logs"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A4-WordFinder"

# Dictionary Path
WORDS_FILE = Path(__file__).parent.parent / "games" / "words.txt"

# Shared word subset for agents (set per game)
_SHARED_WORD_SUBSET = None

# The game code template
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal
import time

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
TIME_SENSITIVITY = 100000  # Scales microsecond response times to meaningful score differences
HUMAN_MODE = {human_mode}

{extra_imports}

{agent1_code}

{agent2_code}

class RandomAgent:
    def __init__(self, name):
        self.name = name
        self.words = None

    def make_move(self, current_word, history):
        if self.words is None:
            self.words = list(load_words())
        
        p_start = current_word[0].lower()
        p_end = current_word[-1].lower()
        
        candidates = []
        # Try to find valid words
        for w in self.words:
             if w in history: continue
             if len(w) == len(current_word): continue
             
             # Check constraints loosely
             if p_start in w and p_end in w:
                 if w[0] == p_start or w[0] == p_end: continue
                 if w[-1] == p_start or w[-1] == p_end: continue
                 candidates.append(w)
        
        if candidates:
            return random.choice(candidates)
        # Fallback to random word (likely invalid)
        return random.choice(self.words)

class HumanAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, current_word, history):
        print(f"\\nCurrent Word: {{current_word}}")
        print(f"Required: Must contain '{{current_word[0]}}' and '{{current_word[-1]}}'")
        print(f"Forbidden: Cannot start/end with '{{current_word[0]}}' or '{{current_word[-1]}}'")
        print("WARNING: Invalid move ends game instantly!")
        while True:
            try:
                w = input(f"Enter word: ").strip().lower()
                if w: return w
            except EOFError: return "quit"


class WordFinderGame:
    """Manages the WordFinder game state and validation."""
    
    def __init__(self, words_set):
        self.words_set = words_set
        self.history = set()
        self.current_word = ""
        self.scores = {{ "Agent-1": 0.0, "Agent-2": 0.0 }}
        self.game_over = False
        self.winner = None
        self.loser = None # For penalty application
        
    def start_game(self):
        """Pick a random starting word."""
        # Pick a word that has at least 3 letters to be safe/interesting
        valid_starts = [w for w in self.words_set if len(w) >= 3]
        if not valid_starts:
            # Fallback if dictionary is weird
            self.current_word = "start"
        else:
            self.current_word = random.choice(valid_starts)
            
        self.history = {{self.current_word}}
        return self.current_word

    def is_valid_move(self, new_word, input_word):
        """
        Check rule compliance. Returns (status, reason) where status is:
        - "valid": Perfect move with both required letters
        - "partial": Contains only ONE required letter (not at start/end) - game continues with penalty
        - "invalid": Doesn't meet basic requirements - game ends

        Rules for valid:
        1. new_word must be in dictionary
        2. new_word must contain input_word[0] and input_word[-1]
        3. new_word[0] != input_word[0] and new_word[0] != input_word[-1]
        4. new_word[-1] != input_word[0] and new_word[-1] != input_word[-1]
        5. new_word not in history
        6. len(new_word) != len(input_word)

        Rules for partial (fallback when no valid word exists):
        - Must pass rules 1, 5, 6
        - Must contain at least ONE of input_word[0] or input_word[-1]
        - That letter must NOT be at start or end of new_word
        """
        nw = new_word.lower()

        # 0. Basic sanity
        if not nw:
            return "invalid", "Empty word"

        # 1. Dictionary check
        if nw not in self.words_set:
            return "invalid", f"Word '{{nw}}' not in dictionary"

        # 2. History check
        if nw in self.history:
            return "invalid", f"Word '{{nw}}' already used"

        # 3. Letter constraints
        p_start = input_word[0].lower()
        p_end = input_word[-1].lower()
        n_start = nw[0]
        n_end = nw[-1]

        has_p_start = p_start in nw
        has_p_end = p_end in nw

        # Check if required letters are at forbidden positions (start/end of new word)
        p_start_at_boundary = (n_start == p_start or n_end == p_start)
        p_end_at_boundary = (n_start == p_end or n_end == p_end)

        # 4. Length constraint - cannot match previous word length
        if len(nw) == len(input_word):
            return "invalid", f"Word length {{len(nw)}} cannot equal previous word length {{len(input_word)}}"

        # Check for VALID move (both letters present, neither at boundary)
        if has_p_start and has_p_end and not p_start_at_boundary and not p_end_at_boundary:
            return "valid", "Valid"

        # Check for PARTIAL move (only one letter, not at boundary)
        # This is the fallback when agent believes no valid word exists
        has_valid_p_start = has_p_start and not p_start_at_boundary
        has_valid_p_end = has_p_end and not p_end_at_boundary

        if has_valid_p_start and not has_p_end:
            return "partial", f"Partial move: contains '{{p_start}}' but missing '{{p_end}}'"
        if has_valid_p_end and not has_p_start:
            return "partial", f"Partial move: contains '{{p_end}}' but missing '{{p_start}}'"

        # If we have one letter but it's at boundary, or neither letter properly placed
        if has_p_start and p_start_at_boundary:
            return "invalid", f"Letter '{{p_start}}' cannot be at start or end of word"
        if has_p_end and p_end_at_boundary:
            return "invalid", f"Letter '{{p_end}}' cannot be at start or end of word"

        # Neither letter present at all
        return "invalid", f"Must contain at least one of '{{p_start}}' or '{{p_end}}' (not at start/end)"

    def apply_move(self, agent_name, new_word, input_word, elapsed_time, is_partial=False):
        """Apply the move and calculate points with potential bonus, hyphen penalty, and time division.

        For partial moves (is_partial=True), the agent receives NEGATIVE points.
        """
        base_points = len(new_word)

        # Check for hyphen penalty (words with "-" get half points)
        has_hyphen = '-' in new_word
        if has_hyphen:
            base_points = base_points // 2  # Integer division for half points

        # Check for consecutive letter bonus (only applies to valid moves, not partial)
        p_start = input_word[0].lower()
        p_end = input_word[-1].lower()
        nw = new_word.lower()

        # Check if required letters appear consecutively (in either order)
        consecutive = (p_start + p_end in nw) or (p_end + p_start in nw)

        if consecutive and not is_partial:
            points = base_points * 2  # 2x multiplier!
        else:
            points = base_points

        # Divide points by (1 + scaled_time) - TIME_SENSITIVITY scales microseconds to meaningful values
        time_adjusted_points = points / (1 + elapsed_time * TIME_SENSITIVITY)

        # For partial moves, negate the points (penalty)
        if is_partial:
            time_adjusted_points = -time_adjusted_points

        self.scores[agent_name] += time_adjusted_points
        self.history.add(new_word.lower())
        self.current_word = new_word

        return time_adjusted_points, consecutive, has_hyphen, elapsed_time, is_partial
        
    def penalize_and_end(self, agent_name):
        """End the game without halving points (penalty is losing the opportunity to score more)."""
        self.game_over = True
        self.loser = agent_name
        # Winner is the other one (implicitly determined by scores later, 
        # but strictly speaking game ends. The prompts check final scores.)
        

# --- Stats ---
stats = {{
    "normal_end": 0,
    "p1_penalty": 0,      # Illegal moves (game-ending)
    "p2_penalty": 0,
    "p1_partial": 0,      # Partial moves (game continues with negative points)
    "p2_partial": 0,
    "p1_timeout": 0,
    "p2_timeout": 0,
    "p1_crash": 0,
    "p2_crash": 0,
    "turns": 0
}}

def is_valid_word(word):
    """Check if word contains only alphabetical characters and hyphens."""
    for char in word:
        if not (char.isalpha() or char == '-'):
            return False
    return True

def load_words(subset=None):
    """Load dictionary. If subset provided, return it. Otherwise use shared subset or load from file."""
    # First check if there's a shared subset available (set by play_game)
    if '_SHARED_WORD_SUBSET' in globals() and _SHARED_WORD_SUBSET is not None:
        return _SHARED_WORD_SUBSET
    
    if subset is not None:
        return subset
    
    # This path is for standalone testing - normally subset is provided
    try:
        with open(WORDS_FILE_PATH, 'r') as f:
            # Load all valid words (only alphabetical + hyphens)
            all_words = {{line.strip().lower() for line in f if line.strip() and is_valid_word(line.strip())}}
        
        if len(all_words) > 100000:
            return set(random.sample(list(all_words), 100000))
        else:
            return all_words
    except Exception as e:
        print(f"ERROR: Could not load words from {{WORDS_FILE_PATH}}: {{e}}")
        sys.exit(1)

def load_full_dictionary():
    """Load the complete dictionary for validation purposes (only valid words)."""
    try:
        with open(WORDS_FILE_PATH, 'r') as f:
            # Only include words with alphabetical characters and hyphens
            return {{line.strip().lower() for line in f if line.strip() and is_valid_word(line.strip())}}
    except Exception as e:
        print(f"ERROR: Could not load words from {{WORDS_FILE_PATH}}: {{e}}")
        sys.exit(1)

def play_game(game_num, total_scores):
    # Load full dictionary for validation (already filtered for valid characters)
    full_dictionary = load_full_dictionary()
    game = WordFinderGame(full_dictionary)
    
    # Create a shared random subset of 10k words for both agents
    # Filter to ensure we only use valid words
    valid_words = [w for w in full_dictionary if is_valid_word(w)]
    
    if len(valid_words) >= 100000:
        shared_word_subset = set(random.sample(valid_words, 100000))
    else:
        shared_word_subset = set(valid_words)
    
    # Make the subset available globally for agents to access via load_words()
    global _SHARED_WORD_SUBSET
    _SHARED_WORD_SUBSET = shared_word_subset
    
    # Initialize agents
    if HUMAN_MODE:
        agent1 = HumanAgent("Agent-1")
        agent2 = RandomAgent("Agent-2")
    else:
        try:
            agent1 = WordFinderAgent_1("Agent-1")
        except Exception as e:
            return ("Agent-2", "Crash init A1")
            
        try:
            agent2 = WordFinderAgent_2("Agent-2")
        except Exception as e:
            return ("Agent-1", "Crash init A2")
            
    current_agent_obj, other_agent_obj = (agent1, agent2) if random.random() < 0.5 else (agent2, agent1)
    
    # Print game header with agent info
    print()
    print("=" * 60)
    print(f"GAME {{game_num}}")
    print(f"Agent-1: {{AGENT1_INFO}}")
    print(f"Agent-2: {{AGENT2_INFO}}")
    print("=" * 60)
    
    # Start
    start_word = game.start_game()
    print(f"Starting random word: {{start_word}}")
    
    end_reason = "Game completed normally"
    end_reason_type = "normal"  # Types: normal, illegal_move, timeout, crash

    while not game.game_over:
        stats["turns"] += 1
        
        # Get Move with timeout and time tracking
        new_word = None
        move_start_time = time.time()

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))

            try:
                # Pass the current word and the history of all used words
                new_word = current_agent_obj.make_move(game.current_word, game.history)
                move_elapsed_time = time.time() - move_start_time
            finally:
                signal.alarm(0)
                
        except MoveTimeoutException:
            # Timeout -> End game with 25% point reduction
            move_elapsed_time = time.time() - move_start_time
            game.penalize_and_end(current_agent_obj.name)
            end_reason = f"{{current_agent_obj.name}} exceeded time limit"
            end_reason_type = "timeout"
            print(f"{{current_agent_obj.name}}: TIMEOUT")
            if current_agent_obj.name == "Agent-1": stats["p1_timeout"] += 1
            else: stats["p2_timeout"] += 1
            break

        except Exception as e:
            # Crash -> End game (treated as illegal move - automatic loss)
            move_elapsed_time = time.time() - move_start_time
            game.penalize_and_end(current_agent_obj.name)
            end_reason = f"{{current_agent_obj.name}} crashed: {{str(e)[:50]}}"
            end_reason_type = "crash"
            print(f"{{current_agent_obj.name}}: CRASH ({{e}})")
            if current_agent_obj.name == "Agent-1": stats["p1_crash"] += 1
            else: stats["p2_crash"] += 1
            break
            
        # Validate
        if not isinstance(new_word, str):
            game.penalize_and_end(current_agent_obj.name)
            end_reason = f"{{current_agent_obj.name}} returned invalid output type"
            end_reason_type = "illegal_move"
            detail = f"returned {{type(new_word).__name__}}: {{new_word}}" if new_word is not None else "returned None"
            print(f"{{current_agent_obj.name}}: INVALID_OUTPUT ({{detail}})")
            if current_agent_obj.name == "Agent-1": stats["p1_crash"] += 1
            else: stats["p2_crash"] += 1
            break

        new_word = new_word.strip()
        move_status, reason = game.is_valid_move(new_word, game.current_word)

        if move_status == "valid":
            # Perfect move - both required letters present
            points_awarded, got_bonus, has_hyphen, time_taken, _ = game.apply_move(
                current_agent_obj.name, new_word, game.current_word, move_elapsed_time, is_partial=False
            )
            bonus_str = "2x" if got_bonus else "None"
            penalty_str = "-50% (hyphen)" if has_hyphen else "None"
            print(f"{{current_agent_obj.name}}: {{new_word}} --> Word length: {{len(new_word)}}, Bonus: {{bonus_str}}, Penalty: {{penalty_str}}, Time: {{time_taken:.6f}} sec, Points: +{{points_awarded:.2f}}")
            # Swap turn
            current_agent_obj, other_agent_obj = other_agent_obj, current_agent_obj

        elif move_status == "partial":
            # Partial move - only one required letter present (fallback when no valid word exists)
            # Game continues but agent gets NEGATIVE points
            points_awarded, _, has_hyphen, time_taken, _ = game.apply_move(
                current_agent_obj.name, new_word, game.current_word, move_elapsed_time, is_partial=True
            )
            penalty_str = "-50% (hyphen)" if has_hyphen else "None"
            print(f"{{current_agent_obj.name}}: {{new_word}} --> PARTIAL MOVE ({{reason}}), Word length: {{len(new_word)}}, Hyphen: {{penalty_str}}, Time: {{time_taken:.6f}} sec, Points: {{points_awarded:.2f}} (PENALTY)")
            if current_agent_obj.name == "Agent-1": stats["p1_partial"] += 1
            else: stats["p2_partial"] += 1
            # Swap turn - game continues
            current_agent_obj, other_agent_obj = other_agent_obj, current_agent_obj

        else:
            # Invalid -> End game (illegal move = automatic loss)
            game.penalize_and_end(current_agent_obj.name)
            end_reason = f"{{current_agent_obj.name}} played invalid word: {{reason}}"
            end_reason_type = "illegal_move"
            print(f"{{current_agent_obj.name}}: {{new_word}} (ILLEGAL MOVE: {{reason}})")
            if current_agent_obj.name == "Agent-1": stats["p1_penalty"] += 1
            else: stats["p2_penalty"] += 1
            break
            
    # Game Over
    # Print game summary header
    print()
    print(f"GAME {{game_num}} ENDED")
    print(f"Reason: {{end_reason}}")
    print(f"Scores Before Penalties - Agent-1: {{game.scores['Agent-1']:.2f}} | Agent-2: {{game.scores['Agent-2']:.2f}}")

    # Apply penalty rules based on end reason type
    loser = game.loser
    if loser:
        other_agent = "Agent-2" if loser == "Agent-1" else "Agent-1"

        if end_reason_type in ("illegal_move", "crash", "timeout"):
            # Illegal move, crash, or timeout = automatic loss regardless of points
            # If the offender has more points, swap scores so they lose
            reason_desc = "timed out" if end_reason_type == "timeout" else "made an illegal move/crash"
            print(f"PENALTY: {{loser}} {{reason_desc}} - automatic loss!")
            if game.scores[loser] >= game.scores[other_agent]:
                # Swap scores so loser has fewer points
                old_loser_score = game.scores[loser]
                old_winner_score = game.scores[other_agent]
                # Set loser's score to be less than winner's (swap them)
                game.scores[loser] = old_winner_score - 0.01 if old_winner_score > 0 else 0.0
                game.scores[other_agent] = old_loser_score
                print(f"SCORE SWAP: {{loser}} score adjusted from {{old_loser_score:.2f}} to {{game.scores[loser]:.2f}}")
                print(f"SCORE SWAP: {{other_agent}} score adjusted from {{old_winner_score:.2f}} to {{game.scores[other_agent]:.2f}}")
            winner = other_agent
        else:
            # Normal end - determine winner by scores
            if game.scores["Agent-1"] > game.scores["Agent-2"]:
                winner = "Agent-1"
            elif game.scores["Agent-2"] > game.scores["Agent-1"]:
                winner = "Agent-2"
            else:
                winner = "DRAW"
    else:
        # No loser recorded - determine winner by scores
        if game.scores["Agent-1"] > game.scores["Agent-2"]:
            winner = "Agent-1"
        elif game.scores["Agent-2"] > game.scores["Agent-1"]:
            winner = "Agent-2"
        else:
            winner = "DRAW"

    # Print final scores after penalties
    print(f"Final Scores After Penalties - Agent-1: {{game.scores['Agent-1']:.2f}} | Agent-2: {{game.scores['Agent-2']:.2f}}")

    # Update total scores with penalty-adjusted values
    total_scores["Agent-1"] += game.scores["Agent-1"]
    total_scores["Agent-2"] += game.scores["Agent-2"]

    # Print winner
    if winner == "DRAW":
        print(f"Result: DRAW")
    else:
        print(f"Winner: {{winner}}")

    print(f"Running Total - Agent-1: {{total_scores['Agent-1']:.2f}} | Agent-2: {{total_scores['Agent-2']:.2f}}")
    print("=" * 60)
    print()
    sys.stdout.flush()

    return winner

def main():
    total_scores = {{"Agent-1": 0.0, "Agent-2": 0.0}}

    for i in range(NUM_GAMES):
        play_game(i+1, total_scores)
        sys.stdout.flush()

    print(f"RESULT:Agent-1={{total_scores['Agent-1']:.2f}},Agent-2={{total_scores['Agent-2']:.2f}}")
    print("--- MATCH STATISTICS ---")
    print(f"Agent-1 Illegal Moves (game-ending): {{stats['p1_penalty']}}")
    print(f"Agent-2 Illegal Moves (game-ending): {{stats['p2_penalty']}}")
    print(f"Agent-1 Partial Moves (negative points): {{stats['p1_partial']}}")
    print(f"Agent-2 Partial Moves (negative points): {{stats['p2_partial']}}")
    print(f"Agent-1 Timeouts: {{stats['p1_timeout']}}")
    print(f"Agent-2 Timeouts: {{stats['p2_timeout']}}")
    print(f"Agent-1 Crashes/Invalid Outputs: {{stats['p1_crash']}}")
    print(f"Agent-2 Crashes/Invalid Outputs: {{stats['p2_crash']}}")
    print(f"Total Turns Played: {{stats['turns']}}")

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
        
        # Find where WordFinderAgent class starts
        if stripped.startswith("class WordFinderAgent"):
            class_start_idx = i
            break
            
        # Collect imports before the class
        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped and "time" not in stripped:
                imports.append(stripped)
    
    if class_start_idx is None:
        logger.error("No WordFinderAgent class found in %s", agent_file)
        return "", ""
    
    # Extract ONLY the WordFinderAgent class
    class_lines = []
    in_class = False
    base_indent = 0
    
    for i in range(class_start_idx, len(code_lines)):
        line = code_lines[i]
        stripped = line.strip()
        
        if i == class_start_idx:
            class_lines.append(line)
            in_class = True
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
    
    # Rename WordFinderAgent to WordFinderAgent_{agent_idx}
    agent_code = re.sub(r"\bWordFinderAgent\b", f"WordFinderAgent_{agent_idx}", agent_code)
    
    return agent_code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
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
    human_mode: bool = False,
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
        human_mode=human_mode,
    )


def run_match(game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = 600) -> dict:
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"wordfinder_match_{match_id}_{temp_id}.py"
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
                "agent1_score": 0.0,
                "agent2_score": 0.0,
                "error": result.stderr[:500],
            }

        # Parse results (scores are now floats)
        match = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout)
        
        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            # Extract moves history AND game boundaries
            log_lines = []
            for line in result.stdout.splitlines():
                if line.startswith(("Starting random word:", "Agent-1:", "Agent-2:",
                                   "GAME ", "Reason:", "Final Scores", "Winner:", "Result:",
                                   "Running Total", "==========")) or line.strip() == "":
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
            "agent1_score": 0.0,
            "agent2_score": 0.0,
            "error": "Could not parse results from output:\n" + result.stdout[:200],
        }

    except Exception as e:
        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": False,
            "agent1_score": 0.0,
            "agent2_score": 0.0,
            "error": str(e),
        }
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def run_match_human(game_code: str) -> None:
    temp_file = os.path.join(tempfile.gettempdir(), f"wordfinder_human_{{uuid.uuid4().hex[:8]}}.py")
    try:
        with open(temp_file, "w") as f: f.write(game_code)
        subprocess.call(["python", temp_file])
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)


async def run_match_async(game_code: str, match_id: int, run_ids: tuple[int, int]) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    parser = argparse.ArgumentParser(description="Run WordFinder matches")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4]")
    parser.add_argument("--human", action="store_true", help="Play interactively against a random bot")
    args = parser.parse_args()

    if args.human:
        print("\n" + "=" * 60)
        print("WORDFINDER HUMAN MODE")
        print("You are playing against a RandomBot.")
        print("=" * 60)
        
        game_code = build_game_code(
            "", "", "", 
            num_games=1, 
            words_file_path=WORDS_FILE,
            move_timeout=99999,
            agent1_info="Human",
            agent2_info="RandomBot",
            human_mode=True
        )
        run_match_human(game_code)
        return

    if not args.agent or len(args.agent) != 2:
        print("ERROR: Need exactly 2 agent specifications.")
        sys.exit(1)

    # Parse and load agents
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
    print("WORDFINDER MATCH - STORED AGENTS")
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
            print(f"  FAILED to load match {i+1}")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        # Create agent info strings for logging
        agent1_info = f"{folder1} (Run {run1})"
        agent2_info = f"{folder2} (Run {run2})"

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_GAMES_PER_MATCH, str(WORDS_FILE), MOVE_TIME_LIMIT,
            agent1_info, agent2_info
        )
        
        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)
    
    total1, total2 = 0.0, 0.0

    with open(log_f, "w") as f:
        f.write(f"WordFinder Match - {ts}\n")
        f.write("=" * 60 + "\n\n")
        
        for result in sorted(results, key=lambda x: x["match_id"]):
            match_id = result["match_id"]
            if result["success"]:
                s1, s2 = result["agent1_score"], result["agent2_score"]
                total1 += s1
                total2 += s2
                status = f"Result: {s1:.2f} - {s2:.2f}"
                game_log = result.get("log", "")
                if game_log:
                    status += f"\n{game_log}\n"
                if result.get("stats_block"):
                    status += f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n"
            else:
                status = f"FAILED: {result.get('error', 'Unknown')}"
                
            print(f"  Match {match_id}: {status}")
            f.write(f"Match {match_id}: {status}\n")
            if result.get("stats_block"):
                f.write(f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n")
                f.write("-" * 60 + "\n\n")

    print("\nFINAL RESULTS (Total Score):")
    print(f"  {folder1}: {total1:.2f}")
    print(f"  {folder2}: {total2:.2f}")
    print(f"\nLogs saved to: {log_f}")

if __name__ == "__main__":
    asyncio.run(main_async())
