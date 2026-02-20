"""
Global scoreboard persistence for cross-match score accumulation.

Reads/writes pipe-delimited scoreboard files with file-level locking
(fcntl.flock) for safe concurrent access from parallel match runners.
Supports both 2-player (7-column) and 6-player (10-column) formats.
"""

import fcntl
from pathlib import Path


def update_scoreboard(
    scoreboard_path: Path,
    agent_name: str,
    games_played: int,
    wins: int,
    losses: int,
    draws: int,
    score: float,
    points: int = 0,
) -> None:
    """Atomically update an agent's row in the scoreboard file.

    Creates the scoreboard directory and file if they don't exist. Uses an
    adjacent .lock file with LOCK_EX for cross-process safety.
    """
    scoreboard_path = Path(scoreboard_path)
    scoreboard_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = scoreboard_path.with_suffix(".lock")

    with open(lock_path, "w") as lock_fh:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)

        entries: dict[str, dict] = {}
        if scoreboard_path.exists():
            for line in scoreboard_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("Agent"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 7:
                    try:
                        entries[parts[0]] = {
                            "games": int(parts[1]),
                            "wins": int(parts[2]),
                            "losses": int(parts[3]),
                            "draws": int(parts[4]),
                            "points": int(parts[5]),
                            "score": float(parts[6]),
                        }
                    except (ValueError, IndexError):
                        continue
                elif len(parts) == 6:
                    try:
                        entries[parts[0]] = {
                            "games": int(parts[1]),
                            "wins": int(parts[2]),
                            "losses": int(parts[3]),
                            "draws": int(parts[4]),
                            "points": 0,
                            "score": float(parts[5]),
                        }
                    except (ValueError, IndexError):
                        continue

        if agent_name in entries:
            row = entries[agent_name]
            row["games"] += games_played
            row["wins"] += wins
            row["losses"] += losses
            row["draws"] += draws
            row["points"] += points
            row["score"] += score
        else:
            entries[agent_name] = {
                "games": games_played,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "points": points,
                "score": score,
            }

        sorted_entries = sorted(
            entries.items(),
            key=lambda kv: (kv[1]["points"], kv[1]["score"]),
            reverse=True,
        )

        lines = ["Agent | Games | Wins | Losses | Draws | Points | Score"]
        for name, row in sorted_entries:
            lines.append(
                f"{name} | {row['games']} | {row['wins']} | "
                f"{row['losses']} | {row['draws']} | "
                f"{row['points']} | {row['score']:.1f}"
            )

        scoreboard_path.write_text("\n".join(lines) + "\n")


def update_scoreboard_6p(
    scoreboard_path: Path,
    agent_name: str,
    games_played: int,
    placements: dict[str, int],
    points: int,
    score: float,
) -> None:
    """Atomically update an agent's row in the 6-player scoreboard file.

    Uses a 10-column format with per-placement counts (1st through 6th).
    Creates the scoreboard directory and file if they don't exist. Uses an
    adjacent .lock file with LOCK_EX for cross-process safety.
    """
    scoreboard_path = Path(scoreboard_path)
    scoreboard_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = scoreboard_path.with_suffix(".lock")

    placement_keys = ["1st", "2nd", "3rd", "4th", "5th", "6th"]

    with open(lock_path, "w") as lock_fh:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)

        entries: dict[str, dict] = {}
        if scoreboard_path.exists():
            for line in scoreboard_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("Agent"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 10:
                    try:
                        entries[parts[0]] = {
                            "games": int(parts[1]),
                            "1st": int(parts[2]),
                            "2nd": int(parts[3]),
                            "3rd": int(parts[4]),
                            "4th": int(parts[5]),
                            "5th": int(parts[6]),
                            "6th": int(parts[7]),
                            "points": int(parts[8]),
                            "score": float(parts[9]),
                        }
                    except (ValueError, IndexError):
                        continue

        if agent_name in entries:
            row = entries[agent_name]
            row["games"] += games_played
            for k in placement_keys:
                row[k] += placements.get(k, 0)
            row["points"] += points
            row["score"] += score
        else:
            row = {"games": games_played, "points": points, "score": score}
            for k in placement_keys:
                row[k] = placements.get(k, 0)
            entries[agent_name] = row

        sorted_entries = sorted(
            entries.items(),
            key=lambda kv: (kv[1]["points"], kv[1]["score"]),
            reverse=True,
        )

        header = "Agent | Games | 1st | 2nd | 3rd | 4th | 5th | 6th | Points | Score"
        lines = [header]
        for name, row in sorted_entries:
            lines.append(
                f"{name} | {row['games']} | "
                f"{row['1st']} | {row['2nd']} | {row['3rd']} | "
                f"{row['4th']} | {row['5th']} | {row['6th']} | "
                f"{row['points']} | {row['score']:.1f}"
            )

        scoreboard_path.write_text("\n".join(lines) + "\n")
