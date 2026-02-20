"""
Round-robin tournament scheduler for competitive LLM agent matches.

Discovers all agents for a given game, generates cross-model fixtures
(filtering out same-model pairs), and executes them concurrently as
subprocesses delegated to the appropriate game match runner.
"""

import argparse
import asyncio
import itertools
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AGENTS_DIR = PROJECT_ROOT / "agents"

GAME_REGISTRY: dict[str, dict] = {
    "A1": {"name": "A1-Battleship", "script": "A1-battleship_match.py", "players": 2},
    "A2": {"name": "A2-TicTacToe", "script": "A2-tictactoe_match.py", "players": 2},
    "A3": {"name": "A3-Wizard", "script": "A3-wizard_match.py", "players": 6},
    "A4": {"name": "A4-WordFinder", "script": "A4-word_finder_match.py", "players": 2},
    "A5": {
        "name": "A5-Connect4RandomStart",
        "script": "A5-connect4_match.py",
        "players": 2,
    },
    "A6": {
        "name": "A6-WordMatrixGame",
        "script": "A6-word_matrix_match.py",
        "players": 2,
    },
    "A7": {"name": "A7-TwoByEightChess", "script": "A7-twobyeight_chess_match.py", "players": 2},
    "A8": {
        "name": "A8-SurroundMorris",
        "script": "A8-surround_morris_match.py",
        "players": 2,
    },
}




# ---------------------------------------------------------------------------
# Agent discovery
# ---------------------------------------------------------------------------


def discover_agents(game_name: str) -> dict[str, list[int]]:
    """Scan agents/*/ for files matching {game_name}_{run}.py.

    Returns mapping of model folder names to sorted run IDs.
    """
    pattern = re.compile(rf"^{re.escape(game_name)}_(\d+)\.py$")
    agents: dict[str, list[int]] = {}

    for model_dir in sorted(AGENTS_DIR.iterdir()):
        if not model_dir.is_dir():
            continue
        runs = []
        for f in model_dir.iterdir():
            m = pattern.match(f.name)
            if m:
                runs.append(int(m.group(1)))
        if runs:
            agents[model_dir.name] = sorted(runs)

    return agents


# ---------------------------------------------------------------------------
# Fixture generation — 2-player
# ---------------------------------------------------------------------------


def generate_2p_fixtures(
    agents: dict[str, list[int]],
    same_opponent_match: int,
    new_models: list[str] | None = None,
) -> list[tuple[tuple[str, int], tuple[str, int]]]:
    """All cross-model agent pairs, repeated same_opponent_match times.

    When *new_models* is given, only pairs where at least one side belongs
    to one of those model folders are produced (incremental tournament).
    """
    flat = [(folder, run) for folder, runs in agents.items() for run in runs]
    pairs = [
        (a, b)
        for a, b in itertools.combinations(flat, 2)
        if a[0] != b[0]
    ]
    if new_models:
        nm_set = set(new_models)
        pairs = [
            (a, b) for a, b in pairs
            if a[0] in nm_set or b[0] in nm_set
        ]
    fixtures = pairs * same_opponent_match
    random.shuffle(fixtures)
    return fixtures


# ---------------------------------------------------------------------------
# Fixture generation — 6-player (A3 Wizard)
# ---------------------------------------------------------------------------


