"""Regressions for game behavior and state promised to generated agents."""

import ast
import collections
import contextlib
import copy
import io
import os
from pathlib import Path
import random
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def runner_path(game_id):
    return next((ROOT / "game_scripts").glob(f"{game_id}-*_match.py"))


def definitions(game_id):
    """Load actual script builders without importing the CLI/API dependencies."""
    path = runner_path(game_id)
    names = {"GAME_CODE_TEMPLATE", "GAME_ENGINE_CODE", "MATCH_RUNNER_CODE",
             "HUMAN_GAME_CODE", "GAME_TIME_LIMIT", "FORFEIT_SCORE",
             "NUM_PLAYERS", "NUM_ROUNDS"}
    nodes = [node for node in ast.parse(path.read_text()).body
             if (isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id in names for t in node.targets))
             or (isinstance(node, ast.FunctionDef) and node.name == "build_game_code")]
    ns = {"MOVE_TIME_LIMIT": 1, "NUM_GAMES_PER_MATCH": 1,
          "MAX_TURNS_PER_GAME": 100, "BOARD_SIZE": 8, "SHIPS": [5, 4, 3]}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), ns)
    return ns


def runtime(game_id, max_turns=100):
    build = definitions(game_id)["build_game_code"]
    if game_id == "A1":
        source = build("", "", "", num_games=1)
    elif game_id == "A3":
        source = build([""] * 6, "", 1, 1, ["test"] * 6)
    elif game_id == "A4":
        source = build("", "", "", 1, 300, 5, 30, "test-1", "test-2")
    elif game_id == "A6":
        source = build("", "", "", 1, 1,
                       str(ROOT / "game_scripts/words_small.txt"),
                       max_turns_per_game=max_turns)
    elif game_id == "A7":
        source = build("", "", "", 1, 1, "test-1", "test-2")
    elif game_id == "A8":
        source = build("", "", "", 1, 1, max_turns, "test-1", "test-2")
    else:
        source = build("", "", "", 1, 1)
    ns = {"__name__": "prompt_alignment_test"}
    exec(source, ns)
    return ns


def stats(players=2):
    return {f"Agent-{i}": collections.defaultdict(int) for i in range(1, players + 1)}


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()) as output:
        result = fn(*args)
    return result, output.getvalue()


class IdleAgent:
    def __init__(self, name, *args):
        self.name = name

    def make_move(self, *args):
        return None

    def pick_number(self):
        return 50


class BattleshipValidationTests(unittest.TestCase):
    def test_non_integer_targets_use_fallback_and_finish_game(self):
        for coordinate in (0.5, float("inf"), "0", True, None):
            with self.subTest(coordinate=coordinate):
                ns = runtime("A1")

                class Agent(IdleAgent):
                    def make_move(self, state, feedback):
                        if state["phase"] == "placement":
                            return {"ship_length": state["ships_to_place"][0],
                                    "start": (state["ships_placed"], 0),
                                    "orientation": "horizontal"}
                        return {"target": (coordinate, 0)}

                ns.update(BattleshipAgent_1=Agent, BattleshipAgent_2=Agent)
                match_stats = stats()
                with patch("random.randint", return_value=0):
                    result, _ = quiet(ns["play_game"], 1, match_stats)
                self.assertEqual(result, ("DRAW", 0))
                self.assertEqual(sum(s["invalid"] for s in match_stats.values()), 128)

    def test_non_integer_ship_coordinates_are_invalid(self):
        ns = runtime("A1")
        board = [["O"] * 8 for _ in range(8)]
        for coordinate in (0.5, float("inf"), "0", True):
            with self.subTest(coordinate=coordinate):
                result = ns["validate_ship_placement"](
                    {"ship_length": 5, "start": (coordinate, 0),
                     "orientation": "horizontal"}, board, 8, 5)
                self.assertFalse(result[0])


class LieOnceStateTests(unittest.TestCase):
    def agents(self, seen):
        class Agent(IdleAgent):
            def guess(self, state):
                return 50 if state["turn"] >= 3 else 1

            def respond(self, state, guess):
                seen.append((self.name, state.copy()))
                return "Correct" if guess == 50 else "Up"
        return Agent

    def assert_feedback(self, seen):
        regular = next(state for name, state in seen
                       if name == "Agent-1" and state["turn"] == 2)
        tie = next(state for name, state in seen
                   if name == "Agent-1" and state["is_tie_attempt"])
        self.assertEqual(regular["last_response"], "Up")
        self.assertEqual(tie["last_response"], "Correct")

    def test_responder_gets_previous_feedback_in_normal_and_tie_turns(self):
        ns = runtime("A2")
        seen = []
        agent = self.agents(seen)
        ns.update(LieOnceAgent_1=agent, LieOnceAgent_2=agent)
        result, _ = quiet(ns["play_game"], 1, stats())
        self.assertEqual(result, "DRAW")
        self.assert_feedback(seen)

    def test_human_mode_uses_the_same_feedback_contract(self):
        ns = {"__name__": "prompt_alignment_test"}
        exec(definitions("A2")["HUMAN_GAME_CODE"], ns)
        seen = []
        agent = self.agents(seen)
        result, _ = quiet(ns["play"], "Agent-1", agent("Agent-1"), agent("Agent-2"))
        self.assertEqual(result, "DRAW")
        self.assert_feedback(seen)


