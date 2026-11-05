"""Regression tests for the A7 Mancala match runner (standard library only)."""

import ast
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "game_scripts/A7-mancala_match.py"
PROMPT_PATH = ROOT / "games/A7-Mancala.txt"


def load_script_definitions():
    # Exercise the actual embedded scripts and builders without importing the
    # outer CLI's API client or requiring its third-party dependencies.
    tree = ast.parse(RUNNER_PATH.read_text())
    names = {"GAME_ENGINE_CODE", "MATCH_RUNNER_CODE", "HUMAN_PLAY_CODE", "FORFEIT_SCORE",
             "GAME_TIME_LIMIT"}
    builders = {"build_game_code", "build_human_game_code"}
    nodes = [
        node for node in tree.body
        if (isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in names for t in node.targets))
        or (isinstance(node, ast.FunctionDef) and node.name in builders)
    ]
    namespace = {"MOVE_TIME_LIMIT": 1.0}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(RUNNER_PATH), "exec"), namespace)
    return types.SimpleNamespace(**namespace)


def load_reference_apply_move():
    """The apply_move function shown to agents in the game prompt."""
    blocks = re.findall(r"```python\n(.*?)```", PROMPT_PATH.read_text(), re.DOTALL)
    source = next(b for b in blocks if "def apply_move" in b)
    namespace = {}
    exec(source, namespace)
    return namespace["apply_move"]


SCRIPTS = load_script_definitions()
ENGINE = {}
exec(SCRIPTS.GAME_ENGINE_CODE, ENGINE)
Game = ENGINE["MancalaGame"]
reference_apply_move = load_reference_apply_move()


def game_with(board, current=0):
    game = Game()
    game.board = list(board)
    game.current = current
    return game


