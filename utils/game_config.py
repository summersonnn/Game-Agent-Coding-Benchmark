"""Independent match sizes for each game.

Callers load their .env file before reading these settings. Backgammon's
setting is a cap because a match ends when an agent reaches five points.
"""

import os


MATCH_GAME_SETTINGS: dict[str, tuple[str, int]] = {
    "A1": ("A1_GAMES_PER_MATCH", 20),
    "A2": ("A2_GAMES_PER_MATCH", 50),
    "A3": ("A3_GAMES_PER_MATCH", 24),
    "A4": ("A4_MAX_GAMES_PER_MATCH", 30),
    "A5": ("A5_GAMES_PER_MATCH", 10),
    "A6": ("A6_GAMES_PER_MATCH", 10),
    "A7": ("A7_GAMES_PER_MATCH", 12),
    "A8": ("A8_GAMES_PER_MATCH", 20),
}

WIZARD_PHASE_GAME_SETTINGS: dict[str, tuple[str, int]] = {
    "qualifier": ("A3_QUALIFIER_GAMES_PER_MATCH", 402),
    "main_event": ("A3_MAIN_EVENT_GAMES_PER_MATCH", 6),
}


def match_count_env_var(game_id: str) -> str:
    """Return the environment variable used by this game's runner."""
    return MATCH_GAME_SETTINGS[game_id][0]


def games_per_match(game_id: str) -> int:
    """Read a game's positive match count, falling back to its own default."""
    return _read_count(*MATCH_GAME_SETTINGS[game_id])


def wizard_phase_games_per_match(phase: str) -> int:
    """Read a Wizard phase's independent count without scaling another count."""
    return _read_count(*WIZARD_PHASE_GAME_SETTINGS[phase])


def _read_count(env_var: str, default: int) -> int:
    try:
        count = int(os.getenv(env_var, str(default)))
    except (ValueError, TypeError):
        return default
    return count if count > 0 else default
