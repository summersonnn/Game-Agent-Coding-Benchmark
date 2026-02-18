"""
Agent enhancement script. Generates a new agent per model/game combo, runs
same-model matches to compare against existing agents, and prunes the
worst-performing agent to keep the pool lean.

Architecture: fully pipelined. All API calls fire in parallel. As soon as
any single response arrives and the agent is saved, its matches start
immediately — even while other models are still in the populating phase.

Usage:
    uv run utils/try_enhancing_agents.py --model <substrings|all> --game <prefixes|all>
"""

import asyncio
import os
import re
import sys
import time
from datetime import datetime
from itertools import combinations
from pathlib import Path

import argparse
from dotenv import load_dotenv

# Add project root and utils to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "utils"))
sys.path.insert(0, str(PROJECT_ROOT / "game_scripts"))

from logging_config import setup_logging
from matchmaker import GAME_REGISTRY, discover_agents
from model_api import ModelAPI
from populate_agents import (
    extract_agent_code,
    get_next_run_ids,
    load_game_prompts,
    prompt_model,
    sanitize_model_name,
    MAX_WORKERS as POPULATE_MAX_WORKERS,
)

logger = setup_logging(__name__)

load_dotenv()

try:
    BASE_NUM_GAMES = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    BASE_NUM_GAMES = 100

ENHANCEMENT_MULTIPLIER = 10
MATCH_TIMEOUT = 900
MAX_MATCH_WORKERS = 24

AGENTS_DIR = PROJECT_ROOT / "agents"
SCRIPT_DIR = PROJECT_ROOT / "game_scripts"


# ---------------------------------------------------------------------------
# Model / game resolution
# ---------------------------------------------------------------------------


def resolve_models(api: ModelAPI, model_args: list[str]) -> list[str]:
    """Resolve --model arguments into full model names from models.txt."""
    if len(model_args) == 1 and model_args[0].lower() == "all":
        return api.models[:]

    selected: list[str] = []
    for query in model_args:
        if query.isdigit():
            idx = int(query)
            if 0 <= idx < len(api.all_models):
                selected.append(api.all_models[idx])
            else:
                print(f"WARNING: Model index {idx} out of range, skipping")
            continue

        matches = [m for m in api.all_models if query.lower() in m.lower()]
        if not matches:
            print(f"WARNING: No model matches substring '{query}', skipping")
            continue

        if len(matches) > 1:
            chosen = api.resolve_model_interactive(query, matches)
            if chosen:
                selected.append(chosen)
        else:
            selected.append(matches[0])

    return list(dict.fromkeys(selected))


def resolve_game_ids(game_arg: str) -> list[str]:
    """Resolve --game argument into validated game IDs, excluding 6-player games."""
    if game_arg.lower() == "all":
        return [
            gid for gid, info in GAME_REGISTRY.items()
            if info["players"] == 2
        ]

    requested = [g.strip().upper() for g in game_arg.split(",")]
    valid: list[str] = []
    for gid in requested:
        if gid not in GAME_REGISTRY:
            print(f"WARNING: Unknown game ID '{gid}', skipping")
            continue
        if GAME_REGISTRY[gid]["players"] != 2:
            print(
                f"WARNING: Game '{gid}' has {GAME_REGISTRY[gid]['players']} "
                f"players, skipping (only 2-player supported)"
            )
            continue
        valid.append(gid)

    return valid


# ---------------------------------------------------------------------------
# Pre-validation
# ---------------------------------------------------------------------------


def validate_existing_agents(
    model_folders: list[str],
    game_ids: list[str],
) -> bool:
    """
    Ensure every (model, game) combo has at least 2 existing agents.
    Returns False if any combo fails.
    """
    ok = True
    for game_id in game_ids:
        game_name = GAME_REGISTRY[game_id]["name"]
        agents = discover_agents(game_name)
        for folder in model_folders:
            runs = agents.get(folder, [])
            if len(runs) < 2:
                print(
                    f"ERROR: Model '{folder}' has only {len(runs)} agent(s) "
                    f"for game {game_name}. Need at least 2."
                )
                ok = False
    return ok