class EngineRuleTests(unittest.TestCase):
    def test_initial_position(self):
        game = Game()
        self.assertEqual(game.board, [4] * 6 + [0] + [4] * 6 + [0])
        self.assertEqual(game.current, 0)
        for p in (0, 1):
            state = game.state_for(p)
            self.assertEqual(state["board"], [4] * 6 + [0] + [4] * 6 + [0])
            self.assertEqual(state["legal_moves"], [0, 1, 2, 3, 4, 5])
            self.assertEqual(state["player"], ("P1", "P2")[p])
            self.assertEqual(state["move_number"], 0)

    def test_p2_sees_rotated_board(self):
        board = list(range(14))
        game = game_with(board)
        self.assertEqual(game.relative_board(0), board)
        self.assertEqual(game.relative_board(1), board[7:] + board[:7])

    def test_last_stone_in_own_mancala_gives_extra_turn(self):
        for p in (0, 1):
            game = Game()
            game.current = p
            info = game.apply_move(2, p)  # 4 stones from pocket 2 -> 3, 4, 5, store
            self.assertTrue(info["extra_turn"])
            self.assertEqual(game.current, p)
            self.assertEqual(game.board[game.store_index(p)], 1)
            self.assertEqual(game.move_number, 1)

    def test_turn_passes_without_extra_turn(self):
        game = Game()
        info = game.apply_move(0, 0)  # 4 stones -> pockets 1-4
        self.assertFalse(info["extra_turn"])
        self.assertEqual(game.current, 1)
        self.assertEqual(game.board, [0, 5, 5, 5, 5, 4, 0, 4, 4, 4, 4, 4, 4, 0])

    def test_opponent_mancala_is_skipped(self):
        # P1 sows 10 from pocket 5: 6, 7..12, skip 13, 0, 1, 2.
        board = [1, 1, 1, 0, 0, 10, 0, 1, 1, 1, 1, 1, 1, 7]
        game = game_with(board)
        game.apply_move(5, 0)
        self.assertEqual(game.board, [2, 2, 2, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 7])
        # P2 sows 10 from its pocket 5 (index 12): 13, 0..5, skip 6, 7, 8, 9.
        board = [1, 1, 1, 1, 1, 1, 9, 1, 1, 1, 0, 0, 10, 0]
        game = game_with(board, current=1)
        game.apply_move(5, 1)
        self.assertEqual(game.board, [2, 2, 2, 2, 2, 2, 9, 2, 2, 2, 0, 0, 0, 1])

    def test_capture_takes_last_stone_and_opposite_pocket(self):
        # P1 pocket 0 has 2 stones -> 1, 2. Pocket 2 was empty; across is 10.
        board = [2, 3, 0, 1, 1, 1, 0, 1, 1, 1, 6, 1, 1, 0]
        game = game_with(board)
        info = game.apply_move(0, 0)
        self.assertEqual(info["captured"], 7)
        self.assertEqual(info["captured_across"], 6)
        self.assertEqual(game.board, [0, 4, 0, 1, 1, 1, 7, 1, 1, 1, 0, 1, 1, 0])
        self.assertEqual(game.current, 1)

    def test_capture_with_empty_opposite_pocket_still_banks_last_stone(self):
        board = [1, 0, 0, 2, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0]
        game = game_with(board)
        info = game.apply_move(0, 0)  # last stone in pocket 1, across (11) is empty
        self.assertEqual(info["captured"], 1)
        self.assertEqual(info["captured_across"], 0)
        self.assertEqual(game.board[1], 0)
        self.assertEqual(game.board[6], 1)

    def test_thirteen_stones_capture_in_the_starting_pocket(self):
        board = [0, 0, 13, 0, 0, 0, 0, 1, 1, 1, 2, 1, 1, 0]
        game = game_with(board)
        info = game.apply_move(2, 0)
        # Lap of 13 lands back in pocket 2; across from it is pocket 10 (2+1=3).
        self.assertEqual(info["captured"], 4)
        self.assertEqual(game.board[2], 0)
        self.assertEqual(game.board[10], 0)
        self.assertEqual(game.board[13], 0)
        self.assertEqual(sum(game.board), 13 + 7)

    def test_empty_pocket_on_opponent_side_does_not_capture(self):
        board = [0, 0, 0, 0, 1, 2, 0, 0, 5, 5, 5, 5, 5, 0]
        game = game_with(board)
        info = game.apply_move(5, 0)  # 2 stones -> store, pocket 7 (empty, opponent's)
        self.assertEqual(info["captured"], 0)
        self.assertEqual(game.board[7], 1)
        self.assertEqual(game.current, 1)

    def test_game_ends_when_mover_row_empties_even_on_extra_turn(self):
        board = [0, 0, 0, 0, 0, 1, 18, 3, 3, 3, 3, 3, 3, 11]
        game = game_with(board)
        info = game.apply_move(5, 0)
        self.assertTrue(info["game_over"])
        self.assertFalse(info["extra_turn"])
        self.assertEqual(game.current, 0)
        self.assertEqual(info["swept"], [0, 18])
        self.assertEqual(game.board[6], 19)
        self.assertEqual(game.board[13], 29)
        self.assertEqual(game.side_stones(0) + game.side_stones(1), 0)

    def test_capture_that_empties_opponent_row_ends_game(self):
        # Last stone lands in empty pocket 1, across (11) holds the only P2 stones.
        board = [1, 0, 0, 0, 0, 3, 10, 0, 0, 0, 0, 5, 0, 29]
        game = game_with(board)
        info = game.apply_move(0, 0)
        self.assertEqual(info["captured"], 6)
        self.assertTrue(info["game_over"])
        self.assertEqual(info["swept"], [3, 0])
        self.assertEqual(game.board[6], 19)
        self.assertEqual(game.board[13], 29)

    def test_validate_move(self):
        game = game_with([0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0])
        self.assertEqual(game.validate_move(1, 0), (True, ""))
        for bad in (0, -1, 6, True, 1.0, "1", None, [1]):
            ok, _ = game.validate_move(bad, 0)
            self.assertFalse(ok, bad)
        self.assertFalse(game.validate_move(5, 1)[0])  # P2 pocket 5 = index 12, empty
        self.assertTrue(game.validate_move(0, 1)[0])

    def test_random_games_terminate_and_conserve_stones(self):
        rng = random.Random(7)
        for _ in range(500):
            game = Game()
            for _ in range(1000):
                p = game.current
                info = game.apply_move(rng.choice(game.legal_moves(p)), p)
                self.assertEqual(sum(game.board), 48)
                if info["game_over"]:
                    break
            else:
                self.fail("game did not end")
            self.assertEqual(game.board[6] + game.board[13], 48)


