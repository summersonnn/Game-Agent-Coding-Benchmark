"""
LieOnce Match Runner: Orchestrates head-to-head matches between two AI models.

Spawns a subprocess per match that runs NUM_GAMES_PER_MATCH games of LieOnce.
Each agent picks a hidden number in [1, 100] and the players alternate guesses;
each agent may lie once. The runner verifies all responses against the truth,
detects second-lie forfeits, and emits structured RESULT/SCORE/WINS/DRAWS lines
that the outer layer parses for scoreboard updates.
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

sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging
from scoreboard import update_scoreboard
from agent_loader import load_stored_agent, consolidate_imports

logger = setup_logging(__name__)

load_dotenv()

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

RESULTS_DIR = Path(__file__).parent.parent / "results" / "lie_once"
SCOREBOARD_PATH = Path(__file__).parent.parent / "scoreboard" / "A2-scoreboard.txt"
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A2-LieOnce"

GAME_ENGINE_CODE = '''
class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

VALID_RESPONSES = ("Up", "Down", "Correct")
MAX_TURNS = 100
MAX_PICK_SCORE = 100  # forfeit-before-any-guess gives opponent this score
MAX_RESPONSES_FOR_LIE = 10  # lies are only legal on respond calls 1..10 (per agent)


def compute_truth(secret, guess):
    if guess == secret:
        return "Correct"
    if secret > guess:
        return "Up"
    return "Down"
'''

MATCH_RUNNER_CODE = '''
def opp_of(name):
    return "Agent-2" if name == "Agent-1" else "Agent-1"


def call_with_timeout(fn, *args):
    """Run fn(*args) under signal.alarm. Returns (value, error_kind, exc).

    error_kind in {None, "timeout", "crash"}.
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(MOVE_TIMEOUT) if MOVE_TIMEOUT >= 1 else 1)
    try:
        try:
            value = fn(*args)
        finally:
            signal.alarm(0)
    except MoveTimeoutException as e:
        return None, "timeout", e
    except Exception as e:
        return None, "crash", e
    return value, None, None


def record_pick_forfeit(loser, reason, match_stats, kind):
    """Loser fails at pick_number; opponent wins with max score."""
    winner = opp_of(loser)
    score = MAX_PICK_SCORE
    print(f"  -> {loser} {reason}; {winner} wins by forfeit (score {score})")
    print("----------------------------------------")
    print(f"Final Result: {winner} wins ({reason})")
    print("Points:")
    print(f"{winner}: 3")
    print(f"{loser}: 0")
    print("Scores:")
    print(f"{winner}: {score}")
    print(f"{loser}: -{score}")
    print("=" * 60)
    match_stats[winner]["wins"] += 1
    match_stats[winner]["points"] += 3
    match_stats[winner]["score"] += score
    match_stats[loser]["losses"] += 1
    match_stats[loser]["score"] -= score
    if kind:
        match_stats[loser][kind] += 1
    return winner


def record_win(winner, loser, reason, winner_guess_count, match_stats):
    score = max(0, MAX_TURNS - winner_guess_count)
    print(f"  -> {winner} wins ({reason}); guesses={winner_guess_count} score={score}")
    print("----------------------------------------")
    print(f"Final Result: {winner} wins ({reason})")
    print("Points:")
    print(f"{winner}: 3")
    print(f"{loser}: 0")
    print("Scores:")
    print(f"{winner}: {score}")
    print(f"{loser}: -{score}")
    print("=" * 60)
    match_stats[winner]["wins"] += 1
    match_stats[winner]["points"] += 3
    match_stats[winner]["score"] += score
    match_stats[loser]["losses"] += 1
    match_stats[loser]["score"] -= score
    return winner