# ---------------------------------------------------------------------------
# Match execution
# ---------------------------------------------------------------------------


def parse_match_result(stdout: str) -> dict | None:
    """
    Parse match results from match subprocess stdout.

    The outer match script prints:
        FINAL RESULTS:
          folder: Pts 377, Score -3315.0
          folder: Pts 2438, Score 3315.0

    We extract the Pts values in order (agent-1 first, agent-2 second).
    Falls back to the inner RESULT:Agent-1=X,Agent-2=Y format if present.
    """
    # Try inner format first (in case script architecture changes)
    res = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", stdout)
    if res:
        return {
            "agent1_points": float(res.group(1)),
            "agent2_points": float(res.group(2)),
        }

    # Parse outer FINAL RESULTS format
    pts_matches = re.findall(r"Pts\s+(\d+),\s*Score", stdout)
    if len(pts_matches) >= 2:
        return {
            "agent1_points": float(pts_matches[0]),
            "agent2_points": float(pts_matches[1]),
        }

    return None


async def run_enhancement_match(
    game_id: str,
    model_folder: str,
    run_a: int,
    run_b: int,
    tag: str,
    match_semaphore: asyncio.Semaphore,
) -> dict:
    """
    Run a single same-model match between two agents.
    Overrides NUM_OF_GAMES_IN_A_MATCH in the subprocess environment to 10x.
    """
    game_info = GAME_REGISTRY[game_id]
    match_script = SCRIPT_DIR / game_info["script"]

    enhanced_games = BASE_NUM_GAMES * ENHANCEMENT_MULTIPLIER
    cmd = [
        sys.executable,
        str(match_script),
        "--agent",
        f"{model_folder}:{run_a}",
        f"{model_folder}:{run_b}",
        # No --update-scoreboard
    ]
    label = f"{model_folder}:{run_a} vs {model_folder}:{run_b}"

    # Override env var for the subprocess
    env = os.environ.copy()
    env["NUM_OF_GAMES_IN_A_MATCH"] = str(enhanced_games)

    async with match_semaphore:
        print(f"  {tag} Starting match: {label}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=MATCH_TIMEOUT
            )
        except asyncio.TimeoutError:
            print(f"  {tag} Match TIMED OUT: {label}")
            return {
                "run_a": run_a,
                "run_b": run_b,
                "success": False,
                "error": "Match timed out",
                "label": label,
            }
        except Exception as e:
            print(f"  {tag} Match ERROR: {label} — {e}")
            return {
                "run_a": run_a,
                "run_b": run_b,
                "success": False,
                "error": str(e),
                "label": label,
            }

        stdout_str = stdout_bytes.decode(errors="replace")
        stderr_str = stderr_bytes.decode(errors="replace")

        if proc.returncode != 0:
            print(f"  {tag} Match FAILED: {label}")
            return {
                "run_a": run_a,
                "run_b": run_b,
                "success": False,
                "error": stderr_str[:500],
                "label": label,
                "stdout": stdout_str,
            }

        parsed = parse_match_result(stdout_str)
        if not parsed:
            print(f"  {tag} Match PARSE ERROR: {label}")
            return {
                "run_a": run_a,
                "run_b": run_b,
                "success": False,
                "error": "Could not parse RESULT line from stdout",
                "label": label,
                "stdout": stdout_str,
            }

        print(
            f"  {tag} Match done: {label} — "
            f"Pts: {parsed['agent1_points']:.0f} vs {parsed['agent2_points']:.0f}"
        )

        return {
            "run_a": run_a,
            "run_b": run_b,
            "success": True,
            "agent1_points": parsed["agent1_points"],
            "agent2_points": parsed["agent2_points"],
            "label": label,
            "stdout": stdout_str,
        }


# ---------------------------------------------------------------------------
# Tournament evaluation
# ---------------------------------------------------------------------------