def generate_6p_fixtures(
    agents: dict[str, list[int]],
    same_opponent_match: int,
    new_models: list[str] | None = None,
) -> list[list[tuple[str, int]]]:
    """Greedy pairwise-coverage groups of 6 agents from different models.

    When *new_models* is given, only cross-model pairs involving those models
    need coverage, and every generated group is guaranteed to contain at least
    one of them.
    """
    flat = [(folder, run) for folder, runs in agents.items() for run in runs]
    folders = list(agents.keys())
    num_models = len(folders)
    group_size = min(num_models, 6)

    # Build target coverage for every cross-model pair
    cross_pairs = [
        (a, b) for a, b in itertools.combinations(flat, 2) if a[0] != b[0]
    ]
    if new_models:
        nm_set = set(new_models)
        cross_pairs = [
            (a, b) for a, b in cross_pairs
            if a[0] in nm_set or b[0] in nm_set
        ]
    coverage: Counter[tuple[tuple[str, int], tuple[str, int]]] = Counter()
    target = same_opponent_match

    def under_covered() -> int:
        return sum(1 for p in cross_pairs if coverage[p] < target)

    fixtures: list[list[tuple[str, int]]] = []
    stall = 0
    max_stall = 200

    while under_covered() > 0:
        best_group: list[tuple[str, int]] | None = None
        best_score = 0

        for _ in range(1000):
            if group_size > num_models:
                break
            if new_models:
                # Force one of the new models into the group
                focus_model = random.choice(new_models)
                other_folders = [f for f in folders if f != focus_model]
                
                remaining_slots = group_size - 1
                if remaining_slots > len(other_folders):
                    remaining_slots = len(other_folders)
                
                chosen_others = random.sample(other_folders, remaining_slots)
                group = [(focus_model, random.choice(agents[focus_model]))]
                group.extend((m, random.choice(agents[m])) for m in chosen_others)
            else:
                chosen_models = random.sample(folders, group_size)
                group = [(m, random.choice(agents[m])) for m in chosen_models]

            score = 0
            for a, b in itertools.combinations(group, 2):
                pair = (a, b) if a < b else (b, a)
                if coverage[pair] < target:
                    score += 1

            if score > best_score:
                best_score = score
                best_group = group

        if best_group is None or best_score == 0:
            stall += 1
            if stall >= max_stall:
                break
            continue

        stall = 0
        for a, b in itertools.combinations(best_group, 2):
            pair = (a, b) if a < b else (b, a)
            coverage[pair] += 1
        fixtures.append(best_group)

    random.shuffle(fixtures)
    return fixtures


# ---------------------------------------------------------------------------
# Match execution
# ---------------------------------------------------------------------------


async def run_match_subprocess(
    cmd: list[str],
    match_idx: int,
    total: int,
    label: str,
    semaphore: asyncio.Semaphore,
    start_time: float,
    env_vars: dict[str, str] | None = None,
) -> dict:
    """Run a single match runner subprocess with concurrency control."""
    import os
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    async with semaphore:
        elapsed = time.time() - start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        pct = (match_idx / total) * 100
        print(
            f"[{match_idx:>5}/{total}] {pct:5.1f}% | {elapsed_str} elapsed | {label}",
            flush=True,
        )

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                stdout, stderr = await proc.communicate()
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                print(f"FAILED (timeout): {label}", flush=True)
                return {"success": False, "label": label, "error": "timeout", "stdout": ""}

            success = proc.returncode == 0
            if success:
                print(f"FINISHED: {label}", flush=True)
            else:
                print(f"FAILED: {label}", flush=True)

            return {
                "success": success,
                "label": label,
                "error": stderr.decode(errors="replace")[:300] if not success else None,
                "stdout": stdout.decode(errors="replace"),
            }
        except Exception as e:
            print(f"ERROR: {label} - {e}", flush=True)
            return {"success": False, "label": label, "error": str(e)[:300], "stdout": ""}


# ---------------------------------------------------------------------------
# Agent health verification
# ---------------------------------------------------------------------------

_BROAD_EXCEPT_TYPES = {"Exception", "BaseException"}


def _find_broad_except_in_make_move(source: str) -> list[str]:
    """Detect top-level broad exception handlers inside make_move methods.

    A broad handler (except Exception / BaseException / bare except) at the
    top level of make_move will silently swallow MoveTimeoutException raised
    by signal.alarm, preventing the game engine from enforcing time limits.

    Returns a list of human-readable violation descriptions.
    """
    import ast

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # syntax errors are reported separately

    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != "make_move":
            continue

        # Only inspect direct children (top-level statements in the body)
        for stmt in node.body:
            if not isinstance(stmt, ast.Try):
                continue
            for handler in stmt.handlers:
                if handler.type is None:
                    violations.append(
                        f"line {handler.lineno}: bare 'except:' in make_move"
                    )
                elif (
                    isinstance(handler.type, ast.Name)
                    and handler.type.id in _BROAD_EXCEPT_TYPES
                ):
                    violations.append(
                        f"line {handler.lineno}: "
                        f"'except {handler.type.id}' in make_move"
                    )
                elif isinstance(handler.type, ast.Tuple):
                    for elt in handler.type.elts:
                        if (
                            isinstance(elt, ast.Name)
                            and elt.id in _BROAD_EXCEPT_TYPES
                        ):
                            violations.append(
                                f"line {handler.lineno}: "
                                f"'except (..., {elt.id}, ...)' in make_move"
                            )
                            break

    return violations