def record_draw(reason, match_stats):
    print(f"  -> DRAW ({reason})")
    print("----------------------------------------")
    print(f"Final Result: Draw ({reason})")
    print("Points:")
    print("Agent-1: 1")
    print("Agent-2: 1")
    print("Scores:")
    print("Agent-1: 0")
    print("Agent-2: 0")
    print("=" * 60)
    match_stats["Agent-1"]["draws"] += 1
    match_stats["Agent-1"]["points"] += 1
    match_stats["Agent-2"]["draws"] += 1
    match_stats["Agent-2"]["points"] += 1
    return "DRAW"


def make_state(agent, secrets, lies_used, response_count, turn, starter, is_tie, last_response=None):
    return {
        "your_number": secrets[agent],
        "your_lie_used": lies_used[agent],
        "your_response_count": response_count[agent],
        "turn": turn,
        "you_started": agent == starter,
        "is_tie_attempt": is_tie,
        "last_response": last_response,
    }


def play_game(game_num, match_stats):
    """Plays one LieOnce game and returns winner name or 'DRAW'."""
    if game_num % 2 == 1:
        starter = "Agent-1"
    else:
        starter = "Agent-2"
    non_starter = opp_of(starter)
    agent_classes = {"Agent-1": LieOnceAgent_1, "Agent-2": LieOnceAgent_2}

    print("=" * 60)
    print(f"Game {game_num}")
    print(f"Agent-1: {AGENT1_NAME}")
    print(f"Agent-2: {AGENT2_NAME}")
    print(f"Starter: {starter}")
    print("-" * 60)

    agents = {}
    for ag in ("Agent-1", "Agent-2"):
        try:
            agents[ag] = agent_classes[ag](ag)
        except Exception as e:
            print(f"{ag} INIT CRASH: {e}")
            return record_pick_forfeit(ag, "init_crash", match_stats, "other_crash")

    secrets = {}
    for ag in ("Agent-1", "Agent-2"):
        value, err, exc = call_with_timeout(agents[ag].pick_number)
        if err == "timeout":
            print(f"{ag} pick_number TIMEOUT")
            return record_pick_forfeit(ag, "pick_timeout", match_stats, "timeout")
        if err == "crash":
            print(f"{ag} pick_number CRASH: {exc}")
            return record_pick_forfeit(ag, "pick_crash", match_stats, "make_move_crash")
        if isinstance(value, bool) or not isinstance(value, int):
            print(f"{ag} INVALID PICK (non-integer): {value!r}")
            return record_pick_forfeit(ag, "invalid_pick_type", match_stats, "invalid")
        if not (1 <= value <= 100):
            print(f"{ag} INVALID PICK (out-of-range): {value}")
            return record_pick_forfeit(ag, "invalid_pick_range", match_stats, "invalid")
        secrets[ag] = value

    print(f"Agent-1 secret: {secrets['Agent-1']}")
    print(f"Agent-2 secret: {secrets['Agent-2']}")
    print("-" * 60)

    lies_used = {"Agent-1": False, "Agent-2": False}
    guess_count = {"Agent-1": 0, "Agent-2": 0}
    response_count = {"Agent-1": 0, "Agent-2": 0}
    last_response = {"Agent-1": None, "Agent-2": None}
    turn = 0
    current = starter

    while turn < MAX_TURNS:
        turn += 1
        opp = opp_of(current)

        state_g = make_state(
            current, secrets, lies_used, response_count, turn, starter, False, last_response[current]
        )
        g_val, g_err, g_exc = call_with_timeout(agents[current].guess, state_g)
        guess_count[current] += 1

        if g_err == "timeout":
            match_stats[current]["timeout"] += 1
            print(f"Turn {turn}: {current} guess TIMEOUT (turn lost)")
            current = opp
            continue
        if g_err == "crash":
            match_stats[current]["make_move_crash"] += 1
            print(f"Turn {turn}: {current} guess CRASH: {g_exc} (turn lost)")
            current = opp
            continue
        if isinstance(g_val, bool) or not isinstance(g_val, int):
            match_stats[current]["invalid"] += 1
            print(f"Turn {turn}: {current} ILLEGAL GUESS: {g_val!r} (turn lost)")
            current = opp
            continue

        guess_int = g_val
        state_r = make_state(opp, secrets, lies_used, response_count, turn, starter, False)
        r_val, r_err, r_exc = call_with_timeout(agents[opp].respond, state_r, guess_int)
        response_count[opp] += 1

        if r_err == "timeout":
            match_stats[opp]["timeout"] += 1
            print(f"Turn {turn}: {current} guesses {guess_int}; {opp} respond TIMEOUT")
            return record_win(current, opp, "respond_timeout", guess_count[current], match_stats)
        if r_err == "crash":
            match_stats[opp]["make_move_crash"] += 1
            print(f"Turn {turn}: {current} guesses {guess_int}; {opp} respond CRASH: {r_exc}")
            return record_win(current, opp, "respond_crash", guess_count[current], match_stats)
        if r_val not in VALID_RESPONSES:
            match_stats[opp]["invalid"] += 1
            print(f"Turn {turn}: {current} guesses {guess_int}; {opp} INVALID RESPONSE: {r_val!r}")
            return record_win(current, opp, "invalid_response", guess_count[current], match_stats)

        truth = compute_truth(secrets[opp], guess_int)
        is_lie = (r_val != truth)

        suffix = f"truth={truth}"
        if is_lie:
            suffix += " [LIE]"
        print(f"Turn {turn}: {current} guesses {guess_int}; {opp} responds '{r_val}' ({suffix})")

        if is_lie:
            if lies_used[opp]:
                match_stats[opp]["second_lie"] += 1
                print(f"  -> {opp} attempted SECOND LIE; forfeit")
                return record_win(current, opp, "second_lie", guess_count[current], match_stats)
            if response_count[opp] > MAX_RESPONSES_FOR_LIE:
                match_stats[opp]["late_lie"] += 1
                print(
                    f"  -> {opp} attempted LIE on response {response_count[opp]} "
                    f"(window closes after {MAX_RESPONSES_FOR_LIE}); forfeit"
                )
                return record_win(current, opp, "late_lie", guess_count[current], match_stats)
            lies_used[opp] = True
            match_stats[opp]["lies"] += 1

        last_response[current] = r_val

        if r_val == "Correct" and truth == "Correct":
            if current == starter and turn < MAX_TURNS:
                tie_outcome = run_tie_attempt(
                    turn, secrets, agents, lies_used, response_count, guess_count, match_stats,
                    starter, non_starter, last_response[non_starter],
                )
                return tie_outcome
            return record_win(current, opp, "correct_guess", guess_count[current], match_stats)

        current = opp

    return record_draw("turn_cap_reached", match_stats)


