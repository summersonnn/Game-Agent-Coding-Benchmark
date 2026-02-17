# Scans all scoreboard files and reports same-model agents with divergent rankings.
# An "inconsistency" is when two runs of the same model differ in rank by more than 10.
# Run explicitly: uv run python spot_inconsistent_performances.py [--game A1]

from __future__ import annotations

import argparse
import re
from pathlib import Path

SCOREBOARD_DIR = Path(__file__).parent / "scoreboard"
MIN_RANK_DIFF = 10


def ordinal(n: int) -> str:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
    return f"{n}{suffix}"


def parse_scoreboard(path: Path) -> dict[str, int]:
    """Return {agent_name: rank} from a scoreboard file (1-indexed, skips header)."""
    rankings: dict[str, int] = {}
    rank = 0
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("Agent"):
            continue
        agent = line.split("|")[0].strip()
        rank += 1
        rankings[agent] = rank
    return rankings


def model_name(agent: str) -> str:
    """Strip the run suffix (:1, :2, …) to get the model identifier."""
    return re.sub(r":\d+$", "", agent)


def find_inconsistencies(
    rankings: dict[str, int],
) -> list[tuple[str, str, int, str, int, int]]:
    """
    Group agents by model, then find all pairs whose rank differs by > MIN_RANK_DIFF.
    Returns list of (model, agent_a, rank_a, agent_b, rank_b, diff), sorted by diff desc.
    """
    from collections import defaultdict

    by_model: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for agent, rank in rankings.items():
        by_model[model_name(agent)].append((agent, rank))

    results = []
    for model, agents in by_model.items():
        if len(agents) < 2:
            continue
        # Check every pair (handles models with 3+ runs too)
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a_name, a_rank = agents[i]
                b_name, b_rank = agents[j]
                diff = abs(a_rank - b_rank)
                if diff > MIN_RANK_DIFF:
                    # Put lower rank (better) first
                    if a_rank > b_rank:
                        a_name, a_rank, b_name, b_rank = b_name, b_rank, a_name, a_rank
                    results.append((model, a_name, a_rank, b_name, b_rank, diff))

    results.sort(key=lambda x: x[5], reverse=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report same-model agents with divergent scoreboard rankings."
    )
    parser.add_argument(
        "--game",
        default="all",
        metavar="GAME",
        help='Game ID to analyse (e.g. A1, A8) or "all" for every game (default: all)',
    )
    args = parser.parse_args()

    if args.game.lower() == "all":
        scoreboards = sorted(SCOREBOARD_DIR.glob("A*-scoreboard.txt"))
    else:
        game_id = args.game.upper()
        path = SCOREBOARD_DIR / f"{game_id}-scoreboard.txt"
        if not path.exists():
            parser.error(f"No scoreboard found for game '{game_id}' at {path}")
        scoreboards = [path]

    for path in scoreboards:
        game_id = path.stem.replace("-scoreboard", "")
        rankings = parse_scoreboard(path)

        if not rankings:
            continue

        inconsistencies = find_inconsistencies(rankings)

        print(f"{game_id} - inconsistent rankings")
        if not inconsistencies:
            print("  (none above threshold)")
        else:
            for model, a_name, a_rank, b_name, b_rank, diff in inconsistencies:
                print(
                    f"  {model}"
                    f" - {a_name}: {ordinal(a_rank)}"
                    f" - {b_name}: {ordinal(b_rank)}"
                    f" - Difference: {diff}"
                )
        print()


if __name__ == "__main__":
    main()