class WizardStateTests(unittest.TestCase):
    def test_new_round_clears_old_trick_and_reports_actual_leader(self):
        ns = runtime("A3")
        game = ns["WizardGame"](6)
        game.start_round(1)
        game.current_trick = [(i, ns["Card"]("jester")) for i in range(6)]
        game.finish_trick()
        game.start_round(2)
        bidding = game.get_game_state(1, "bid")
        self.assertEqual(bidding["current_trick"], [])
        self.assertIsNone(bidding["trick_leader"])
        self.assertEqual(bidding["played_tricks"], [])
        game.start_trick()
        game.validate_and_play(1, game.hands[1][0])
        playing = game.get_game_state(2, "play")
        self.assertEqual(playing["trick_leader"], 1)
        self.assertEqual(playing["current_trick"][0][0], 1)


class BackgammonValidationTests(unittest.TestCase):
    def test_non_integer_endpoints_reject_whole_turn_and_rollback(self):
        ns = runtime("A4")
        for coordinate in (5.9, "5", True, float("inf"), None):
            with self.subTest(coordinate=coordinate):
                game = ns["BackgammonGame"]()
                before = copy.deepcopy((game.board, game.bar, game.borne_off))
                ok, _, hits = game.validate_and_apply_turn(
                    "W", [2, 1], [(5, 3), (coordinate, 4)])
                self.assertFalse(ok)
                self.assertEqual(hits, 0)
                self.assertEqual((game.board, game.bar, game.borne_off), before)


class WordMatrixTests(unittest.TestCase):
    def test_bad_path_coordinates_cost_ten_and_end_turn_without_crash(self):
        for coordinate in (0.5, float("inf"), "0", True):
            with self.subTest(coordinate=coordinate):
                ns = runtime("A6", max_turns=1)
                ns["load_words"] = lambda: {"noon"}

                class Agent(IdleAgent):
                    def make_move(self, *args):
                        return ([(coordinate, 0), (0, 1)], "noon")

                ns.update(WordMatrixAgent_1=Agent, WordMatrixAgent_2=Agent)
                match_stats = stats()
                result, _ = quiet(ns["play_game"], 1, match_stats)
                self.assertEqual(result, "Agent-2")
                self.assertEqual(match_stats["Agent-1"]["invalid"], 1)
                self.assertEqual(match_stats["Agent-1"]["score"], -10)
                self.assertEqual(match_stats["Agent-2"]["score"], 10)

    def test_forfeit_margin_scales_with_actual_turn_cap(self):
        class BrokenAgent(IdleAgent):
            def __init__(self, *args):
                raise RuntimeError("initialization failure")

        for cap in (1, 3, 100, 140):
            with self.subTest(cap=cap):
                ns = runtime("A6", max_turns=cap)
                ns.update(load_words=lambda: {"noon"},
                          WordMatrixAgent_1=BrokenAgent, WordMatrixAgent_2=IdleAgent)
                match_stats = stats()
                result, _ = quiet(ns["play_game"], 1, match_stats)
                self.assertEqual(result, "Agent-2")
                self.assertEqual(match_stats["Agent-2"]["score"], 10 * cap + 160)
                self.assertEqual(match_stats["Agent-1"]["score"], -(10 * cap + 160))

    def noon_game(self):
        ns = runtime("A6")
        base_game = ns["WordMatrixGame"]

        class Game(base_game):
            def __init__(self, words):
                super().__init__(words)
                self.board[0][:2] = ["n", "o"]

        class Agent(IdleAgent):
            def make_move(self, board, *args):
                path = [(0, 0), (0, 1)]
                return (path if board[0][0] == "n" else path[::-1], "noon")

        class PassAgent(IdleAgent):
            def make_move(self, *args):
                return "PASS"

        ns.update(load_words=lambda: {"noon"}, WordMatrixGame=Game,
                  WordMatrixAgent_1=Agent, WordMatrixAgent_2=PassAgent)
        return ns

    def test_forfeit_margin_exceeds_legal_repeated_noon_score(self):
        ns = self.noon_game()
        match_stats = stats()
        quiet(ns["play_game"], 1, match_stats)
        self.assertEqual(match_stats["Agent-1"]["score"], 500)
        self.assertGreater(ns["FORFEIT_SCORE"], 500)

    def test_documented_clock_draw_discards_existing_lead(self):
        ns = self.noon_game()
        ns["_runner_monotonic"] = Mock(side_effect=[0, 0, 16, 16])
        match_stats = stats()
        result, output = quiet(ns["play_game"], 1, match_stats)
        self.assertEqual(result, "DRAW")
        self.assertIn("Scores: Agent-1=10 Agent-2=0", output)
        for agent in match_stats.values():
            self.assertEqual(agent["points"], 1)
            self.assertEqual(agent["score"], 0)