def run_tie_attempt(prev_turn, secrets, agents, lies_used, response_count, guess_count, match_stats, starter, non_starter, ns_last_response=None):
    """Non-starter gets one final guess; starter responds. Returns winner name or 'DRAW'."""
    turn = prev_turn + 1
    print(f"-- TIE-ATTEMPT (turn {turn}): {non_starter} gets one final guess --")

    state_g = make_state(non_starter, secrets, lies_used, response_count, turn, starter, True, ns_last_response)
    g_val, g_err, g_exc = call_with_timeout(agents[non_starter].guess, state_g)
    guess_count[non_starter] += 1

    if g_err == "timeout":
        match_stats[non_starter]["timeout"] += 1
        print(f"Tie-attempt: {non_starter} guess TIMEOUT (no respond call)")
        return record_win(starter, non_starter, "tie_attempt_failed", guess_count[starter], match_stats)
    if g_err == "crash":
        match_stats[non_starter]["make_move_crash"] += 1
        print(f"Tie-attempt: {non_starter} guess CRASH: {g_exc}")
        return record_win(starter, non_starter, "tie_attempt_failed", guess_count[starter], match_stats)
    if isinstance(g_val, bool) or not isinstance(g_val, int):
        match_stats[non_starter]["invalid"] += 1
        print(f"Tie-attempt: {non_starter} ILLEGAL GUESS: {g_val!r}")
        return record_win(starter, non_starter, "tie_attempt_failed", guess_count[starter], match_stats)

    guess_int = g_val
    state_r = make_state(starter, secrets, lies_used, response_count, turn, starter, True)
    r_val, r_err, r_exc = call_with_timeout(agents[starter].respond, state_r, guess_int)
    response_count[starter] += 1

    if r_err == "timeout":
        match_stats[starter]["timeout"] += 1
        print(f"Tie-attempt: {starter} respond TIMEOUT (forfeit)")
        return record_win(non_starter, starter, "tie_respond_timeout", guess_count[non_starter], match_stats)
    if r_err == "crash":
        match_stats[starter]["make_move_crash"] += 1
        print(f"Tie-attempt: {starter} respond CRASH: {r_exc}")
        return record_win(non_starter, starter, "tie_respond_crash", guess_count[non_starter], match_stats)
    if r_val not in VALID_RESPONSES:
        match_stats[starter]["invalid"] += 1
        print(f"Tie-attempt: {starter} INVALID RESPONSE: {r_val!r}")
        return record_win(non_starter, starter, "tie_invalid_response", guess_count[non_starter], match_stats)

    truth = compute_truth(secrets[starter], guess_int)
    is_lie = (r_val != truth)
    suffix = f"truth={truth}"
    if is_lie:
        suffix += " [LIE]"
    print(f"Tie-attempt: {non_starter} guesses {guess_int}; {starter} responds '{r_val}' ({suffix})")

    if is_lie:
        if lies_used[starter]:
            match_stats[starter]["second_lie"] += 1
            print(f"  -> {starter} attempted SECOND LIE in tie-attempt; forfeit")
            return record_win(non_starter, starter, "tie_second_lie", guess_count[non_starter], match_stats)
        if response_count[starter] > MAX_RESPONSES_FOR_LIE:
            match_stats[starter]["late_lie"] += 1
            print(
                f"  -> {starter} attempted LIE on response {response_count[starter]} "
                f"in tie-attempt (window closes after {MAX_RESPONSES_FOR_LIE}); forfeit"
            )
            return record_win(non_starter, starter, "tie_late_lie", guess_count[non_starter], match_stats)
        lies_used[starter] = True
        match_stats[starter]["lies"] += 1

    if r_val == "Correct" and truth == "Correct":
        return record_draw("tie_attempt_success", match_stats)
    return record_win(starter, non_starter, "tie_attempt_failed", guess_count[starter], match_stats)