def determine_worst_agent(
    existing_runs: list[int],
    new_run: int,
    results: list[dict],
    extra_results: list[dict] | None = None,
) -> int:
    """
    Determine the worst agent run ID based on match results.

    Logic:
    - If new agent lost to all existing agents -> new is worst.
    - If new agent beat all existing agents -> extra_results (between
      existing agents) is used to find the worst existing agent.
    - Mixed case: the agent that lost to the new agent with the fewest
      points is worst (if multiple lost, pick worst among them).

    Returns the run ID of the worst agent.
    """
    new_wins_against: list[int] = []
    new_losses_against: list[int] = []

    for r in results:
        if not r["success"]:
            continue

        if r["run_a"] == new_run:
            new_pts = r["agent1_points"]
            opp_pts = r["agent2_points"]
            opp_run = r["run_b"]
        else:
            new_pts = r["agent2_points"]
            opp_pts = r["agent1_points"]
            opp_run = r["run_a"]

        if new_pts > opp_pts:
            new_wins_against.append(opp_run)
        else:
            new_losses_against.append(opp_run)

    # Case 1: New lost to all
    if not new_wins_against:
        return new_run

    # Case 2: New beat all -> need extra_results to find worst among existing
    if not new_losses_against:
        if not extra_results:
            return _worst_by_points(existing_runs, results, new_run)
        return _worst_from_existing_matches(existing_runs, extra_results)

    # Case 3: Mixed — among agents that lost to the new agent, pick the one
    # with fewest points against the new agent
    losers = new_wins_against
    if len(losers) == 1:
        return losers[0]

    return _worst_by_points(losers, results, new_run)


def _worst_by_points(
    candidate_runs: list[int],
    results: list[dict],
    new_run: int,
) -> int:
    """Among candidate_runs, return the one that scored fewest points vs new_run."""
    points: dict[int, float] = {r: 0.0 for r in candidate_runs}

    for res in results:
        if not res["success"]:
            continue

        if res["run_a"] == new_run and res["run_b"] in points:
            points[res["run_b"]] += res["agent2_points"]
        elif res["run_b"] == new_run and res["run_a"] in points:
            points[res["run_a"]] += res["agent1_points"]

    return min(points, key=lambda r: points[r])


def _worst_from_existing_matches(
    existing_runs: list[int],
    results: list[dict],
) -> int:
    """Among existing agents, find the worst based on head-to-head results."""
    points: dict[int, float] = {r: 0.0 for r in existing_runs}

    for res in results:
        if not res["success"]:
            continue
        if res["run_a"] in points:
            points[res["run_a"]] += res["agent1_points"]
        if res["run_b"] in points:
            points[res["run_b"]] += res["agent2_points"]

    return min(points, key=lambda r: points[r])


# ---------------------------------------------------------------------------
# Agent file operations
# ---------------------------------------------------------------------------


def delete_agent(model_folder: str, game_name: str, run_id: int) -> None:
    """Delete an agent file."""
    agent_file = AGENTS_DIR / model_folder / f"{game_name}_{run_id}.py"
    if agent_file.exists():
        agent_file.unlink()
        print(f"  Deleted: {agent_file.relative_to(PROJECT_ROOT)}")
    else:
        print(f"  WARNING: File not found for deletion: {agent_file}")


def rename_agent(
    model_folder: str,
    game_name: str,
    old_run: int,
    new_run: int,
) -> None:
    """Rename an agent file from one run ID to another."""
    old_path = AGENTS_DIR / model_folder / f"{game_name}_{old_run}.py"
    new_path = AGENTS_DIR / model_folder / f"{game_name}_{new_run}.py"

    if not old_path.exists():
        print(f"  WARNING: Cannot rename — source not found: {old_path}")
        return

    old_path.rename(new_path)
    print(f"  Renamed: {old_path.name} -> {new_path.name}")


# ---------------------------------------------------------------------------
# Per-combo pipeline (populate -> match -> evaluate -> prune)
# ---------------------------------------------------------------------------


