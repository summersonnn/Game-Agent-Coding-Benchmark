"""Verify independent match counts and their propagation to match runners."""

import asyncio
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "utils"))
sys.path.insert(0, str(ROOT / "game_scripts"))

from game_config import games_per_match, wizard_phase_games_per_match


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MatchCountTests(unittest.TestCase):
    def test_defaults_and_legacy_setting_do_not_couple_games(self):
        with patch.dict(os.environ, {"NUM_OF_GAMES_IN_A_MATCH": "999"}, clear=True):
            self.assertEqual(
                [games_per_match(f"A{i}") for i in range(1, 9)],
                [20, 50, 24, 30, 10, 10, 12, 20],
            )

    def test_invalid_and_non_positive_counts_use_each_games_default(self):
        for value in ("", "bad", "0", "-1", "1.5"):
            with self.subTest(value=value), patch.dict(
                os.environ,
                {"A1_GAMES_PER_MATCH": value, "A5_GAMES_PER_MATCH": value},
                clear=True,
            ):
                self.assertEqual(games_per_match("A1"), 20)
                self.assertEqual(games_per_match("A5"), 10)

    def test_every_runner_uses_its_own_count_and_scales_its_timeout(self):
        settings = {f"A{i}_GAMES_PER_MATCH": str(i + 2) for i in range(1, 9)}
        settings["A4_MAX_GAMES_PER_MATCH"] = "9"
        settings["NUM_OF_GAMES_IN_A_MATCH"] = "999"
        with patch.dict(os.environ, settings, clear=True), \
                patch("dotenv.load_dotenv", return_value=False):
            for path in sorted((ROOT / "game_scripts").glob("A*_match.py")):
                with self.subTest(runner=path.name):
                    runner = load_module(path)
                    game_id = path.name[:2]
                    expected = 9 if game_id == "A4" else int(game_id[1]) + 2
                    actual = (runner.MAX_GAMES_PER_MATCH if game_id == "A4"
                              else runner.NUM_GAMES_PER_MATCH)
                    self.assertEqual(actual, expected)
                    self.assertEqual(runner.MATCH_TIME_LIMIT,
                                     runner.GAME_TIME_LIMIT * expected)
                    if game_id == "A4":
                        namespace = {"__name__": "human_cap_test"}
                        exec(runner.build_human_game_code("humanvsbot"), namespace)
                        self.assertEqual(namespace["MAX_GAMES_PER_MATCH"], 9)

    def test_enhancement_passes_only_the_selected_games_override(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch("dotenv.load_dotenv", return_value=False):
            enhancement = load_module(ROOT / "utils/try_enhancing_agents.py")

        for game_id, key, count, expected in (
            ("A1", "A1_GAMES_PER_MATCH", 7, 70),
            ("A5", "A5_GAMES_PER_MATCH", 3, 30),
            ("A4", "A4_MAX_GAMES_PER_MATCH", 9, 9),
        ):
            process = types.SimpleNamespace(
                returncode=0,
                communicate=AsyncMock(return_value=(b"RESULT:Agent-1=3,Agent-2=0", b"")),
            )
            create_process = AsyncMock(return_value=process)
            with self.subTest(game=game_id), \
                    patch.dict(os.environ, {key: str(count)}, clear=True), \
                    patch("asyncio.create_subprocess_exec", create_process), \
                    contextlib.redirect_stdout(io.StringIO()):
                result = asyncio.run(enhancement.run_enhancement_match(
                    game_id, "example-model", 1, 2, "test", asyncio.Semaphore(1),
                ))
                self.assertTrue(result["success"])
                self.assertEqual(create_process.call_args.kwargs["env"],
                                 {key: str(expected)})

    def test_wizard_phase_counts_are_independent(self):
        settings = {
            "A3_GAMES_PER_MATCH": "7",
            "A3_QUALIFIER_GAMES_PER_MATCH": "60",
            "A3_MAIN_EVENT_GAMES_PER_MATCH": "12",
        }
        with patch.dict(os.environ, settings, clear=True):
            self.assertEqual(games_per_match("A3"), 7)
            self.assertEqual(wizard_phase_games_per_match("qualifier"), 60)
            self.assertEqual(wizard_phase_games_per_match("main_event"), 12)
        with patch.dict(os.environ, {
            "A3_QUALIFIER_GAMES_PER_MATCH": "0",
            "A3_MAIN_EVENT_GAMES_PER_MATCH": "bad",
        }, clear=True):
            self.assertEqual(wizard_phase_games_per_match("qualifier"), 402)
            self.assertEqual(wizard_phase_games_per_match("main_event"), 6)

    def test_wizard_scheduler_passes_each_phase_count_to_its_runner(self):
        with patch("dotenv.load_dotenv", return_value=False):
            scheduler = load_module(ROOT / "game_scripts/matchmaker.py")
        agents = {f"model-{i}": [1, 2] for i in range(6)}
        result_line = "RESULT:" + ",".join(f"Agent-{i}={i}.0" for i in range(1, 7))
        run_match = AsyncMock(return_value={
            "success": True, "stdout": result_line, "label": "test table",
        })
        with patch.dict(os.environ, {
            "A3_GAMES_PER_MATCH": "7",
            "A3_QUALIFIER_GAMES_PER_MATCH": "60",
            "A3_MAIN_EVENT_GAMES_PER_MATCH": "12",
        }, clear=True), \
                patch.object(scheduler, "discover_agents", return_value=agents), \
                patch.object(scheduler, "run_match_subprocess", run_match), \
                contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(scheduler.run_a3_tournament("A3", 2, False, auto_yes=True))
        self.assertEqual(run_match.call_count, 3)
        for call in run_match.call_args_list[:2]:
            self.assertEqual(call.kwargs["env_vars"], {"A3_GAMES_PER_MATCH": "60"})
        self.assertEqual(run_match.call_args_list[2].kwargs["env_vars"],
                         {"A3_GAMES_PER_MATCH": "12"})

    def test_wizard_main_event_requires_six_models(self):
        with patch("dotenv.load_dotenv", return_value=False):
            scheduler = load_module(ROOT / "game_scripts/matchmaker.py")
        agents = {f"model-{i}": [1, 2] for i in range(5)}
        run_match = AsyncMock()
        with patch.object(scheduler, "discover_agents", return_value=agents), \
                patch.object(scheduler, "run_match_subprocess", run_match), \
                contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            asyncio.run(scheduler.run_a3_tournament("A3", 2, False, auto_yes=True))
        run_match.assert_not_called()


if __name__ == "__main__":
    unittest.main()