def verify_agent_syntax(game_name: str, agents: dict[str, list[int]]) -> bool:
    """Run all health checks on discovered agents.

    Checks performed:
      1. Syntax validity (ast.parse)
      2. Broad exception handlers in make_move (swallow MoveTimeoutException)

    Returns True if all agents pass every check, False otherwise.
    """
    import ast

    print("Running agent health checks...", flush=True)

    syntax_errors: list[str] = []
    broad_except_errors: list[str] = []
    agent_count = 0

    for model_name, runs in agents.items():
        for run in runs:
            agent_count += 1
            filename = f"{game_name}_{run}.py"
            file_path = AGENTS_DIR / model_name / filename

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                ast.parse(source)
            except SyntaxError as e:
                syntax_errors.append(f"  - {model_name}/{filename}: {e}")
                continue
            except Exception as e:
                syntax_errors.append(f"  - {model_name}/{filename}: {e}")
                continue

            # Passed syntax — check for prohibited broad except in make_move
            for violation in _find_broad_except_in_make_move(source):
                broad_except_errors.append(
                    f"  - {model_name}/{filename}: {violation}"
                )

    passed = True

    if syntax_errors:
        print("Syntax errors:")
        for err in syntax_errors:
            print(err)
        passed = False

    if broad_except_errors:
        print(
            "Broad exception handlers in make_move "
            "(will swallow MoveTimeoutException):"
        )
        for err in broad_except_errors:
            print(err)
        passed = False

    if passed:
        print(f"All {agent_count} agents passed health checks.")

    return passed