def main():
    base_stats = {
        "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
        "make_move_crash": 0, "other_crash": 0, "crash": 0,
        "timeout": 0, "invalid": 0, "lies": 0, "second_lie": 0, "late_lie": 0,
    }
    match_stats = {
        "Agent-1": dict(base_stats),
        "Agent-2": dict(base_stats),
    }
    for i in range(NUM_GAMES):
        play_game(i + 1, match_stats)
        sys.stdout.flush()

    for agent in ("Agent-1", "Agent-2"):
        match_stats[agent]["crash"] = (
            match_stats[agent]["make_move_crash"] + match_stats[agent]["other_crash"]
        )

    print("=" * 60)
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
    for agent in ("Agent-1", "Agent-2"):
        s = match_stats[agent]
        print(f"{agent} make_move_crash: {s['make_move_crash']}")
        print(f"{agent} other_crash: {s['other_crash']}")
        print(f"{agent} Timeouts: {s['timeout']}")
        print(f"{agent} Invalid: {s['invalid']}")
        print(f"{agent} Lies used: {s['lies']}")
        print(f"{agent} Second-lie forfeits: {s['second_lie']}")
        print(f"{agent} Late-lie forfeits: {s['late_lie']}")
    print("------------------------------------------------------------")


if __name__ == "__main__":
    main()
'''


HUMAN_GAME_CODE = '''
import sys
import random