class PromptReferenceTests(unittest.TestCase):
    def test_reference_matches_engine_on_random_positions(self):
        rng = random.Random(11)
        checked = 0
        for _ in range(400):
            game = Game()
            while True:
                p = game.current
                pocket = rng.choice(game.legal_moves(p))
                before = game.relative_board(p)
                expected_board, expected_extra, expected_over = reference_apply_move(before, pocket)
                info = game.apply_move(pocket, p)
                self.assertEqual(game.relative_board(p), expected_board)
                self.assertEqual(info["extra_turn"], expected_extra)
                self.assertEqual(info["game_over"], expected_over)
                checked += 1
                if info["game_over"]:
                    break
        self.assertGreater(checked, 5000)

    def test_reference_handles_long_wraps(self):
        rng = random.Random(3)
        for _ in range(2000):
            stones = [rng.randint(0, 20) for _ in range(12)]
            if not any(stones[:6]) or not any(stones[6:]):
                continue
            absolute = stones[:6] + [rng.randint(0, 10)] + stones[6:] + [rng.randint(0, 10)]
            for p in (0, 1):
                game = game_with(absolute, current=p)
                for pocket in game.legal_moves(p):
                    trial = game_with(absolute, current=p)
                    expected = reference_apply_move(trial.relative_board(p), pocket)
                    info = trial.apply_move(pocket, p)
                    self.assertEqual(
                        (trial.relative_board(p), info["extra_turn"], info["game_over"]),
                        expected,
                    )


AGENT_RANDOM = """
class MancalaAgent_{idx}:
    def __init__(self, name, player):
        self.name = name
        self.player = player

    def make_move(self, state):
        return random.choice(state["legal_moves"])
"""

AGENT_GREEDY = """
class MancalaAgent_{idx}:
    def __init__(self, name, player):
        self.name = name

    def make_move(self, state):
        board = state["board"]
        for pocket in reversed(state["legal_moves"]):
            if board[pocket] == 6 - pocket:
                return pocket
        return state["legal_moves"][-1]
"""

AGENT_BAD = """
class MancalaAgent_{idx}:
    def __init__(self, name, player):
        self.calls = 0

    def make_move(self, state):
        self.calls += 1
        if self.calls == 1:
            raise ValueError("boom")
        if self.calls == 2:
            return "3"
        if self.calls == 3:
            return 9
        if self.calls == 4:
            empty = [i for i in range(6) if state["board"][i] == 0]
            return empty[0] if empty else 6
        if self.calls == 5:
            time.sleep(1.5)
        return state["legal_moves"][0]
"""

AGENT_INIT_CRASH = """
class MancalaAgent_{idx}:
    def __init__(self, name, player):
        raise RuntimeError("init failed")

    def make_move(self, state):
        return state["legal_moves"][0]
"""


def run_inner_match(agent1, agent2, num_games, game_time_limit=60):
    code = SCRIPTS.build_game_code(
        agent1.format(idx=1), agent2.format(idx=2), "", num_games, 1.0,
        "model-a:1", "model-b:1", game_time_limit,
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path], capture_output=True, text=True, timeout=120,
        )
    finally:
        os.remove(path)
    return proc


def parse_totals(stdout):
    def pair(key):
        m = re.search(rf"{key}:Agent-1=(-?[\d.]+),Agent-2=(-?[\d.]+)", stdout)
        return float(m.group(1)), float(m.group(2))
    draws = int(re.search(r"DRAWS:(\d+)", stdout).group(1))
    stats = {}
    for agent in ("Agent-1", "Agent-2"):
        line = re.search(rf"STATS:{agent}=(\{{.*\}})", stdout).group(1)
        stats[agent] = ast.literal_eval(line)
    return pair("RESULT"), pair("SCORE"), pair("WINS"), draws, stats