async def run_tournament(
    game_id: str,
    same_opponent_match: int,
    workers: int,
    dry_run: bool,
    new_models: list[str] | None = None,
    health_check: bool = False,
    random16: bool = False,
) -> None:
    game = GAME_REGISTRY[game_id]
    game_name = game["name"]
    players = game["players"]
    match_script = SCRIPT_DIR / game["script"]

    if not match_script.exists():
        print(f"ERROR: Match script not found: {match_script}")
        sys.exit(1)

    agents = discover_agents(game_name)
    if not agents:
        print(f"ERROR: No agents found for {game_name} in {AGENTS_DIR}")
        sys.exit(1)

    if health_check:
        if not verify_agent_syntax(game_name, agents):
            sys.exit(1)

    if new_models:
        missing = [m for m in new_models if m not in agents]
        if missing:
            print(f"ERROR: --new-model model(s) not found: {', '.join(missing)}")
            print(f"  Available models: {', '.join(sorted(agents.keys()))}")
            sys.exit(1)

    total_agents = sum(len(runs) for runs in agents.values())
    num_models = len(agents)

    if num_models < 2:
        print(f"ERROR: Need 2+ models for cross-model pairings, found {num_models}")
        sys.exit(1)

    if players == 6 and num_models < 6:
        print(f"ERROR: Need 6+ models for 6-player games, found {num_models}")
        sys.exit(1)

    # Generate fixtures
    mode_label = f" [incremental: {', '.join(new_models)}]" if new_models else ""

    if players == 2:
        fixtures_2p = generate_2p_fixtures(agents, same_opponent_match, new_models)
        if random16 and len(fixtures_2p) > 16:
            fixtures_2p = random.sample(fixtures_2p, 16)
        total_matches = len(fixtures_2p)
        # Compute unique pairings for display
        flat_agents = [(f, r) for f, rs in agents.items() for r in rs]
        all_pairs = [
            (a, b)
            for a, b in itertools.combinations(flat_agents, 2)
            if a[0] != b[0]
        ]
        if new_models:
            nm_set = set(new_models)
            all_pairs = [
                (a, b) for a, b in all_pairs
                if a[0] in nm_set or b[0] in nm_set
            ]
        unique_pairs = len(all_pairs)
        print(f"\nMATCHMAKER - {game_name}{mode_label}")
        print(f"Agents: {total_agents} ({num_models} models)")
        print(
            f"Fixture: {total_matches} matches "
            f"({unique_pairs} pairings x {same_opponent_match} same_opponent_match)"
        )
        print(f"Workers: {workers}")
    else:
        fixtures_6p = generate_6p_fixtures(agents, same_opponent_match, new_models)
        if random16 and len(fixtures_6p) > 16:
            fixtures_6p = random.sample(fixtures_6p, 16)
        total_matches = len(fixtures_6p)
        print(f"\nMATCHMAKER - {game_name}{mode_label}")
        print(f"Agents: {total_agents} ({num_models} models)")
        print(f"Fixture: {total_matches} matches (6-player groups, greedy coverage)")
        print(f"Workers: {workers}")

    if dry_run:
        print("\n--- DRY RUN (no matches executed) ---")
        print(f"Total Matches: {total_matches}")
        return

    # Build subprocess commands
    commands: list[tuple[list[str], str]] = []

    if players == 2:
        for a, b in fixtures_2p:
            cmd = [
                sys.executable,
                str(match_script),
                "--agent",
                f"{a[0]}:{a[1]}",
                f"{b[0]}:{b[1]}",
                "--update-scoreboard",
            ]
            label = f"{a[0]}:{a[1]} vs {b[0]}:{b[1]}"
            commands.append((cmd, label))
    else:
        for group in fixtures_6p:
            cmd = [sys.executable, str(match_script), "--agent"]
            cmd.extend(f"{f}:{r}" for f, r in group)
            cmd.append("--update-scoreboard")
            label = " vs ".join(f"{f}:{r}" for f, r in group)
            commands.append((cmd, label))

    semaphore = asyncio.Semaphore(workers)
    start_time = time.time()

    tasks = [
        run_match_subprocess(cmd, i + 1, total_matches, label, semaphore, start_time)
        for i, (cmd, label) in enumerate(commands)
    ]

    # Handle KeyboardInterrupt gracefully
    results = []
    try:
        results = await asyncio.gather(*tasks)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\nInterrupted — cancelling remaining matches...")
        for t in tasks:
            if isinstance(t, asyncio.Task) and not t.done():
                t.cancel()

    # Summary
    succeeded = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))
    duration = time.time() - start_time
    duration_str = time.strftime("%H:%M:%S", time.gmtime(duration))

    print(f"\nCOMPLETE")
    print(f"  Succeeded: {succeeded} | Failed: {failed}")
    print(f"  Duration: {duration_str}")

    if failed:
        print(f"\nFailed matches:")
        for r in results:
            if not r.get("success"):
                err = r.get("error", "unknown")
                print(f"  - {r['label']}: {err}")