VALID_RESPONSES = ("Up", "Down", "Correct")
MAX_TURNS = 100
MAX_RESPONSES_FOR_LIE = 10


def compute_truth(secret, guess):
    if guess == secret:
        return "Correct"
    if secret > guess:
        return "Up"
    return "Down"


class HumanAgent:
    def __init__(self, name):
        self.name = name

    def pick_number(self):
        while True:
            try:
                v = input(f"[{self.name}] Pick your secret integer in [1, 100]: ")
                n = int(v)
                if 1 <= n <= 100:
                    return n
                print("Out of range.")
            except ValueError:
                print("Not an integer.")

    def guess(self, state):
        while True:
            try:
                tag = " (TIE-ATTEMPT)" if state["is_tie_attempt"] else ""
                v = input(f"[{self.name}] Turn {state['turn']}{tag} - guess opponent's number: ")
                return int(v)
            except ValueError:
                print("Not an integer (you will lose your turn). Re-prompt:")

    def respond(self, state, opponent_guess):
        while True:
            tag = " (TIE-ATTEMPT)" if state["is_tie_attempt"] else ""
            window_open = state["your_response_count"] < MAX_RESPONSES_FOR_LIE
            v = input(
                f"[{self.name}] Turn {state['turn']}{tag} - opponent guessed {opponent_guess}. "
                f"Your secret is {state['your_number']}, lie_used={state['your_lie_used']}, "
                f"responses_given={state['your_response_count']} (lie_window_open={window_open}). "
                f"Respond Up/Down/Correct: "
            ).strip()
            if v in VALID_RESPONSES:
                return v
            print("Must be one of Up/Down/Correct.")


class RandomAgent:
    def __init__(self, name):
        self.name = name
        self._lie_used = False

    def pick_number(self):
        return random.randint(1, 100)

    def guess(self, state):
        return random.randint(1, 100)

    def respond(self, state, opponent_guess):
        truth = compute_truth(state["your_number"], opponent_guess)
        if not state["your_lie_used"] and random.random() < 0.05:
            choices = [r for r in VALID_RESPONSES if r != truth]
            return random.choice(choices)
        return truth


def play(starter, agent_a, agent_b):
    """agent_a is Agent-1 (first by name), agent_b is Agent-2."""
    agents = {"Agent-1": agent_a, "Agent-2": agent_b}
    secrets = {ag: agents[ag].pick_number() for ag in ("Agent-1", "Agent-2")}
    print(f"(Hidden picks committed.)")

    lies_used = {"Agent-1": False, "Agent-2": False}
    guess_count = {"Agent-1": 0, "Agent-2": 0}
    response_count = {"Agent-1": 0, "Agent-2": 0}

    def step(curr, is_tie):
        opp = "Agent-2" if curr == "Agent-1" else "Agent-1"
        state_g = {
            "your_number": secrets[curr], "your_lie_used": lies_used[curr],
            "your_response_count": response_count[curr],
            "turn": guess_count[curr] + guess_count[opp] + 1,
            "you_started": curr == starter, "is_tie_attempt": is_tie,
        }
        g = agents[curr].guess(state_g)
        guess_count[curr] += 1
        if not isinstance(g, int) or isinstance(g, bool):
            print(f"{curr} illegal guess; turn lost.")
            return None, "lost_turn"
        state_r = {
            "your_number": secrets[opp], "your_lie_used": lies_used[opp],
            "your_response_count": response_count[opp],
            "turn": guess_count[curr] + guess_count[opp],
            "you_started": opp == starter, "is_tie_attempt": is_tie,
        }
        r = agents[opp].respond(state_r, g)
        response_count[opp] += 1
        if r not in VALID_RESPONSES:
            print(f"{opp} invalid response; forfeit.")
            return curr, "respond_invalid"
        truth = compute_truth(secrets[opp], g)
        is_lie = r != truth
        if is_lie:
            if lies_used[opp]:
                print(f"{opp} second lie; forfeit.")
                return curr, "second_lie"
            if response_count[opp] > MAX_RESPONSES_FOR_LIE:
                print(f"{opp} late lie on response {response_count[opp]}; forfeit.")
                return curr, "late_lie"
            lies_used[opp] = True
            print(f"  ({opp} lied — lie now used)")
        print(f"  {curr} guesses {g} -> {opp} says '{r}' (truth={truth})")
        if r == "Correct" and truth == "Correct":
            return curr, "win"
        return None, "continue"

    turn = 0
    current = starter
    non_starter = "Agent-2" if starter == "Agent-1" else "Agent-1"
    while turn < MAX_TURNS:
        turn += 1
        winner, status = step(current, False)
        if status in ("respond_invalid", "second_lie", "late_lie"):
            return winner
        if status == "win":
            if current == starter and turn < MAX_TURNS:
                turn += 1
                tw, ts = step(non_starter, True)
                if ts == "win":
                    print("DRAW (tie-attempt succeeded).")
                    return "DRAW"
                if ts in ("respond_invalid", "second_lie", "late_lie"):
                    return tw
                return starter
            return current
        current = "Agent-2" if current == "Agent-1" else "Agent-1"
    print("Turn cap reached.")
    return "DRAW"


