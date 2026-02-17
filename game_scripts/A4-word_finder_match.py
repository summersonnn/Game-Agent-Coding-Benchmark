"""
WordFinder Match Runner: Orchestrates head-to-head matches for A4-WordFinder.

Loads pre-generated WordFinderAgent code from agents/, injects it into a
self-contained game script, runs matches via subprocess, and reports
standardized results with scoreboard integration.
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
    # A4 takes too long to finish. So, arrange less matches
    NUM_GAMES_PER_MATCH = int(int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100")) / 10)
except (ValueError, TypeError):
    NUM_GAMES_PER_MATCH = 10

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / "word_finder"
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / "A4-scoreboard.txt"
AGENTS_DIR = BASE_DIR / "agents"

GAME_NAME = "A4-WordFinder"

# Dictionary Path
WORDS_FILE = Path(__file__).parent / "words.txt"

MODE_TITLES = {
    "humanvsbot": "Human vs Random Bot",
    "humanvshuman": "Human vs Human",
    "humanvsagent": "Human vs Stored Agent",
}

# Max possible tie-breaker score (used for init-crash forfeits; unbounded game)
FORFEIT_SCORE = 12

# Max rounds per game (each round = 1 turn per player = 2 individual turns)
MAX_ROUNDS = 100


# ============================================================
# Game engine code (WordFinderGame, dictionary, agents, display)
# ============================================================
GAME_ENGINE_CODE = r'''
# Penalty applied for invalid/crash/timeout moves (game continues)
INVALID_PENALTY = -10

# Max possible tie-breaker score for init-crash forfeits
FORFEIT_SCORE = 12

# Max rounds per game (50 rounds = 100 individual turns)
MAX_ROUNDS = 50


def is_valid_word(word):
    """Check if word contains only alphabetical characters and hyphens."""
    for char in word:
        if not (char.isalpha() or char == '-'):
            return False
    return True


def load_words():
    """Load dictionary from WORDS_FILE_PATH and sample 10k random words."""
    try:
        with open(WORDS_FILE_PATH, 'r') as f:
            all_words = [line.strip().lower() for line in f
                        if line.strip() and is_valid_word(line.strip())]
            
            if len(all_words) > 10000:
                # Use a fixed seed so all agents (and the game) see the same 10k words
                rng = random.Random(42)
                return set(rng.sample(all_words, 10000))
            return set(all_words)
    except Exception as e:
        print(f"ERROR: Could not load words from {WORDS_FILE_PATH}: {e}")
        sys.exit(1)


class WordFinderGame:
    """Manages the WordFinder game state and validation."""

    def __init__(self, words_set):
        self.words_set = words_set
        self.history = set()
        self.current_word = ""
        self.scores = {"Agent-1": 0.0, "Agent-2": 0.0}
        self.game_over = False
        self.turn_count = 0

    def start_game(self):
        """Pick a random starting word (at least 3 letters)."""
        valid_starts = [w for w in self.words_set if len(w) >= 3]
        if not valid_starts:
            self.current_word = "start"
        else:
            self.current_word = random.choice(valid_starts)
        self.history = {self.current_word}
        return self.current_word

    def is_valid_move(self, new_word, input_word):
        """
        Check rule compliance. Returns (status, reason) where status is:
        - "valid": Perfect move with both required letters
        - "partial": Contains only ONE required letter (not at start/end)
        - "invalid": Doesn't meet basic requirements
        """
        nw = new_word.lower()

        if not nw:
            return "invalid", "Empty word"

        if nw not in self.words_set:
            return "invalid", f"Word '{nw}' not in dictionary"

        if nw in self.history:
            return "invalid", f"Word '{nw}' already used"

        p_start = input_word[0].lower()
        p_end = input_word[-1].lower()
        n_start = nw[0]
        n_end = nw[-1]

        has_p_start = p_start in nw
        has_p_end = p_end in nw

        p_start_at_boundary = (n_start == p_start or n_end == p_start)
        p_end_at_boundary = (n_start == p_end or n_end == p_end)

        if len(nw) == len(input_word):
            return "invalid", f"Word length {len(nw)} cannot equal previous word length {len(input_word)}"

        # Valid move: both letters present, neither at boundary
        if has_p_start and has_p_end and not p_start_at_boundary and not p_end_at_boundary:
            return "valid", "Valid"

        # Partial move: only one letter, not at boundary
        has_valid_p_start = has_p_start and not p_start_at_boundary
        has_valid_p_end = has_p_end and not p_end_at_boundary

        if has_valid_p_start and not has_p_end:
            return "partial", f"Partial move: contains '{p_start}' but missing '{p_end}'"
        if has_valid_p_end and not has_p_start:
            return "partial", f"Partial move: contains '{p_end}' but missing '{p_start}'"

        if has_p_start and p_start_at_boundary:
            return "invalid", f"Letter '{p_start}' cannot be at start or end of word"
        if has_p_end and p_end_at_boundary:
            return "invalid", f"Letter '{p_end}' cannot be at start or end of word"

        return "invalid", f"Must contain at least one of '{p_start}' or '{p_end}' (not at start/end)"

    def apply_move(self, agent_name, new_word, input_word, is_partial=False):
        """Apply the move and calculate points with bonus/penalty mechanics.

        Scoring:
        - Base points = word length
        - Hyphen penalty: words with '-' get half points
        - Consecutive bonus: 2x if required letters appear consecutively (valid only)
        - Partial moves: negative base points (penalty)
        """
        base_points = len(new_word)

        has_hyphen = '-' in new_word
        if has_hyphen:
            base_points = base_points // 2

        p_start = input_word[0].lower()
        p_end = input_word[-1].lower()
        nw = new_word.lower()

        consecutive = (p_start + p_end in nw) or (p_end + p_start in nw)

        if consecutive and not is_partial:
            points = base_points * 2
        else:
            points = base_points

        if is_partial:
            points = -points

        self.scores[agent_name] += points
        self.history.add(new_word.lower())
        self.current_word = new_word

        return points, consecutive, has_hyphen


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
        for w in self.words:
            if w in history:
                continue
            if len(w) == len(current_word):
                continue
            if p_start in w and p_end in w:
                if w[0] == p_start or w[0] == p_end:
                    continue
                if w[-1] == p_start or w[-1] == p_end:
                    continue
                candidates.append(w)

        if candidates:
            return random.choice(candidates)
        return random.choice(self.words)


class HumanAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, current_word, history):
        print(f"\nCurrent Word: {current_word}")
        print(f"Required: Must contain '{current_word[0]}' and '{current_word[-1]}'")
        print(f"Forbidden: Cannot start/end with '{current_word[0]}' or '{current_word[-1]}'")
        while True:
            try:
                w = input("Enter word: ").strip().lower()
                if w:
                    return w
            except EOFError:
                return "quit"


def print_word_chain_log(history, current_word):
    """Print game state with BOARD: prefix for log filtering."""
    print(f"BOARD: Words played: {len(history)}")
    print(f"BOARD: Current word: {current_word}")
'''


# ============================================================
# Match runner code (play_game, main, stats, output)
# ============================================================
MATCH_RUNNER_CODE = r'''
class MoveTimeoutException(BaseException):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")


def play_game(game_num, match_stats, Agent1Class, Agent2Class, dictionary):
    """Play a single game and update match_stats. Returns winner name or 'DRAW'."""
    game = WordFinderGame(dictionary)

    # Instinctiate agents for this game (Init crash = Game Forfeit)
    try:
        agent1 = Agent1Class("Agent-1")
    except Exception as e:
        print(f"Agent-1 init crash: {e}")
        match_stats["Agent-1"]["other_crash"] += 1
        
        # Forfeit penalties
        match_stats["Agent-2"]["wins"] += 1
        match_stats["Agent-2"]["points"] += 3
        match_stats["Agent-2"]["score"] += FORFEIT_SCORE
        match_stats["Agent-1"]["losses"] += 1
        match_stats["Agent-1"]["score"] -= FORFEIT_SCORE
        
        print(f"Game {game_num}: Agent-1 crashed during initialization. Agent-2 wins.")
        return "Agent-2"

    try:
        agent2 = Agent2Class("Agent-2")
    except Exception as e:
        print(f"Agent-2 init crash: {e}")
        match_stats["Agent-2"]["other_crash"] += 1
        
        # Forfeit penalties
        match_stats["Agent-1"]["wins"] += 1
        match_stats["Agent-1"]["points"] += 3
        match_stats["Agent-1"]["score"] += FORFEIT_SCORE
        match_stats["Agent-2"]["losses"] += 1
        match_stats["Agent-2"]["score"] -= FORFEIT_SCORE
        
        print(f"Game {game_num}: Agent-2 crashed during initialization. Agent-1 wins.")
        return "Agent-1"

    agents = {"Agent-1": agent1, "Agent-2": agent2}

    # Randomize who goes first
    if random.random() < 0.5:
        turn_order = ["Agent-1", "Agent-2"]
    else:
        turn_order = ["Agent-2", "Agent-1"]

    print()
    print("=" * 60)
    print(f"Game {game_num}")
    print(f"Agent-1: {AGENT1_NAME}")
    print(f"Agent-2: {AGENT2_NAME}")
    print("-" * 60)

    # Start game
    start_word = game.start_game()
    print(f"Starting word: {start_word}")

    # --- Game loop (max MAX_ROUNDS rounds = 2*MAX_ROUNDS individual turns) ---
    turn_idx = 0
    while game.turn_count < MAX_ROUNDS * 2:
        current_name = turn_order[turn_idx % 2]
        current_agent = agents[current_name]
        game.turn_count += 1
        turn_idx += 1

        new_word = None
        error_type = None

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                new_word = current_agent.make_move(game.current_word, game.history.copy())
            finally:
                signal.alarm(0)
        except MoveTimeoutException:
            match_stats[current_name]["timeout"] += 1
            error_type = "timeout"
        except Exception as e:
            match_stats[current_name]["make_move_crash"] += 1
            error_type = "crash"
            print(f"{current_name} CRASH: {e}")

        # Validate logic
        move_status = None
        reason = ""
        
        if error_type is None:
            if not isinstance(new_word, str) or not new_word.strip():
                match_stats[current_name]["invalid"] += 1
                error_type = "invalid_format"
            else:
                new_word = new_word.strip()
                move_status, reason = game.is_valid_move(new_word, game.current_word)
                if move_status == "invalid":
                     match_stats[current_name]["invalid"] += 1
                     error_type = "invalid_move"

        # Handle valid/partial vs fallback
        if error_type is None and move_status in ["valid", "partial"]:
            # Acceptable move
            pass
        else:
            # Fallback required
            print(f"{current_name}: Error ({error_type or reason}). Triggering Random Fallback.")
            
            # Find valid fallback
            candidates = []
            p_start = game.current_word[0].lower()
            p_end = game.current_word[-1].lower()
            t_len = len(game.current_word)
            
            for w in game.words_set:
                if w in game.history: continue
                if len(w) == t_len: continue
                if p_start not in w or p_end not in w: continue
                if w.startswith(p_start) or w.endswith(p_start): continue
                if w.startswith(p_end) or w.endswith(p_end): continue
                candidates.append(w)
            
            if candidates:
                new_word = random.choice(candidates)
                move_status = "valid"
                print(f"{current_name}: FALLBACK -> {new_word}")
            else:
                print(f"{current_name}: FALLBACK failed (no valid words). Skipping turn.")
                move_status = "skip"

        # Apply move
        if move_status == "valid":
            points, got_bonus, has_hyphen = game.apply_move(
                current_name, new_word, game.current_word, is_partial=False
            )
            bonus_str = "2x" if got_bonus else "None"
            penalty_str = "-50% (hyphen)" if has_hyphen else "None"
            print(f"{current_name}: {new_word} -> Len: {len(new_word)}, Bonus: {bonus_str}, Penalty: {penalty_str}, Points: {points:+d}")

        elif move_status == "partial":
            points, _, has_hyphen = game.apply_move(
                current_name, new_word, game.current_word, is_partial=True
            )
            penalty_str = "-50% (hyphen)" if has_hyphen else "None"
            print(f"{current_name}: {new_word} -> PARTIAL ({reason}), Len: {len(new_word)}, Hyphen: {penalty_str}, Points: {points:+d}")
        
        else:
             print(f"{current_name}: Turn Skipped.")

    # --- Game over: determine winner by score ---
    print()
    print("Final Position:")
    print_word_chain_log(game.history, game.current_word)

    a1_score = game.scores["Agent-1"]
    a2_score = game.scores["Agent-2"]
    score_diff = abs(a1_score - a2_score)

    if a1_score > a2_score:
        winner = "Agent-1"
        loser = "Agent-2"
    elif a2_score > a1_score:
        winner = "Agent-2"
        loser = "Agent-1"
    else:
        winner = "DRAW"
        loser = None

    BIG_WIN_THRESHOLD = MAX_ROUNDS * 2  # decisive win: margin >= 2 * max_rounds
    DRAW_THRESHOLD = MAX_ROUNDS          # near-draw: margin < max_rounds

    print("-" * 40)
    if winner == "DRAW" or score_diff < DRAW_THRESHOLD:
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
    elif score_diff >= BIG_WIN_THRESHOLD:
        print(f"Final Result: {winner} wins (decisive).")
        print("-" * 40)
        print("Points:")
        print(f"{winner}: 3")
        print(f"{loser}: 0")
        print("-" * 40)
        print("Scores:")
        print(f"{winner}: {score_diff:.1f}")
        print(f"{loser}: -{score_diff:.1f}")
        print("=" * 60)

        match_stats[winner]["wins"] += 1
        match_stats[winner]["points"] += 3
        match_stats[winner]["score"] += score_diff
        match_stats[loser]["losses"] += 1
        match_stats[loser]["score"] -= score_diff
        return winner
    else:
        # Narrow win: DRAW_THRESHOLD <= score_diff < BIG_WIN_THRESHOLD
        print(f"Final Result: {winner} wins (narrow).")
        print("-" * 40)
        print("Points:")
        print(f"{winner}: 2")
        print(f"{loser}: 0.5")
        print("-" * 40)
        print("Scores:")
        print(f"{winner}: {score_diff:.1f}")
        print(f"{loser}: -{score_diff:.1f}")
        print("=" * 60)

        match_stats[winner]["wins"] += 1
        match_stats[winner]["points"] += 2
        match_stats[winner]["score"] += score_diff
        match_stats[loser]["losses"] += 1
        match_stats[loser]["points"] += 0.5
        match_stats[loser]["score"] -= score_diff
        return winner


def _print_final_stats(match_stats):
    """Print the final match statistics in the expected parseable format."""
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
    print()

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


def main():
    """Main function to run the WordFinder match."""
    dictionary = load_words()

    # Determine agent classes based on game mode
    if GAME_MODE == "humanvsbot":
        class_1, class_2 = HumanAgent, RandomAgent
    elif GAME_MODE == "humanvshuman":
        class_1, class_2 = HumanAgent, HumanAgent
    elif GAME_MODE == "humanvsagent":
        class_1, class_2 = HumanAgent, WordFinderAgent_1
    else:
        class_1, class_2 = WordFinderAgent_1, WordFinderAgent_2

    match_stats = {
        "Agent-1": {
            "wins": 0, "losses": 0, "draws": 0, "points": 0.0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0,
        },
        "Agent-2": {
            "wins": 0, "losses": 0, "draws": 0, "points": 0.0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0,
        },
    }

    for i in range(NUM_GAMES):
        play_game(i + 1, match_stats, class_1, class_2, dictionary)
        sys.stdout.flush()

    _print_final_stats(match_stats)


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

        if stripped.startswith("class WordFinderAgent"):
            class_start_idx = i
            break

        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:
                imports.append(stripped)

    if class_start_idx is None:
        logger.error("No WordFinderAgent class found in %s", agent_file)
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
        r"\bWordFinderAgent\b", f"WordFinderAgent_{agent_idx}", agent_code
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
    words_file_path: str,
    game_mode: str = "",
    agent1_name: str = "Agent-1",
    agent2_name: str = "Agent-2",
) -> str:
    """Build the complete game code by concatenating header, agents, engine, and runner."""
    header = (
        "import sys\n"
        "import random\n"
        "import signal\n"
        "\n"
        f"MOVE_TIMEOUT = {move_timeout}\n"
        f"NUM_GAMES = {num_games}\n"
        f'WORDS_FILE_PATH = r"{words_file_path}"\n'
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
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = 600
) -> dict:
    """Execute a match subprocess, parse results, and return structured dict."""
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
            agent1_points = float(match.group(1))
            agent2_points = float(match.group(2))
            agent1_score = float(score_match.group(1)) if score_match else 0.0
            agent2_score = float(score_match.group(2)) if score_match else 0.0

            # Log filtering: keep only meaningful lines
            log_lines = []
            for line in result.stdout.splitlines():
                stripped = line.lstrip()
                if stripped.startswith((
                    "Agent-1:", "Agent-2:", "Game ",
                    "=====", "----",
                    "Starting word:", "Final", "Scores:", "Points:",
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
        tempfile.gettempdir(), f"wordfinder_human_{uuid.uuid4().hex[:8]}.py"
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
        description="Run WordFinder matches between stored AI agents"
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
        print(f"WORDFINDER - {mode_title}")
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
            num_games=10,
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
    print("WORDFINDER MATCH - STORED AGENTS")
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
            print(f"  FAILED to load match {i + 1}: Could not load agent code.")
            continue

        all_imports = set(imp1.split("\n") + imp2.split("\n"))
        extra_imports = "\n".join(imp for imp in all_imports if imp.strip())

        game_code = build_game_code(
            code1, code2, extra_imports,
            NUM_GAMES_PER_MATCH, MOVE_TIME_LIMIT,
            words_file_path=str(WORDS_FILE),
            agent1_name=f"{folder1}:{run1}", agent2_name=f"{folder2}:{run2}",
        )

        match_tasks.append(run_match_async(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    print(f"\nRunning {len(match_tasks)} matches in parallel...")
    results = await asyncio.gather(*match_tasks)

    # Process results and write log
    total1, total2 = 0.0, 0.0
    total_pts1, total_pts2 = 0, 0

    with open(log_f, "w") as f:
        f.write("Match Contenders:\n")
        if num_matches > 0:
            f.write(f"{folder1}:{runs1[0]}\n")
            f.write(f"{folder2}:{runs2[0]}\n\n")

        for result in sorted(results, key=lambda x: x["match_id"]):
            match_id = result["match_id"]
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
                if result.get("stats_block"):
                    status += f"\n--- MATCH STATISTICS ---\n{result['stats_block']}\n"
            else:
                status = f"FAILED: {result.get('error', 'Unknown')}"

            print(f"Match {match_id} Completed. Pts {p1}-{p2}")

            f.write(f"{status}\n")
            f.write("-" * 60 + "\n\n")

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
    print(f"\nLogs saved to: {log_f}")
    print(f"Scoreboard updated: {SCOREBOARD_PATH}")


if __name__ == "__main__":
    asyncio.run(main_async())