class MatchRunnerTests(unittest.TestCase):
    def test_full_match_output_is_consistent(self):
        proc = run_inner_match(AGENT_GREEDY, AGENT_RANDOM, num_games=6)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        (pts1, pts2), (sc1, sc2), (w1, w2), draws, stats = parse_totals(proc.stdout)
        self.assertEqual(w1 + w2 + draws, 6)
        self.assertEqual(pts1, 3 * w1 + draws)
        self.assertEqual(pts2, 3 * w2 + draws)
        self.assertEqual(sc1, -sc2)
        self.assertEqual(proc.stdout.count("Final Position:"), 6)
        self.assertIn("BOARD: ", proc.stdout)
        self.assertIn("--- MATCH STATISTICS ---", proc.stdout)
        # Seats alternate: Agent-1 is P1 in odd games, P2 in even games.
        self.assertIn("Game 1\nAgent-1: model-a:1 (P1)\nAgent-2: model-b:1 (P2)", proc.stdout)
        self.assertIn("Game 2\nAgent-1: model-a:1 (P2)\nAgent-2: model-b:1 (P1)", proc.stdout)
        for agent in ("Agent-1", "Agent-2"):
            self.assertEqual(stats[agent]["crash"], 0)
            self.assertEqual(stats[agent]["invalid"], 0)

    def test_random_opening_is_shared_by_each_pair_of_games(self):
        proc = run_inner_match(AGENT_GREEDY, AGENT_RANDOM, num_games=40)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        games = proc.stdout.split("\nGame ")[1:]
        self.assertEqual(len(games), 40)
        openings = []
        for text in games:
            m = re.search(r"Random opening: P1 pocket (\d) \(4 stones\)( -> extra turn)?\n(.*)\n", text)
            pocket = int(m.group(1))
            openings.append(pocket)
            # Pocket 2 ends in P1's Mancala, so P1's agent moves next.
            next_seat = "(P1)" if pocket == 2 else "(P2)"
            self.assertEqual(m.group(2) is not None, pocket == 2)
            self.assertIn(next_seat, m.group(3))
        self.assertEqual(openings[0::2], openings[1::2])
        self.assertGreater(len(set(openings)), 1)
        self.assertIn("Total Moves:", proc.stdout)

    def test_errors_fall_back_to_random_and_are_counted(self):
        proc = run_inner_match(AGENT_BAD, AGENT_RANDOM, num_games=1)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        _, _, (w1, w2), draws, stats = parse_totals(proc.stdout)
        self.assertEqual(w1 + w2 + draws, 1)
        bad = stats["Agent-1"]
        self.assertEqual(bad["make_move_crash"], 1)
        self.assertEqual(bad["invalid"], 3)
        self.assertEqual(bad["timeout"], 1)
        self.assertEqual(bad["crash"], 1)
        self.assertIn("Agent-1 (P1): CRASH 'boom'", proc.stdout)
        self.assertIn("INVALID not an int: '3'", proc.stdout)
        self.assertIn("INVALID pocket 9 out of range [0, 5]", proc.stdout)
        self.assertIn("Agent-1 (P1): TIMEOUT", proc.stdout)
        self.assertIn("Agent-1 (P1): random pocket", proc.stdout)

    def test_init_crash_forfeits_with_max_score(self):
        proc = run_inner_match(AGENT_INIT_CRASH, AGENT_RANDOM, num_games=2)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        (pts1, pts2), (sc1, sc2), (w1, w2), draws, stats = parse_totals(proc.stdout)
        self.assertEqual((w1, w2, draws), (0, 2, 0))
        self.assertEqual((pts1, pts2), (0, 6))
        self.assertEqual((sc1, sc2), (-96, 96))
        self.assertEqual(stats["Agent-1"]["other_crash"], 2)

    def test_exhausted_game_time_limit_ends_games_as_draws(self):
        proc = run_inner_match(AGENT_RANDOM, AGENT_RANDOM, num_games=3, game_time_limit=0)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        (pts1, pts2), (sc1, sc2), (w1, w2), draws, _ = parse_totals(proc.stdout)
        self.assertEqual((w1, w2, draws), (0, 0, 3))
        self.assertEqual((pts1, pts2, sc1, sc2), (3, 3, 0, 0))
        self.assertIn("Time-limit Draws: 3", proc.stdout)


class HumanModeTests(unittest.TestCase):
    def test_human_vs_bot_plays_to_the_end(self):
        code = SCRIPTS.build_human_game_code("humanvsbot")
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            path = f.name
        try:
            proc = subprocess.run(
                [sys.executable, path], input="0\n1\n2\n3\n4\n5\n" * 200,
                capture_output=True, text=True, timeout=60,
            )
        finally:
            os.remove(path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("GAME OVER:", proc.stdout)

    def test_human_vs_agent_code_compiles(self):
        agent = AGENT_RANDOM.format(idx=1)
        code = SCRIPTS.build_human_game_code("humanvsagent", agent, "import random")
        compile(code, "<human>", "exec")


if __name__ == "__main__":
    unittest.main()
