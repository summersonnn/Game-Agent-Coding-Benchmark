"""Regression tests for standalone backgammon scripts (standard library only)."""

import ast
import contextlib
import copy
import io
from pathlib import Path
import random
import signal
import subprocess
import sys
import types
import unittest
from unittest.mock import mock_open, patch


RUNNER_PATH = Path(__file__).resolve().parents[1] / "game_scripts/A4-backgammon_match.py"


def load_script_definitions():
    # Exercise the actual embedded scripts and builders without importing the
    # outer CLI's API client or requiring its third-party dependencies.
    tree = ast.parse(RUNNER_PATH.read_text())
    names = {"GAME_ENGINE_CODE", "MATCH_RUNNER_CODE", "HUMAN_PLAY_CODE", "GAME_TIME_LIMIT"}
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


SCRIPTS = load_script_definitions()
ENGINE = {}
exec(SCRIPTS.GAME_ENGINE_CODE, ENGINE)
Game = ENGINE["BackgammonGame"]


def position(points, bar=0, off=0, color="W"):
    game = Game()
    game.board = [points.get(p, 0) for p in range(24)]
    game.bar = {"W": bar, "B": 0}
    game.borne_off = {"W": off, "B": 0}
    if color == "B":
        game.board = [-v for v in reversed(game.board)]
        game.bar = {"W": 0, "B": bar}
        game.borne_off = {"W": 0, "B": off}
    return game


def snapshot(game):
    return copy.deepcopy((game.board, game.bar, game.borne_off, game.current_player, game.turn_count))


class LegalTurnTests(unittest.TestCase):
    def assert_legal_turn(self, game, color, dice, expected=None):
        before = snapshot(game)
        original_dice = list(dice)
        target = game.max_dice_usable(color, dice)
        if expected is not None:
            self.assertEqual(target, expected)
        sequence = game.get_random_legal_turn(color, dice)
        self.assertEqual(len(sequence), target)
        self.assertEqual(snapshot(game), before)
        self.assertEqual(dice, original_dice)
        replay = copy.deepcopy(game)
        ok, message, _ = replay.validate_and_apply_turn(color, dice, sequence)
        self.assertTrue(ok, (sequence, message))
        for player, sign in (("W", 1), ("B", -1)):
            total = sum(abs(v) for v in replay.board if v * sign > 0)
            total += replay.bar[player] + replay.borne_off[player]
            self.assertEqual(total, 15)
        return sequence

    def test_opening_all_rolls_and_colors(self):
        for color in ("W", "B"):
            for d1 in range(1, 7):
                for d2 in range(d1, 7):
                    dice = [d1] * 4 if d1 == d2 else [d1, d2]
                    with self.subTest(color=color, dice=dice):
                        self.assert_legal_turn(Game(), color, dice, len(dice))

    def test_bar_doubles_hits_and_bearing_off(self):
        cases = [
            ({1: 13, 23: -2, 18: -13}, 2, 0, [1, 2], 1),
            ({1: 14, 23: -2, 22: -2, 18: -11}, 1, 0, [1, 2], 0),
            ({1: 10, 22: -15}, 5, 0, [1, 1, 1, 1], 4),
            ({5: 1, 18: -15}, 0, 14, [2, 2, 2, 2], 3),
            ({0: 1, 3: 1, 18: -15}, 0, 13, [4, 6], 2),
            ({0: 14, 6: 1, 18: -15}, 0, 0, [1, 6], 2),
            ({0: 1, 18: -15}, 0, 14, [6, 6, 6, 6], 1),
            ({8: 15, 5: -1, 18: -14}, 0, 0, [3, 1], 2),
        ]
        for color in ("W", "B"):
            for points, bar, off, dice, target in cases:
                with self.subTest(color=color, points=points, dice=dice):
                    self.assert_legal_turn(position(points, bar, off, color), color, dice, target)

    def test_backtracks_from_hit_that_strands_second_die(self):
        game = position({1: 14, 23: -1, 21: -2, 18: -12}, bar=1)
        # Try bar->23 first. It hits, but leaves no playable move for die 2.
        # A full turn must instead enter at 22, then move 1->0 with die 1.
        with patch.object(ENGINE["random"], "shuffle", lambda moves: None):
            sequence = self.assert_legal_turn(game, "W", [1, 2], 2)
        self.assertEqual(sequence, [("bar", 22), (1, 0)])
        self.assertEqual(game.bar["B"], 0)

    def test_invalid_endpoints_roll_back_legal_prefix(self):
        invalid = [("bar", "off"), (-1, "off"), (24, "off"), (8, 24), (float("inf"), 1)]
        for bad_move in invalid:
            game = position({8: 15, 5: -1, 18: -14})
            before = snapshot(game)
            with self.subTest(move=bad_move):
                ok, _, hits = game.validate_and_apply_turn("W", [3, 1], [(8, 5), bad_move])
                self.assertFalse(ok)
                self.assertEqual(hits, 0)
                self.assertEqual(snapshot(game), before)


class RunnerFallbackTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(signal.signal, signal.SIGALRM, signal.getsignal(signal.SIGALRM))
        self.addCleanup(random.setstate, random.getstate())

    def run_one_turn(self, behavior, blocked=False, winning=False):
        namespace = {"__name__": "backgammon_test", "random": random, "signal": signal, "sys": sys,
                     "MAX_TURNS_PER_GAME": 1, "MOVE_TIMEOUT": 1,
                     "GAME_TIME_LIMIT": SCRIPTS.GAME_TIME_LIMIT,
                     "AGENT1_INFO": "test-1", "AGENT2_INFO": "test-2"}
        exec(SCRIPTS.GAME_ENGINE_CODE + SCRIPTS.MATCH_RUNNER_CODE, namespace)
        base = namespace["BackgammonGame"]
        games = []
        fallback_starts = []
        applied = []
        initial = (position({1: 14, 23: -2, 22: -2, 18: -11}, bar=1)
                   if blocked else position({8: 15, 5: -1, 18: -14}))
        if winning:
            initial = position({0: 1, 18: -15}, off=14)

        class RecordingGame(base):
            def __init__(self):
                super().__init__()
                self.board = list(initial.board)
                self.bar = dict(initial.bar)
                self.borne_off = dict(initial.borne_off)
                games.append(self)

            def get_random_legal_turn(self, *args, **kwargs):
                fallback_starts.append(snapshot(self))
                return super().get_random_legal_turn(*args, **kwargs)

            def validate_and_apply_turn(self, color, dice, sequence, **kwargs):
                result = super().validate_and_apply_turn(color, dice, sequence, **kwargs)
                if result[0]:
                    applied.append((copy.deepcopy(sequence), result[2]))
                return result

        class Agent:
            def __init__(self, name, color):
                pass

            def make_move(self, state, feedback):
                if behavior == "crash":
                    raise RuntimeError("broken agent")
                if behavior == "timeout":
                    signal.raise_signal(signal.SIGALRM)
                if behavior == "valid":
                    return [(8, 5), (5, 4)]
                return behavior

        namespace["BackgammonGame"] = RecordingGame
        stats = {name: dict.fromkeys(("wins", "losses", "draws", "other_crash", "make_move_crash",
                                     "timeout", "invalid", "hits", "dice_used"), 0)
                 for name in ("Agent-1", "Agent-2")}
        dice = [1, 2] if blocked else [3, 1]
        if winning:
            dice = [6, 6]
        output = io.StringIO()
        with patch.object(random, "choice", return_value="W"), \
                patch.object(random, "randint", side_effect=dice), contextlib.redirect_stdout(output):
            namespace["play_game"](1, {"Agent-1": 0.0, "Agent-2": 0.0}, stats,
                                   {"W": "Agent-1", "B": "Agent-2"},
                                   {"Agent-1": Agent, "Agent-2": Agent})
        self.assertEqual(signal.alarm(0), 0)
        return games[0], initial, stats, fallback_starts, applied, output.getvalue()

    def test_failures_apply_complete_fallback_and_keep_original_error(self):
        cases = [("crash", "make_move_crash"), ("timeout", "timeout"), (None, "invalid"),
                 ([], "invalid"), ([(8, 5)] * 3, "invalid"),
                 ([(8, 5), ("bar", "off")], "invalid")]
        for behavior, counter in cases:
            with self.subTest(behavior=behavior):
                game, initial, stats, starts, applied, output = self.run_one_turn(behavior)
                self.assertEqual(len(starts), 1)
                self.assertEqual(starts[0][:3], snapshot(initial)[:3])
                self.assertEqual(len(applied), 1)
                sequence, hits = applied[0]
                self.assertEqual(len(sequence), 2)
                expected = copy.deepcopy(initial)
                self.assertTrue(expected.validate_and_apply_turn("W", [3, 1], sequence)[0])
                self.assertEqual(snapshot(game)[:3], snapshot(expected)[:3])
                self.assertEqual(stats["Agent-1"][counter], 1)
                self.assertEqual(sum(stats["Agent-1"][key] for key in
                                     ("invalid", "timeout", "make_move_crash", "other_crash")), 1)
                self.assertEqual(stats["Agent-1"]["dice_used"], 2)
                self.assertEqual(stats["Agent-1"]["hits"], hits)
                self.assertEqual(game.turn_count, 1)
                self.assertIn("random legal fallback", output)

    def test_fallback_can_win_and_award_gammon_points(self):
        game, _, stats, starts, _, output = self.run_one_turn(None, winning=True)
        self.assertEqual(len(starts), 1)
        self.assertEqual(game.borne_off["W"], 15)
        self.assertEqual(stats["Agent-1"]["wins"], 1)
        self.assertEqual(stats["Agent-1"]["dice_used"], 1)
        self.assertEqual(stats["Agent-1"]["draws"], 0)
        self.assertIn("wins by Gammon (+2)", output)

    def test_valid_turn_and_blocked_pass_do_not_trigger_fallback(self):
        for blocked in (False, True):
            with self.subTest(blocked=blocked):
                _, _, stats, starts, applied, _ = self.run_one_turn("valid", blocked=blocked)
                self.assertEqual(starts, [])
                self.assertEqual(len(applied), 0 if blocked else 1)
                self.assertEqual(stats["Agent-1"]["dice_used"], 0 if blocked else 2)
                self.assertEqual(stats["Agent-1"]["hits"], 0 if blocked else 1)
                self.assertEqual(sum(stats["Agent-1"][key] for key in
                                     ("invalid", "timeout", "make_move_crash")), 0)

    def test_broken_agents_complete_standalone_game(self):
        agent1 = '''class BackgammonAgent_1:
    def __init__(self, name, color): pass
    def make_move(self, state, feedback): raise RuntimeError("broken")
'''
        agent2 = '''class BackgammonAgent_2:
    def __init__(self, name, color): pass
    def make_move(self, state, feedback): return []
'''
        script = SCRIPTS.build_game_code(agent1, agent2, "random.seed(12345)",
                                         1, 300, 1, 1, "crash", "invalid")
        result = subprocess.run([sys.executable, "-c", script], capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GAMES_PLAYED:1", result.stdout)
        self.assertRegex(result.stdout, r"wins by (Single|Gammon)")
        self.assertNotIn("Draw by turn limit", result.stdout)
        stats = [ast.literal_eval(line.split("=", 1)[1])
                 for line in result.stdout.splitlines() if line.startswith("STATS:")]
        self.assertGreater(stats[0]["make_move_crash"], 0)
        self.assertGreater(stats[1]["invalid"], 0)
        self.assertTrue(all(s["dice_used"] > 0 for s in stats))

    def test_human_mode_random_bot_uses_complete_turn(self):
        namespace = {"__name__": "backgammon_test"}
        exec(SCRIPTS.build_human_game_code("humanvsbot"), namespace)
        game = position({1: 14, 23: -1, 21: -2, 18: -12}, bar=1)
        state = game.get_state_for_agent("W", [1, 2], {"W": 0, "B": 0}, 1, 2,
                                         game.get_legal_sub_moves("W", [1, 2]))
        sequence = namespace["RandomAgent"]("bot", "W").make_move(state)
        self.assertEqual(len(sequence), 2)
        self.assertTrue(game.validate_and_apply_turn("W", [1, 2], sequence)[0])

    def test_human_mode_agent_failures_also_play_fallback(self):
        for body in ("return []", "raise RuntimeError('broken')", "signal.raise_signal(signal.SIGALRM)"):
            with self.subTest(body=body):
                agent = f'''class BackgammonAgent_1:
    def __init__(self, name, color): pass
    def make_move(self, state, feedback): {body}
'''
                namespace = {"__name__": "backgammon_test"}
                exec(SCRIPTS.build_human_game_code("humanvsagent", agent), namespace)
                namespace.update(MAX_TURNS_PER_GAME=1, MAX_GAMES_PER_MATCH=1)
                base = namespace["BackgammonGame"]
                games = []

                class RecordingGame(base):
                    def __init__(self):
                        super().__init__()
                        games.append(self)

                namespace["BackgammonGame"] = RecordingGame
                output = io.StringIO()
                with patch.object(random, "random", return_value=1), \
                        patch.object(random, "choice", return_value="W"), \
                        patch.object(random, "randint", side_effect=[1, 2]), \
                        patch("builtins.open", mock_open()), contextlib.redirect_stdout(output):
                    namespace["play_human_match"]()
                self.assertIn("Playing a random legal turn", output.getvalue())
                self.assertNotEqual(games[0].board, Game().board)
                self.assertEqual(games[0].turn_count, 1)
                self.assertEqual(signal.alarm(0), 0)


if __name__ == "__main__":
    unittest.main()