async def run_combo_pipeline(
    api: ModelAPI,
    model_name: str,
    model_folder: str,
    game_id: str,
    existing_runs: list[int],
    prompt: str,
    game_name: str,
    api_semaphore: asyncio.Semaphore,
    match_semaphore: asyncio.Semaphore,
    timestamp: str,
) -> None:
    """
    Full pipeline for one (model, game) combo.

    Stages run sequentially within this combo, but multiple combos execute
    concurrently via asyncio.gather in the caller.
    """
    tag = f"[{model_folder}/{game_id}]"

    model_dir = AGENTS_DIR / model_folder
    model_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. Population: single API call (shares semaphore with other combos) ---
    new_run_ids = get_next_run_ids(model_dir, game_name, 1)
    new_run = new_run_ids[0]

    print(f"  {tag} Populating new agent (run {new_run})...")
    _, _, _, content = await prompt_model(
        api, model_name, prompt, new_run, game_name, api_semaphore
    )

    if not content:
        print(f"  {tag} FAILED: Empty API response. Skipping combo.")
        return

    code, imports = extract_agent_code(content, game_name)
    if not code:
        print(f"  {tag} FAILED: No agent code found in response. Skipping combo.")
        return

    # Save agent file
    file_content = f'"""\nAgent Code: {game_name}\nModel: {model_name}\nRun: {new_run}\nGenerated: {timestamp}\n"""\n\n{imports}\n\n{code}\n'
    output_file = model_dir / f"{game_name}_{new_run}.py"
    output_file.write_text(file_content)
    print(f"  {tag} Agent saved: {output_file.name}")

    # --- 2. Matches: new agent vs each existing (all at once) ---
    enhanced_games = BASE_NUM_GAMES * ENHANCEMENT_MULTIPLIER
    total_matches = len(existing_runs)
    print(f"  {tag} Running {total_matches} matches ({enhanced_games} games each)...")

    match_tasks = [
        run_enhancement_match(
            game_id, model_folder, new_run, ex_run, tag, match_semaphore
        )
        for ex_run in existing_runs
    ]
    results = await asyncio.gather(*match_tasks)

    # Check for total failure
    successful = [r for r in results if r["success"]]
    if not successful:
        print(f"  {tag} ERROR: All matches failed. Deleting new agent.")
        delete_agent(model_folder, game_name, new_run)
        return

    # --- 3. Evaluate: do we need extra matches between existing agents? ---
    new_wins_against = []
    for r in successful:
        if r["run_a"] == new_run:
            if r["agent1_points"] > r["agent2_points"]:
                new_wins_against.append(r["run_b"])
        else:
            if r["agent2_points"] > r["agent1_points"]:
                new_wins_against.append(r["run_a"])

    extra_results = None
    if len(new_wins_against) == len(existing_runs) and len(existing_runs) > 1:
        print(f"  {tag} New agent beat all existing. Running old-vs-old matches...")
        pairs = list(combinations(existing_runs, 2))
        extra_tasks = [
            run_enhancement_match(
                game_id, model_folder, ra, rb, tag, match_semaphore
            )
            for ra, rb in pairs
        ]
        extra_results_raw = await asyncio.gather(*extra_tasks)
        extra_results = [r for r in extra_results_raw if r["success"]]

    # --- 4. Determine and remove worst agent ---
    worst = determine_worst_agent(existing_runs, new_run, successful, extra_results)

    print(f"\n  {tag} VERDICT: Worst agent is run {worst}")

    if worst == new_run:
        print(f"  {tag} New agent (run {new_run}) did not improve the pool.")
        delete_agent(model_folder, game_name, new_run)
    else:
        print(
            f"  {tag} Existing agent (run {worst}) replaced by "
            f"new agent (run {new_run})."
        )
        delete_agent(model_folder, game_name, worst)
        rename_agent(model_folder, game_name, new_run, worst)

    print(f"  {tag} Done.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main_async() -> None:
    """Async entry point."""
    parser = argparse.ArgumentParser(
        description="Enhance agents by generating a new one and pruning the worst"
    )
    parser.add_argument(
        "--model",
        type=str,
        nargs="+",
        required=True,
        help="Model substrings, indices, or 'all'",
    )
    parser.add_argument(
        "--game",
        type=str,
        required=True,
        help="Comma-separated game prefixes (e.g., A1,A2) or 'all'",
    )

    args = parser.parse_args()

    # Initialize API
    api = ModelAPI()
    if not api.models:
        print("ERROR: No models loaded from config/models.txt")
        sys.exit(1)

    # Resolve models
    models = resolve_models(api, args.model)
    if not models:
        print("ERROR: No valid models selected")
        sys.exit(1)

    # Resolve games
    game_ids = resolve_game_ids(args.game)
    if not game_ids:
        print("ERROR: No valid games selected")
        sys.exit(1)

    # Build model folder mapping
    model_folders = {sanitize_model_name(m): m for m in models}

    # Pre-validation: all combos must have >= 2 existing agents
    print("\nPre-validation: checking existing agents...")
    if not validate_existing_agents(list(model_folders.keys()), game_ids):
        print(
            "\nAborting. Ensure each model/game combo has at least 2 agents "
            "before running enhancement."
        )
        sys.exit(1)

    # Load all game prompts upfront
    game_prefixes = [gid for gid in game_ids]
    prompts = load_game_prompts(game_prefixes)
    if not prompts:
        print("ERROR: No game prompts found")
        sys.exit(1)

    # Build combo list and snapshot existing agents
    combos: list[dict] = []
    for folder, model_name in model_folders.items():
        for game_id in game_ids:
            game_name = GAME_REGISTRY[game_id]["name"]
            all_agents = discover_agents(game_name)
            existing_runs = all_agents.get(folder, [])

            # Find the prompt for this game
            prompt = prompts.get(game_name)
            if not prompt:
                print(f"WARNING: No prompt for {game_name}, skipping")
                continue

            combos.append({
                "model_name": model_name,
                "model_folder": folder,
                "game_id": game_id,
                "game_name": game_name,
                "existing_runs": existing_runs,
                "prompt": prompt,
            })

    if not combos:
        print("ERROR: No valid combos to enhance")
        sys.exit(1)

    # Compute stats for summary
    enhanced_games = BASE_NUM_GAMES * ENHANCEMENT_MULTIPLIER
    worst_case_subprocesses = sum(len(c["existing_runs"]) for c in combos)

    print(f"\n{'=' * 60}")
    print("AGENT ENHANCEMENT")
    print(f"{'=' * 60}")
    print(f"Models: {len(models)}")
    for folder in model_folders:
        print(f"  - {folder}")
    print(f"Games: {len(game_ids)}")
    for gid in game_ids:
        print(f"  - {GAME_REGISTRY[gid]['name']}")
    print(f"Combos: {len(combos)}")
    print(f"Games per match: {enhanced_games} (base {BASE_NUM_GAMES} x {ENHANCEMENT_MULTIPLIER})")
    print(f"API calls: {len(combos)}")
    print(f"Match subprocesses: {worst_case_subprocesses} needed, max {MAX_MATCH_WORKERS} concurrent")
    print(f"{'=' * 60}")

    confirm = input("\nProceed? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    # Fire all combos concurrently — each combo is an independent pipeline
    api_semaphore = asyncio.Semaphore(POPULATE_MAX_WORKERS)
    match_semaphore = asyncio.Semaphore(MAX_MATCH_WORKERS)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_time = time.time()

    pipeline_tasks = [
        run_combo_pipeline(
            api,
            combo["model_name"],
            combo["model_folder"],
            combo["game_id"],
            combo["existing_runs"],
            combo["prompt"],
            combo["game_name"],
            api_semaphore,
            match_semaphore,
            timestamp,
        )
        for combo in combos
    ]

    print(f"\nLaunching {len(pipeline_tasks)} combo pipelines...\n")
    await asyncio.gather(*pipeline_tasks)

    duration = time.time() - start_time
    duration_str = time.strftime("%H:%M:%S", time.gmtime(duration))
    print(f"\n{'=' * 60}")
    print(f"ENHANCEMENT COMPLETE — {duration_str}")
    print(f"{'=' * 60}")


def main() -> None:
    """Entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