async def run_a3_tournament(
    game_id: str,
    workers: int,
    dry_run: bool,
    health_check: bool = False,
) -> None:
    import os
    import math

    game = GAME_REGISTRY.get(game_id)
    if not game:
        print(f"ERROR: Unknown game_id {game_id}")
        sys.exit(1)

    game_name = game["name"]
    match_script = SCRIPT_DIR / game["script"]

    if not match_script.exists():
        print(f"ERROR: Match script not found: {match_script}")
        sys.exit(1)

    agents = discover_agents(game_name)
    if not agents:
        print(f"ERROR: No agents found for {game_name} in {AGENTS_DIR}")
        sys.exit(1)

    if health_check:
        if not verify_agent_syntax(game_name, agents):
            sys.exit(1)

    # Validate agent counts: Exactly 2 per model.
    invalid_models = [m for m, rs in agents.items() if len(rs) != 2]
    if invalid_models:
        print(f"ERROR: A3 requires exactly 2 agents per model. Invalid models: {invalid_models}")
        sys.exit(1)

    models = sorted(agents.keys())
    num_models = len(models)

    # Validate models count is divisible by 3 to form 6-person pods.
    if num_models % 3 != 0 or num_models == 0:
        print(f"ERROR: A3 requires number of models to be a multiple of 3 (for 6-player games). Found {num_models}.")
        sys.exit(1)

    print(f"\nMATCHMAKER A3 - PHASE 1: Qualifiers")
    print(f"Models: {num_models} (Total Agents: {num_models * 2})")

    # Group into chunks of 3 models
    random.shuffle(models)
    groups = [models[i : i + 3] for i in range(0, num_models, 3)]
    
    commands_p1: list[tuple[list[str], str, list[tuple[str, int]]]] = []
    for g in groups:
        # Each group has 3 models. 2 agents per model = 6 players.
        cmd = [sys.executable, str(match_script), "--agent"]
        match_agents = []
        for m in g:
            match_agents.extend([(m, agents[m][0]), (m, agents[m][1])])
            cmd.extend([f"{m}:{agents[m][0]}", f"{m}:{agents[m][1]}"])
        # We do NOT run --update-scoreboard for Phase 1 as these are qualifiers 
        # and do not reflect final standings across the board.
        
        label = " vs ".join(g)
        commands_p1.append((cmd, label, match_agents))
        
    num_p1 = len(commands_p1)
    print(f"Fixture: {num_p1} matches (Qualifiers)")
    
    if dry_run:
        print("\n--- DRY RUN (Phase 1) ---")
        for cmd_data in commands_p1:
            print(f"  {cmd_data[1]}")
        
        # Expected Combinatorics Phase 2
        combinations_count = math.comb(num_models, 6)
        print(f"\n--- DRY RUN (Phase 2) ---")
        print(f"Expected Matches: {combinations_count} combinations of winning agents")
        return

    # Execute Phase 1
    # NUM_OF_GAMES_IN_A_MATCH is typically an env var. We bump it x10 for A3 Phase 1.
    base_games = int(os.environ.get("NUM_OF_GAMES_IN_A_MATCH", "50"))
    env_vars_p1 = {"NUM_OF_GAMES_IN_A_MATCH": str(base_games * 10)}
    print(f"Config: {env_vars_p1['NUM_OF_GAMES_IN_A_MATCH']} games per Match (Phase 1 only)")

    semaphore = asyncio.Semaphore(workers)
    start_time = time.time()
    
    tasks = [
        run_match_subprocess(cmd_data[0], i + 1, num_p1, cmd_data[1], semaphore, start_time, env_vars=env_vars_p1)
        for i, cmd_data in enumerate(commands_p1)
    ]
    
    try:
        results = await asyncio.gather(*tasks)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\nInterrupted Phase 1 — cancelling remaining matches...")
        for t in tasks:
            if isinstance(t, asyncio.Task) and not t.done():
                t.cancel()
        sys.exit(1)

    print(f"\n--- PHASE 1 RESULTS ---")
    for r in results:
        if not r.get("success"):
            print(f"\nFailed Qualifier: {r['label']}\n{r.get('error')}")
            sys.exit(1)
        # Print output so user can read the standard scoreboard stats for this match
        print(f"\n{'-'*60}\nQualifier Group: {r['label']}\n{'-'*60}")
        print(r.get("stdout", ""))

    print(f"\n--- PHASE 1 SELECTION ---")
    # Automatic selection based on points
    model_results: dict[str, list[tuple[int, float]]] = {m: [] for m in models}
    
    for i, r in enumerate(results):
        stdout = r.get("stdout", "")
        # RESULT:Agent-1=45.0,Agent-2=25.0,...
        m_res = re.search(r"RESULT:([^ \n]+)", stdout)
        if m_res:
            parts = m_res.group(1).split(",")
            match_agents = commands_p1[i][2]
            for p in parts:
                if "=" not in p: continue
                agent_label, points_str = p.split("=")
                agent_idx = int(agent_label.split("-")[1]) - 1
                points = float(points_str)
                model_name, run_id = match_agents[agent_idx]
                model_results[model_name].append((run_id, points))

    chosen_agents: list[tuple[str, int]] = []
    print(f"{'Model':<40} | {'Run A (Pts)':<15} | {'Run B (Pts)':<15} | {'Winner'}")
    print("-" * 85)
    
    for m in sorted(models):
        res = sorted(model_results[m]) # [ (run1, pts1), (run2, pts2) ]
        if len(res) != 2:
            # Fallback if parsing failed for some reason
            print(f"WARNING: Could not parse results for {m}. Defaulting to first run.")
            winner_run = agents[m][0]
            pts_a, pts_b = 0.0, 0.0
        else:
            run_a, pts_a = res[0]
            run_b, pts_b = res[1]
            if pts_a >= pts_b:
                winner_run = run_a
            else:
                winner_run = run_b
        
        chosen_agents.append((m, winner_run))
        a_str = f"{res[0][0]} ({res[0][1]:.1f})" if len(res)>0 else "N/A"
        b_str = f"{res[1][0]} ({res[1][1]:.1f})" if len(res)>1 else "N/A"
        print(f"{m:<40} | {a_str:<15} | {b_str:<15} | {winner_run}")
                
    # Phase 2
    combinations = list(itertools.combinations(chosen_agents, 6))
    num_p2 = len(combinations)
    print(f"\nMATCHMAKER A3 - PHASE 2: Main Event")
    print(f"Selected Agents: {len(chosen_agents)}")
    print(f"Combinations: {num_p2} matches")
    
    while True:
        proceed = input("Start Phase 2? [y/N]: ").strip().lower()
        if proceed in ("y", "yes"):
            break
        elif proceed in ("n", "no", ""):
            print("Aborting.")
            sys.exit(0)

    # Build P2 commands
    commands_p2: list[tuple[list[str], str]] = []
    for count_idx, group in enumerate(combinations):
        cmd = [sys.executable, str(match_script), "--agent"]
        cmd.extend(f"{f}:{r}" for f, r in group)
        cmd.append("--update-scoreboard")
        # Keep label short since there are 134k 
        label = f"Match_{count_idx+1}"
        commands_p2.append((cmd, label))

    random.shuffle(commands_p2) # disperse model clustering evenly
    semaphore_p2 = asyncio.Semaphore(workers)
    start_time_p2 = time.time()
    
    # Phase 2: Hardcode to 1 game per match
    env_vars_p2 = {"NUM_OF_GAMES_IN_A_MATCH": "1"}
    print(f"Config: 1 game per Match (Phase 2 only)")
    
    tasks_p2 = [
        run_match_subprocess(cmd, i + 1, num_p2, label, semaphore_p2, start_time_p2, env_vars=env_vars_p2)
        for i, (cmd, label) in enumerate(commands_p2)
    ]
    
    try:
        results_p2 = await asyncio.gather(*tasks_p2)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\nInterrupted Phase 2 — cancelling remaining matches...")
        for t in tasks_p2:
            if isinstance(t, asyncio.Task) and not t.done():
                t.cancel()
        sys.exit(1)
        
    succeeded = sum(1 for r in results_p2 if r.get("success"))
    failed = sum(1 for r in results_p2 if not r.get("success"))
    duration = time.time() - start_time_p2
    duration_str = time.strftime("%H:%M:%S", time.gmtime(duration))

    print(f"\nPHASE 2 COMPLETE")
    print(f"  Succeeded: {succeeded} | Failed: {failed}")
    print(f"  Duration: {duration_str}")

    if failed:
        with open("a3_failed_matches.log", "w") as f:
            for r in results_p2:
                if not r.get("success"):
                    err = r.get("error", "unknown")
                    f.write(f"{r['label']}: {err}\n")
        print("Failed matches written to a3_failed_matches.log")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Round-robin tournament scheduler for LLM agent matches"
    )
    parser.add_argument(
        "--game",
        required=True,
        choices=list(GAME_REGISTRY.keys()),
        help="Game ID (e.g. A1, A2, ..., A8)",
    )
    parser.add_argument(
        "--same_opponent_match",
        type=int,
        default=4,
        help="Times each cross-model agent pair faces each other (default: 1)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=24,
        help="Max concurrent match subprocesses (default: 16)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print fixture list without executing matches",
    )
    parser.add_argument(
        "--new-model",
        type=str,
        default=None,
        help="Only generate matches involving these model folders (comma-separated)",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run syntax verification on all agents before execution",
    )
    parser.add_argument(
        "--random16",
        action="store_true",
        help="Randomly select 16 matches and run them",
    )
    args = parser.parse_args()

    new_models = None
    if args.new_model:
        new_models = [m.strip() for m in args.new_model.split(",") if m.strip()]

    if args.game == "A3":
        asyncio.run(
            run_a3_tournament(
                args.game,
                args.workers,
                args.dry_run,
                args.health,
            )
        )
    else:
        asyncio.run(
            run_tournament(
                args.game,
                args.same_opponent_match,
                args.workers,
                args.dry_run,
                new_models,
                args.health,
                args.random16,
            )
        )


if __name__ == "__main__":
    main()