if __name__ == "__main__":
    human = HumanAgent("Agent-1")
    bot = RandomAgent("Agent-2")
    starter = "Agent-1"
    print("LieOnce — Human (Agent-1) vs Random Bot (Agent-2). Human starts.")
    winner = play(starter, human, bot)
    print(f"Winner: {winner}")
'''


def build_game_code(
    agent1_code: str,
    agent2_code: str,
    extra_imports: str,
    num_games: int,
    move_timeout: float,
    agent1_name: str = "Agent-1",
    agent2_name: str = "Agent-2",
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
        f'AGENT1_NAME = "{agent1_name}"\n'
        f'AGENT2_NAME = "{agent2_name}"\n'
    )
    return "\n\n".join([
        header,
        GAME_ENGINE_CODE,
        extra_imports,
        agent1_code,
        agent2_code,
        MATCH_RUNNER_CODE,
    ])


def load_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "games" / "A2-LieOnce.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()


def find_model_folder(pattern: str) -> str | None:
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


def run_match(
    game_code: str, match_id: int, run_ids: tuple[int, int], timeout: int = MATCH_TIME_LIMIT
) -> dict:
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"lie_once_match_{match_id}_{temp_id}.py"
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

        match = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", result.stdout)
        stats_block = ""
        if "--- MATCH STATISTICS ---" in result.stdout:
            stats_block = result.stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if match:
            wins_match = re.search(r"WINS:Agent-1=(\d+),Agent-2=(\d+)", result.stdout)
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


async def run_match_async(
    game_code: str, match_id: int, run_ids: tuple[int, int]
) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    parser = argparse.ArgumentParser(description="Run LieOnce matches between stored AI agents")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4]")
    parser.add_argument("--humanvsbot", action="store_true", help="Play interactively against a random bot")
    parser.add_argument(
        "--update-scoreboard", action="store_true",
        help="Write results to scoreboard (default: off; enabled by matchmaker)",
    )
    parser.add_argument(
        "--parallel", type=int, default=4,
        help="Number of matches to run in parallel",
    )
    args = parser.parse_args()

    if args.humanvsbot:
        temp_file = os.path.join(tempfile.gettempdir(), f"lie_once_human_{uuid.uuid4().hex[:8]}.py")
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
    print("LIEONCE MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Model 1: {folder1} ({len(runs1)} runs)")
    print(f"Model 2: {folder2} ({len(runs2)} runs)")
    print(f"Total Matches: {num_matches}")
    print("=" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    match_tasks = []
    semaphore = asyncio.Semaphore(args.parallel)

    for i in range(num_matches):
        run1 = runs1[i]
        run2 = runs2[i]
        code1, imp1 = load_stored_agent(folder1, GAME_NAME, run1, 1, "LieOnceAgent")
        code2, imp2 = load_stored_agent(folder2, GAME_NAME, run2, 2, "LieOnceAgent")
        if not code1 or not code2:
            print(f"  FAILED to prepare match {i+1}: Could not load agent code.")
            continue

        extra_imports = consolidate_imports(imp1, imp2)
        game_code = build_game_code(
            agent1_code=code1,
            agent2_code=code2,
            extra_imports=extra_imports,
            num_games=NUM_GAMES_PER_MATCH,
            move_timeout=MOVE_TIME_LIMIT,
            agent1_name=f"{folder1}:{run1}",
            agent2_name=f"{folder2}:{run2}",
        )

        async def sem_task(gc, mid, rids):
            async with semaphore:
                return await run_match_async(gc, mid, rids)

        match_tasks.append(sem_task(game_code, i + 1, (run1, run2)))

    if not match_tasks:
        print("No valid matches to run.")
        return

    match_word = "match" if len(match_tasks) == 1 else "matches"
    parallel_info = f" (up to {args.parallel} in parallel)" if len(match_tasks) > 1 else ""
    print(f"\nRunning {len(match_tasks)} {match_word}{parallel_info}...")
    results = await asyncio.gather(*match_tasks)

    total_pts1, total_pts2 = 0, 0
    for res in sorted(results, key=lambda x: x["match_id"]):
        m_id = res["match_id"]
        r1, r2 = runs1[m_id - 1], runs2[m_id - 1]
        log_f = RESULTS_DIR / f"{ts}_{folder1}:{r1}_vs_{folder2}:{r2}_match.txt"

        if res["success"]:
            p1, p2 = res["agent1_points"], res["agent2_points"]
            total_pts1 += p1
            total_pts2 += p2
            print(f"  Match {m_id} ({folder1}:{r1} vs {folder2}:{r2}): {p1} - {p2}")
            s1, s2 = res["agent1_score"], res["agent2_score"]
            print(f"MINI:{folder1}:{r1}={p1},{s1}|{folder2}:{r2}={p2},{s2}")
            status = "Result:\n"
            status += f"{folder1}:{res['agent1_run_id']} : Pts: {res['agent1_points']} - Score: {res['agent1_score']}\n"
            status += f"{folder2}:{res['agent2_run_id']} : Pts: {res['agent2_points']} - Score: {res['agent2_score']}\n"
            if res.get("log"):
                status += f"\n{res['log'].strip()}\n"
        else:
            print(f"  Match {m_id} ({folder1}:{r1} vs {folder2}:{r2}): FAILED - {res.get('error')}")
            status = f"FAILED: {res.get('error', 'Unknown')}\n"
            if res.get("log"):
                status += f"\nLog:\n{res['log']}\n"

        with open(log_f, "w") as f:
            f.write("Match Contenders:\n")
            f.write(f"{folder1}:{r1}\n")
            f.write(f"{folder2}:{r2}\n\n")
            f.write(f"{status}\n")
            f.write("-" * 60 + "\n")

        if res["success"] and args.update_scoreboard:
            agent1_key = f"{folder1}:{res['agent1_run_id']}"
            update_scoreboard(
                SCOREBOARD_PATH, agent1_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=res["agent1_wins"],
                losses=res["agent2_wins"],
                draws=res["draws"],
                score=res["agent1_score"],
                points=res["agent1_points"],
            )
            agent2_key = f"{folder2}:{res['agent2_run_id']}"
            update_scoreboard(
                SCOREBOARD_PATH, agent2_key,
                games_played=NUM_GAMES_PER_MATCH,
                wins=res["agent2_wins"],
                losses=res["agent1_wins"],
                draws=res["draws"],
                score=res["agent2_score"],
                points=res["agent2_points"],
            )

    print("\nFINAL RESULTS:")
    print(f"  {folder1}: {total_pts1}")
    print(f"  {folder2}: {total_pts2}")
    print(f"\nLogs saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    asyncio.run(main_async())
