"""
Mancala Match Runner: Orchestrates head-to-head matches for A7-Mancala.

Classic two-rank Mancala: 6 pockets per player, 4 stones per pocket, one
Mancala (store) per player. Stones are sown counter-clockwise, skipping the
opponent's Mancala. Last stone in your own Mancala earns a free turn; last
stone in an empty pocket on your own side captures it plus the pocket across.
The game ends when either row is empty; remaining stones go to their owner.
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

from dotenv import load_dotenv

# Add utils directory to sys.path
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging
from scoreboard import update_scoreboard
from agent_loader import load_stored_agent, consolidate_imports

logger = setup_logging(__name__)

load_dotenv()

# Configuration
try:
    NUM_GAMES_PER_MATCH = int(int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100")) / 10)
except (ValueError, TypeError):
    NUM_GAMES_PER_MATCH = 10

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

# Time limit for one game, agent setup included. Set so ~95% of games finish
# at the pace real agents play (see CLAUDE.md, Game Time Limits); it scales
# with MOVE_TIME_LIMIT. A game still running when it is used up ends as a draw.
GAME_TIME_LIMIT = 25 * MOVE_TIME_LIMIT

# So a match takes at most GAME_TIME_LIMIT per game. The hard kill waits
# MATCH_KILL_GRACE more seconds and only fires if an agent hangs inside a
# single move (e.g. by swallowing the per-move timeout).
MATCH_TIME_LIMIT = GAME_TIME_LIMIT * NUM_GAMES_PER_MATCH
MATCH_KILL_GRACE = 60

# Tie-breaker for a forfeit: the largest possible Mancala difference (48-0).
FORFEIT_SCORE = 48

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / "mancala"
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / "A7-scoreboard.txt"
AGENTS_DIR = BASE_DIR / "agents"
GAME_NAME = "A7-Mancala"
AGENT_CLASS = "MancalaAgent"


# ============================================================
# Shared game engine code (used by both match and human modes)
# ============================================================
GAME_ENGINE_CODE = r'''
class MancalaGame:
    """
    Classic two-rank Mancala (6 pockets per side, 4 stones per pocket).

    Absolute board: 14 stone counts in counter-clockwise sowing order.
        0-5   P1 pockets (P1's left to right)    6   P1 Mancala
        7-12  P2 pockets (P2's left to right)    13  P2 Mancala
    Player index 0 is P1 (moves first), 1 is P2. The pocket across from
    pocket index i is 12 - i. Player p's pocket k is absolute index 7*p + k,
    and rotating the board by 7*p gives p's own perspective, which is what
    agents see.

    No move limit is needed: a move that does not reach a Mancala keeps its
    stones on the mover's row and moves them closer to the mover's Mancala,
    and every other move adds at least one stone to a Mancala, so every game
    ends.
    """

    PLAYERS = ('P1', 'P2')
    POCKETS = 6
    STONES_PER_POCKET = 4

    def __init__(self):
        self.board = [self.STONES_PER_POCKET] * 6 + [0] + [self.STONES_PER_POCKET] * 6 + [0]
        self.current = 0
        self.move_number = 0

    @staticmethod
    def store_index(p):
        return 6 + 7 * p

    def side_stones(self, p):
        start = 7 * p
        return sum(self.board[start:start + 6])

    def legal_moves(self, p):
        start = 7 * p
        return [k for k in range(6) if self.board[start + k] > 0]

    def relative_board(self, p):
        """The board from player p's seat: p's pockets and Mancala first."""
        return self.board[7 * p:] + self.board[:7 * p]

    def state_for(self, p):
        return {
            "board": self.relative_board(p),
            "legal_moves": self.legal_moves(p),
            "player": self.PLAYERS[p],
            "move_number": self.move_number,
        }

    def validate_move(self, move, p):
        """Return (ok, reason). A move is a pocket index 0-5 holding stones."""
        if isinstance(move, bool) or not isinstance(move, int):
            return False, f"not an int: {move!r}"
        if not 0 <= move <= 5:
            return False, f"pocket {move} out of range [0, 5]"
        if self.board[7 * p + move] == 0:
            return False, f"pocket {move} is empty"
        return True, ""

    def is_over(self):
        return self.side_stones(0) == 0 or self.side_stones(1) == 0

    def apply_move(self, pocket, p):
        """
        Sow from player p's pocket (0-5). The move must be valid.
        Updates current player and move_number. Returns a dict:
            sown, extra_turn, captured (total stones moved to the Mancala by
            a capture, 0 if none), captured_across (opponent stones taken),
            game_over, swept ([P1, P2] stones moved by the final sweep).
        """
        board = self.board
        own_store = 6 + 7 * p
        opp_store = 13 - 7 * p
        idx = 7 * p + pocket
        stones = board[idx]
        board[idx] = 0
        sown = stones
        while stones > 0:
            idx = (idx + 1) % 14
            if idx == opp_store:
                continue
            board[idx] += 1
            stones -= 1

        extra_turn = idx == own_store
        captured = 0
        captured_across = 0
        if 7 * p <= idx < 7 * p + 6 and board[idx] == 1:
            opposite = 12 - idx
            captured_across = board[opposite]
            captured = 1 + captured_across
            board[own_store] += captured
            board[idx] = 0
            board[opposite] = 0

        self.move_number += 1

        swept = [0, 0]
        game_over = self.is_over()
        if game_over:
            extra_turn = False
            for q in (0, 1):
                start = 7 * q
                swept[q] = sum(board[start:start + 6])
                board[6 + 7 * q] += swept[q]
                for i in range(start, start + 6):
                    board[i] = 0
        elif not extra_turn:
            self.current = 1 - p

        return {
            "sown": sown,
            "extra_turn": extra_turn,
            "captured": captured,
            "captured_across": captured_across,
            "game_over": game_over,
            "swept": swept,
        }

    def board_lines(self):
        """Board drawn with P1 at the bottom, P2 at the top."""
        b = self.board
        top = "".join(f"[{b[12 - c]:>2}]" for c in range(6))
        bottom = "".join(f"[{b[c]:>2}]" for c in range(6))
        top_nums = "".join(f"  {5 - c} " for c in range(6))
        bottom_nums = "".join(f"  {c} " for c in range(6))
        return [
            f"    {top_nums}   <- P2 pockets",
            f"    {top}",
            f"[{b[13]:>2}]{' ' * 24}[{b[6]:>2}]",
            f"    {bottom}",
            f"    {bottom_nums}   <- P1 pockets",
            f"P2 Mancala (left): {b[13]}   P1 Mancala (right): {b[6]}",
        ]
'''


# ============================================================
# Match runner code (play_game + main for agent-vs-agent)
# ============================================================
MATCH_RUNNER_CODE = r'''
# Private aliases: agent code above may rebind these module-level names.
import random as _runner_random
import signal as _runner_signal
from time import monotonic as _runner_monotonic


class MoveTimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")


total_moves = 0
time_limit_draws = 0


def print_outcome(result_text, first, second, points, scores):
    print("-" * 40)
    print(f"Final Result: {result_text}")
    print("-" * 40)
    print("Points:")
    print(f"{first}: {points[first]}")
    print(f"{second}: {points[second]}")
    print("-" * 40)
    print("Scores:")
    print(f"{first}: {scores[first]}")
    print(f"{second}: {scores[second]}")
    print("=" * 60)


def record_win(match_stats, winner, loser, margin):
    match_stats[winner]["wins"] += 1
    match_stats[winner]["points"] += 3
    match_stats[winner]["score"] += margin
    match_stats[loser]["losses"] += 1
    match_stats[loser]["score"] -= margin


def record_draw(match_stats):
    for agent_key in ("Agent-1", "Agent-2"):
        match_stats[agent_key]["draws"] += 1
        match_stats[agent_key]["points"] += 1


def play_game(game_num, match_stats, opening=None):
    """Play one game. The engine first sows P1's pocket `opening` (random if
    None). The game clock includes agent setup; if it passes GAME_TIME_LIMIT
    before a move, the game ends as a draw."""
    global total_moves, time_limit_draws
    game = MancalaGame()
    game_start = _runner_monotonic()
    game_deadline = game_start + GAME_TIME_LIMIT

    # Alternate who moves first each game (P1 moves first)
    if game_num % 2 == 1:
        classes = (MancalaAgent_1, MancalaAgent_2)
        names = ("Agent-1", "Agent-2")
    else:
        classes = (MancalaAgent_2, MancalaAgent_1)
        names = ("Agent-2", "Agent-1")
    seat = {names[0]: "P1", names[1]: "P2"}

    print()
    print("=" * 60)
    print(f"Game {game_num}")
    print(f"Agent-1: {AGENT1_INFO} ({seat['Agent-1']})")
    print(f"Agent-2: {AGENT2_INFO} ({seat['Agent-2']})")
    print("-" * 60)

    # --- Init agents (crash = forfeit) ---
    agents = []
    for p in (0, 1):
        try:
            agents.append(classes[p](names[p], game.PLAYERS[p]))
        except Exception as e:
            crasher, winner = names[p], names[1 - p]
            print(f"{crasher} ({game.PLAYERS[p]}) init crash: {str(e)[:200]}")
            match_stats[crasher]["other_crash"] += 1
            record_win(match_stats, winner, crasher, FORFEIT_SCORE)
            print("Final Position: N/A (initialization crash)")
            print_outcome(
                f"{winner} wins by forfeit ({crasher} crashed during initialization)",
                winner, crasher,
                {winner: 3, crasher: 0},
                {winner: FORFEIT_SCORE, crasher: -FORFEIT_SCORE},
            )
            sys.stdout.flush()
            return winner

    # Random opening: the engine plays P1's first move. It counts as P1's
    # move, so pocket 2 (last stone in P1's Mancala) gives P1 a free turn.
    if opening is None:
        opening = _runner_random.randrange(6)
    info = game.apply_move(opening, 0)
    total_moves += 1
    print(
        f"Random opening: P1 pocket {opening} ({info['sown']} stones)"
        f"{' -> extra turn' if info['extra_turn'] else ''}"
    )

    result_text = None

    while True:
        if _runner_monotonic() >= game_deadline:
            time_limit_draws += 1
            result_text = (
                f"Draw (time limit reached after {_runner_monotonic() - game_start:.0f}s)"
            )
            break

        p = game.current
        name = names[p]
        label = f"{name} ({game.PLAYERS[p]})"
        legal = game.legal_moves(p)
        state = game.state_for(p)

        move = None
        failed = False
        try:
            _runner_signal.signal(_runner_signal.SIGALRM, timeout_handler)
            _runner_signal.alarm(max(1, int(MOVE_TIMEOUT)))
            try:
                move = agents[p].make_move(state)
            finally:
                _runner_signal.alarm(0)
        except MoveTimeoutException:
            print(f"{label}: TIMEOUT")
            match_stats[name]["timeout"] += 1
            failed = True
        except Exception as e:
            print(f"{label}: CRASH '{str(e)[:80]}'")
            match_stats[name]["make_move_crash"] += 1
            failed = True
        else:
            ok, reason = game.validate_move(move, p)
            if not ok:
                print(f"{label}: INVALID {reason}")
                match_stats[name]["invalid"] += 1
                failed = True

        if failed:
            move = _runner_random.choice(legal)

        info = game.apply_move(move, p)
        total_moves += 1

        sown = info["sown"]
        desc = (
            f"{label}: {'random ' if failed else ''}pocket {move} "
            f"({sown} stone{'' if sown == 1 else 's'})"
        )
        if info["extra_turn"]:
            desc += " -> extra turn"
            match_stats[name]["extra_turns"] += 1
        if info["captured"]:
            desc += f" -> capture {info['captured']} ({info['captured_across']} from across)"
            match_stats[name]["captures"] += 1
        print(desc)

        if info["game_over"]:
            swept = info["swept"]
            print(f"Row empty. Final sweep: P1 +{swept[0]}, P2 +{swept[1]}")
            break

    print()
    print("Final Position:")
    for line in game.board_lines():
        print(f"BOARD: {line}")
    s1, s2 = game.board[6], game.board[13]
    print(f"Mancalas: P1={s1} P2={s2}")

    if result_text is not None:
        winner = "DRAW"
    elif s1 == s2:
        winner = "DRAW"
        result_text = f"Draw {s1}-{s2}"
    else:
        w = 0 if s1 > s2 else 1
        winner, loser = names[w], names[1 - w]
        high, low = max(s1, s2), min(s1, s2)
        margin = high - low
        result_text = f"{winner} ({game.PLAYERS[w]}) wins {high}-{low}"

    if winner == "DRAW":
        record_draw(match_stats)
        print_outcome(
            result_text, "Agent-1", "Agent-2",
            {"Agent-1": 1, "Agent-2": 1}, {"Agent-1": 0, "Agent-2": 0},
        )
    else:
        record_win(match_stats, winner, loser, margin)
        print_outcome(
            result_text, winner, loser,
            {winner: 3, loser: 0}, {winner: margin, loser: -margin},
        )

    sys.stdout.flush()
    return winner


def main():
    match_stats = {
        agent_key: {
            "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0, "captures": 0, "extra_turns": 0,
        }
        for agent_key in ("Agent-1", "Agent-2")
    }

    # Every game gets the same GAME_TIME_LIMIT; a game that overruns it is a
    # draw. Games are played in pairs (1-2, 3-4, ...) that share one random
    # opening with seats swapped, so each agent plays both sides of it.
    opening = None
    for i in range(NUM_GAMES):
        if i % 2 == 0:
            opening = _runner_random.randrange(6)
        play_game(i + 1, match_stats, opening)
        sys.stdout.flush()

    # Aggregate crash stat for backward compatibility
    for agent_key in ("Agent-1", "Agent-2"):
        match_stats[agent_key]["crash"] = (
            match_stats[agent_key]["make_move_crash"]
            + match_stats[agent_key]["other_crash"]
        )

    print("=" * 60)
    print(f"Agent-1: {AGENT1_INFO}")
    print(f"Agent-2: {AGENT2_INFO}")
    print(f"RESULT:Agent-1={match_stats['Agent-1']['points']},Agent-2={match_stats['Agent-2']['points']}")
    print(f"SCORE:Agent-1={match_stats['Agent-1']['score']},Agent-2={match_stats['Agent-2']['score']}")
    print(f"WINS:Agent-1={match_stats['Agent-1']['wins']},Agent-2={match_stats['Agent-2']['wins']}")
    print(f"DRAWS:{match_stats['Agent-1']['draws']}")
    print(f"STATS:Agent-1={match_stats['Agent-1']}")
    print(f"STATS:Agent-2={match_stats['Agent-2']}")
    print()
    print("--- MATCH STATISTICS ---")
    for agent_key in ("Agent-1", "Agent-2"):
        print(f"{agent_key} make_move_crash: {match_stats[agent_key]['make_move_crash']}")
    for agent_key in ("Agent-1", "Agent-2"):
        print(f"{agent_key} other_crash: {match_stats[agent_key]['other_crash']}")
    for agent_key in ("Agent-1", "Agent-2"):
        print(f"{agent_key} crash (total): {match_stats[agent_key]['crash']}")
    for agent_key in ("Agent-1", "Agent-2"):
        print(f"{agent_key} Timeouts: {match_stats[agent_key]['timeout']}")
    for agent_key in ("Agent-1", "Agent-2"):
        print(f"{agent_key} Invalid: {match_stats[agent_key]['invalid']}")
    for agent_key in ("Agent-1", "Agent-2"):
        print(f"{agent_key} Captures: {match_stats[agent_key]['captures']}")
    for agent_key in ("Agent-1", "Agent-2"):
        print(f"{agent_key} Extra Turns: {match_stats[agent_key]['extra_turns']}")
    print(f"Total Moves: {total_moves}")
    print(f"Time-limit Draws: {time_limit_draws}")


if __name__ == "__main__":
    main()
'''


# ============================================================
# Human play mode code
# ============================================================
HUMAN_PLAY_CODE = r'''
import random


class HumanAgent:
    def __init__(self, name, player):
        self.name = name
        self.player = player

    def make_move(self, state):
        legal = state["legal_moves"]
        while True:
            raw = input(f"{self.name} ({self.player}), choose a pocket {legal}: ").strip()
            try:
                pocket = int(raw)
            except ValueError:
                print("Please enter a pocket number.")
                continue
            if pocket in legal:
                return pocket
            print(f"Pocket {pocket} is not a legal move.")


class RandomAgent:
    def __init__(self, name, player):
        self.name = name
        self.player = player

    def make_move(self, state):
        return random.choice(state["legal_moves"])


MODE_TITLES = {
    "humanvsbot": "Human vs Random Bot",
    "humanvshuman": "Human vs Human",
    "humanvsagent": "Human vs Stored Agent",
}


def print_board(game):
    print()
    for line in game.board_lines():
        print(line)
    print()


if __name__ == "__main__":
    print("=" * 60)
    print(f"MANCALA - {MODE_TITLES.get(GAME_MODE, GAME_MODE)}")
    print("=" * 60)
    print("Sow counter-clockwise; your Mancala is on your right.")
    print("Pockets are numbered 0-5 from your own left. P1 sits at the")
    print("bottom, P2 at the top. Last stone in your Mancala = free turn;")
    print("last stone in an empty pocket on your side = capture.")

    if GAME_MODE == "humanvsbot":
        seats = [(HumanAgent, "Human"), (RandomAgent, "Bot")]
    elif GAME_MODE == "humanvshuman":
        seats = [(HumanAgent, "Player 1"), (HumanAgent, "Player 2")]
    else:
        seats = [(HumanAgent, "Human"), (MancalaAgent_1, "Agent")]
    if GAME_MODE != "humanvshuman" and random.random() < 0.5:
        seats.reverse()
    players = [cls(name, MancalaGame.PLAYERS[p]) for p, (cls, name) in enumerate(seats)]
    print(f"P1 (moves first, bottom row): {players[0].name}")
    print(f"P2 (top row): {players[1].name}")

    game = MancalaGame()
    opening = random.randrange(6)
    info = game.apply_move(opening, 0)
    print()
    print(f"Random opening: P1 pocket {opening} ({info['sown']} stones)"
          f"{' -> extra turn for P1' if info['extra_turn'] else ''}")
    while True:
        p = game.current
        agent = players[p]
        print_board(game)
        state = game.state_for(p)
        try:
            move = agent.make_move(state)
        except Exception as e:
            print(f"{agent.name} crashed: {e}")
            move = None
        ok, reason = game.validate_move(move, p)
        if not ok:
            move = random.choice(state["legal_moves"])
            print(f"{agent.name}: invalid move ({reason}), playing random pocket {move}")
        info = game.apply_move(move, p)
        sown = info["sown"]
        desc = (
            f"{agent.name} ({game.PLAYERS[p]}) sows pocket {move} "
            f"({sown} stone{'' if sown == 1 else 's'})"
        )
        if info["extra_turn"]:
            desc += " -> extra turn!"
        if info["captured"]:
            desc += f" -> captures {info['captured']}!"
        print(desc)
        if info["game_over"]:
            swept = info["swept"]
            print(f"A row is empty. Final sweep: P1 +{swept[0]}, P2 +{swept[1]}")
            break

    print_board(game)
    s1, s2 = game.board[6], game.board[13]
    if s1 == s2:
        print(f"GAME OVER: Draw {s1}-{s2}")
    else:
        w = 0 if s1 > s2 else 1
        print(f"GAME OVER: {players[w].name} ({game.PLAYERS[w]}) wins {max(s1, s2)}-{min(s1, s2)}")
    print("Thanks for playing!")
'''


# ============================================================
# Outer layer: agent loading, match orchestration, logging
# ============================================================

def find_model_folder(pattern: str) -> str | None:
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
    model_dir = AGENTS_DIR / model_folder
    runs = []
    pattern = re.compile(rf"^{re.escape(game)}_(\d+)\.py$")

    for file in model_dir.glob(f"{game}_*.py"):
        match = pattern.match(file.name)
        if match:
            runs.append(int(match.group(1)))

    return sorted(runs)


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
    move_timeout: float,
    agent1_info: str,
    agent2_info: str,
    game_time_limit: float = GAME_TIME_LIMIT,
) -> str:
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
        f"GAME_TIME_LIMIT = {game_time_limit}\n"
        f"FORFEIT_SCORE = {FORFEIT_SCORE}\n"
        f"AGENT1_INFO = {agent1_info!r}\n"
        f"AGENT2_INFO = {agent2_info!r}\n"
    )

    return "\n\n".join([
        header,
        extra_imports,
        agent1_code,
        agent2_code,
        GAME_ENGINE_CODE,
        MATCH_RUNNER_CODE,
    ])


def build_human_game_code(
    mode: str, agent_code: str = "", agent_imports: str = ""
) -> str:
    parts = [f'GAME_MODE = "{mode}"\n']
    if mode == "humanvsagent" and agent_imports:
        parts.append(agent_imports)
    if mode == "humanvsagent" and agent_code:
        parts.append(agent_code)
    parts.append(GAME_ENGINE_CODE)
    parts.append(HUMAN_PLAY_CODE)
    return "\n\n".join(parts)


def run_match(
    game_code: str, match_id: int, run_ids: tuple[int, int],
    timeout: int = MATCH_TIME_LIMIT + MATCH_KILL_GRACE,
) -> dict:
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"mancala_match_{match_id}_{temp_id}.py"
    )

    failure = {
        "match_id": match_id,
        "agent1_run_id": run_ids[0],
        "agent2_run_id": run_ids[1],
        "success": False,
        "agent1_score": 0,
        "agent2_score": 0,
    }

    try:
        with open(temp_file, "w") as f:
            f.write(game_code)

        result = subprocess.run(
            ["python", temp_file], capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            return {**failure, "error": result.stderr[:500]}

        match = re.search(
            r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout
        )
        if not match:
            return {**failure, "error": "Could not parse results:\n" + result.stdout[:200]}

        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        wins_match = re.search(r"WINS:Agent-1=(\d+),Agent-2=(\d+)", result.stdout)
        draws_match = re.search(r"DRAWS:(\d+)", result.stdout)
        score_match = re.search(
            r"SCORE:Agent-1=(-?[\d.]+),Agent-2=(-?[\d.]+)", result.stdout
        )

        return {
            "match_id": match_id,
            "agent1_run_id": run_ids[0],
            "agent2_run_id": run_ids[1],
            "success": True,
            "agent1_score": float(score_match.group(1)) if score_match else 0.0,
            "agent2_score": float(score_match.group(2)) if score_match else 0.0,
            "agent1_wins": int(wins_match.group(1)) if wins_match else 0,
            "agent2_wins": int(wins_match.group(2)) if wins_match else 0,
            "agent1_points": int(float(match.group(1))),
            "agent2_points": int(float(match.group(2))),
            "draws": int(draws_match.group(1)) if draws_match else 0,
            "error": None,
            "stats_block": stats_block,
            "log": result.stdout,
        }

    except Exception as e:
        return {**failure, "error": str(e)}
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def run_match_async(
    game_code: str, match_id: int, run_ids: tuple[int, int]
) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


def run_human_mode(human_mode: str, agent_specs: list[str] | None) -> None:
    if human_mode == "humanvsagent":
        if not agent_specs or len(agent_specs) != 1:
            print("ERROR: --humanvsagent requires exactly 1 --agent spec.")
            print("Example: --humanvsagent --agent mistral:1")
            sys.exit(1)
        model_pattern, runs = parse_agent_spec(agent_specs[0])
        folder = find_model_folder(model_pattern)
        if not folder:
            sys.exit(1)
        if not runs:
            runs = get_available_runs(folder, GAME_NAME)
        if not runs:
            print(f"ERROR: No runs found for {folder}/{GAME_NAME}")
            sys.exit(1)
        agent_code, agent_imports = load_stored_agent(
            folder, GAME_NAME, runs[0], 1, AGENT_CLASS
        )
        if not agent_code:
            print(f"ERROR: Failed to load agent from {folder}")
            sys.exit(1)
        game_code = build_human_game_code("humanvsagent", agent_code, agent_imports)
    elif agent_specs:
        print("ERROR: --agent is not used with --humanvsbot or --humanvshuman.")
        sys.exit(1)
    else:
        game_code = build_human_game_code(human_mode)

    temp_file = os.path.join(
        tempfile.gettempdir(), f"mancala_{human_mode}_{uuid.uuid4().hex[:8]}.py"
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


async def main_async():
    parser = argparse.ArgumentParser(description="Run Mancala matches between stored AI agents")
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
    parser.add_argument(
        "--parallel", type=int, default=4,
        help="Number of matches to run in parallel",
    )
    args = parser.parse_args()

    for mode in ("humanvsbot", "humanvshuman", "humanvsagent"):
        if getattr(args, mode):
            run_human_mode(mode, args.agent)
            return

    if not args.agent or len(args.agent) != 2:
        print("ERROR: Need exactly 2 agent specifications.")
        print("Example: --agent mistral:1 gpt-5-mini:1")
        sys.exit(1)

    model1_pattern, runs1 = parse_agent_spec(args.agent[0])
    model2_pattern, runs2 = parse_agent_spec(args.agent[1])

    folder1 = find_model_folder(model1_pattern)
    folder2 = find_model_folder(model2_pattern)

    if not folder1 or not folder2:
        sys.exit(1)

    runs_explicitly_specified = bool(runs1 or runs2)

    if not runs1:
        runs1 = get_available_runs(folder1, GAME_NAME)
    if not runs2:
        runs2 = get_available_runs(folder2, GAME_NAME)

    num_matches = min(len(runs1), len(runs2))
    if len(runs1) != len(runs2):
        logger.warning(
            "Run count mismatch: %s (%d) vs %s (%d). Using first %d.",
            folder1, len(runs1), folder2, len(runs2), num_matches,
        )

    if not runs_explicitly_specified:
        runs1 = runs1[:num_matches] * args.parallel
        runs2 = runs2[:num_matches] * args.parallel
    else:
        runs1 = runs1[:num_matches]
        runs2 = runs2[:num_matches]
    num_matches = len(runs1)

    print("\n" + "=" * 60)
    print("MANCALA MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    match_tasks = []
    semaphore = asyncio.Semaphore(args.parallel)

    async def sem_task(gc, mid, rids):
        async with semaphore:
            return await run_match_async(gc, mid, rids)

    for i in range(num_matches):
        run1 = runs1[i]
        run2 = runs2[i]

        code1, imp1 = load_stored_agent(folder1, GAME_NAME, run1, 1, AGENT_CLASS)
        code2, imp2 = load_stored_agent(folder2, GAME_NAME, run2, 2, AGENT_CLASS)

        if not code1 or not code2:
            print(f"  FAILED to load match {i + 1}")
            continue

        extra_imports = consolidate_imports(imp1, imp2)

        game_code = build_game_code(
            code1, code2, extra_imports, NUM_GAMES_PER_MATCH,
            MOVE_TIME_LIMIT, f"{folder1}:{run1}", f"{folder2}:{run2}",
        )

        match_tasks.append(sem_task(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    match_word = "match" if len(match_tasks) == 1 else "matches"
    parallel_info = f" (up to {args.parallel} in parallel)" if len(match_tasks) > 1 else ""
    print(f"\nRunning {len(match_tasks)} {match_word}{parallel_info}...")
    results = await asyncio.gather(*match_tasks)

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
        if result["success"]:
            print(f"MINI:{folder1}:{run1}={p1},{s1}|{folder2}:{run2}={p2},{s2}")

        with open(log_f, "w") as f:
            f.write("Match Contenders:\n")
            f.write(f"{folder1}:{run1}\n")
            f.write(f"{folder2}:{run2}\n\n")
            f.write(f"{status}\n")
            f.write("-" * 60 + "\n")

        if result["success"] and args.update_scoreboard:
            update_scoreboard(
                SCOREBOARD_PATH, f"{folder1}:{run1}",
                games_played=NUM_GAMES_PER_MATCH,
                wins=result.get("agent1_wins", 0),
                losses=result.get("agent2_wins", 0),
                draws=result.get("draws", 0),
                score=result["agent1_score"],
                points=result.get("agent1_points", 0),
            )
            update_scoreboard(
                SCOREBOARD_PATH, f"{folder2}:{run2}",
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

    # Exit non-zero so the matchmaker reports failed matches instead of
    # counting them as succeeded.
    failed = [r for r in results if not r["success"]]
    if failed:
        for r in failed:
            print(
                f"Match {r['match_id']} FAILED: {str(r.get('error', 'Unknown'))[:200]}",
                file=sys.stderr,
            )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main_async())
