"""
This script parses game logs to aggregate failure statistics across agents.
It reads through all text logs for a specified game, extracting 'timeout', 
'invalid', 'make_move_crash', and 'crash' counts for each agent, and prints 
the sorted aggregated results, skipping any agents with zero occurrences.
"""

import argparse
import ast
import logging
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True, type=str)
    return parser.parse_args()


def process_log_file(
    file_path: Path, agent_stats: dict[str, dict[str, int]], stats_keys: list[str]
) -> None:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except OSError as e:
        logger.error(f"Failed to read %s: %s", file_path, e)
        return

    agent_1_name: str | None = None
    agent_2_name: str | None = None
    agent_1_stats: dict[str, int] | None = None
    agent_2_stats: dict[str, int] | None = None

    for line in reversed(lines):
        line = line.strip()
        if line.startswith("Agent-1: ") and agent_1_name is None:
            agent_1_name = line.split("Agent-1: ")[1].strip()
        elif line.startswith("Agent-2: ") and agent_2_name is None:
            agent_2_name = line.split("Agent-2: ")[1].strip()
        elif line.startswith("STATS:Agent-1=") and agent_1_stats is None:
            try:
                agent_1_stats = ast.literal_eval(line.split("STATS:Agent-1=")[1])
            except (ValueError, SyntaxError) as e:
                logger.error("Failed to parse STATS:Agent-1 in %s: %s", file_path, e)
        elif line.startswith("STATS:Agent-2=") and agent_2_stats is None:
            try:
                agent_2_stats = ast.literal_eval(line.split("STATS:Agent-2=")[1])
            except (ValueError, SyntaxError) as e:
                logger.error("Failed to parse STATS:Agent-2 in %s: %s", file_path, e)

        if agent_1_name and agent_2_name and agent_1_stats and agent_2_stats:
            break

    if agent_1_name and agent_1_stats:
        for k in stats_keys:
            agent_stats[k][agent_1_name] += agent_1_stats.get(k, 0)
    if agent_2_name and agent_2_stats:
        for k in stats_keys:
            agent_stats[k][agent_2_name] += agent_2_stats.get(k, 0)


def print_stats(agent_stats: dict[str, dict[str, int]], key: str, title: str) -> None:
    stats = agent_stats[key]
    valid_stats = {k: v for k, v in stats.items() if v > 0}
    if not valid_stats:
        return

    print(f"\n{title}:")
    sorted_stats = sorted(valid_stats.items(), key=lambda x: x[1], reverse=True)
    for agent, val in sorted_stats:
        print(f"- {agent} : {val}")


def main() -> None:
    args = parse_arguments()
    results_dir = Path(__file__).parent.parent / "results" / args.game

    if not results_dir.exists() or not results_dir.is_dir():
        logger.error("Directory %s does not exist.", results_dir)
        return

    stats_keys = ["timeout", "invalid", "make_move_crash", "crash"]
    agent_stats: dict[str, dict[str, int]] = {
        key: defaultdict(int) for key in stats_keys
    }

    for log_file in results_dir.glob("*.txt"):
        process_log_file(log_file, agent_stats, stats_keys)

    print_stats(agent_stats, "timeout", "Agents with the most timeouts")
    print_stats(agent_stats, "make_move_crash", "Agents with most make_move crashes")
    print_stats(agent_stats, "crash", "Agents with most general crashes")
    print_stats(agent_stats, "invalid", "Agents with most invalid moves")


if __name__ == "__main__":
    main()