class MorrisTests(unittest.TestCase):
    def test_turn_cap_is_independent_of_word_matrix_configuration(self):
        path = runner_path("A8")
        nodes = [node for node in ast.parse(path.read_text()).body
                 if isinstance(node, ast.Try)
                 and any(isinstance(item, ast.Assign)
                         and any(isinstance(t, ast.Name) and t.id == "MAX_TURNS_PER_GAME"
                                 for t in item.targets) for item in node.body)]
        source = compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec")
        for value, expected in ((None, 200), ("17", 17), ("bad", 200), ("0", 200), ("-1", 200)):
            with self.subTest(value=value):
                env = {"MAX_TURNS_PER_GAME": "100"}
                if value is not None:
                    env["A8_MAX_TURNS_PER_GAME"] = value
                ns = {"os": os}
                with patch.dict(os.environ, env, clear=True):
                    exec(source, ns)
                self.assertEqual(ns["MAX_TURNS_PER_GAME"], expected)
                game_ns = runtime("A8", max_turns=expected)
                game = game_ns["SurroundMorrisGame"]()
                game.phase = "movement"
                game.move_count = expected - 1
                self.assertFalse(game.check_turn_limit()[0])
                game.move_count += 1
                self.assertTrue(game.check_turn_limit()[0])

    def test_non_integer_moves_use_random_fallback_in_both_phases(self):
        for coordinate in (0.9, float("inf"), "0", True):
            with self.subTest(coordinate=coordinate):
                ns = runtime("A8", max_turns=1)
                ns["random"] = random.Random(0)

                class Agent(IdleAgent):
                    def make_move(self, state, feedback):
                        if state["phase"] == "placement":
                            return coordinate
                        return (coordinate, 1)

                ns.update(SurroundMorrisAgent_1=Agent, SurroundMorrisAgent_2=Agent)
                match_stats = stats()
                result, _ = quiet(ns["play_game"], 1, match_stats)
                self.assertIn(result, ("Agent-1", "Agent-2", "DRAW"))
                self.assertEqual(sum(s["invalid"] for s in match_stats.values()), 15)


class GameClockTests(unittest.TestCase):
    def test_expired_clock_has_documented_outcome_in_every_game(self):
        classes = {"A1": "BattleshipAgent", "A2": "LieOnceAgent", "A3": "WizardAgent",
                   "A4": "BackgammonAgent", "A5": "Connect4Agent", "A6": "WordMatrixAgent",
                   "A7": "MancalaAgent", "A8": "SurroundMorrisAgent"}
        for game_id, class_name in classes.items():
            with self.subTest(game=game_id):
                ns = runtime(game_id)
                ns["GAME_TIME_LIMIT"] = 0
                ns["load_words"] = lambda: {"noon"}
                players = 6 if game_id == "A3" else 2
                for i in range(1, players + 1):
                    ns[f"{class_name}_{i}"] = IdleAgent
                match_stats = stats(players)
                if game_id == "A4":
                    points = {"Agent-1": 0.0, "Agent-2": 0.0}
                    args = (1, points, match_stats, {"W": "Agent-1", "B": "Agent-2"},
                            {"Agent-1": IdleAgent, "Agent-2": IdleAgent})
                    result, _ = quiet(ns["play_game"], *args)
                    self.assertEqual(result, ("DRAW", 0.5))
                    self.assertEqual(list(points.values()), [0.5, 0.5])
                else:
                    result, _ = quiet(ns["play_game"], 1, match_stats)
                    if game_id == "A1":
                        self.assertEqual(result, ("TIME_DRAW", 0))
                    elif game_id == "A3":
                        self.assertTrue(all(s["points"] == 2.5 and s["score"] == 0
                                            for s in match_stats.values()))
                    else:
                        self.assertEqual(result, "DRAW")
                        self.assertTrue(all(s["points"] == 1 and s["score"] == 0
                                            for s in match_stats.values()))


if __name__ == "__main__":
    unittest.main()
