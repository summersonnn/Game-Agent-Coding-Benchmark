"""
Global scoreboard persistence for cross-match score accumulation.

Reads/writes pipe-delimited scoreboard files with file-level locking
(fcntl.flock) for safe concurrent access from parallel match runners.
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
                if len(parts) != 6:
                    continue
                try:
                    entries[parts[0]] = {
                        "games": int(parts[1]),
                        "wins": int(parts[2]),
                        "losses": int(parts[3]),
                        "draws": int(parts[4]),
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
            row["score"] += score
        else:
            entries[agent_name] = {
                "games": games_played,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "score": score,
            }

        sorted_entries = sorted(
            entries.items(), key=lambda kv: kv[1]["score"], reverse=True
        )

        lines = ["Agent | Games | Wins | Losses | Draws | Score"]
        for name, row in sorted_entries:
            lines.append(
                f"{name} | {row['games']} | {row['wins']} | "
                f"{row['losses']} | {row['draws']} | {row['score']:.1f}"
            )

        scoreboard_path.write_text("\n".join(lines) + "\n")
