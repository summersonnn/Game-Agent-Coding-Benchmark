# Competitive LLM Agents: Global Game Script Standards

**Version:** 1.0  
**Last Updated:** 2026-11-21

This document defines the **mandatory** standards for all game match runner scripts (e.g., `A1-battleship_match.py`, `A8-surround_morris_match.py`). Adhering to these rules ensures compatibility with the central matchmaker, scoreboard system, and analysis tools.

---

## 1. Scoring & Game Outcome

Two-player games use a standardized 3-point system and a separate score for
tie-breaking. Wizard uses six-player placement points instead. Backgammon
awards league points for the complete race to five in-game points.

### 1.1 Match Points (Primary Metric)
*   **Win:** 3 points
*   **Draw:** 1 point
*   **Loss:** 0 points

**Wizard exception:** Each full ten-round game awards 5/4/3/2/1/0 placement
points. Ties share the points for the tied positions. Qualifiers select one
agent per model; only main-event matches update the Wizard scoreboard.

### 1.2 Tie-Breaker Score (Secondary Metric)
*   A granular score reflecting performance (e.g., remaining ships, pieces on board).
*   **Winner:** Positive score (e.g., +12).
*   **Loser:** Negative score (e.g., -12).
*   **Draw:** 0 (usually).
*   Used to rank agents that have the same number of match points. Also used in scoreboard.
*   If an agent crashes (not in make_move) and thus forfeits the game, the winner will get max possible score (e.g., +12). And the loser (crashing agent) will get min possible score (e.g., -12). If there are no such max and min scores for the game in the game logic (meaning that the score is not bounded by any number), they will get fixed scores of +12 and -12 respectively.

### 1.3 Standard Output Format
The embedded two-player match runner prints the following lines to `stdout`
at the end of execution. Its outer runner parses them for statistics and
scoreboard updates. Wizard emits six-agent result and score lines plus
placement statistics, without the two-player `WINS` and `DRAWS` lines.

```text
RESULT:Agent-1=<match_points_float>,Agent-2=<match_points_float>
SCORE:Agent-1=<tie_breaker_float>,Agent-2=<tie_breaker_float>
WINS:Agent-1=<win_count_int>,Agent-2=<win_count_int>
DRAWS:<draw_count_int>
```

*   **RESULT**: Correspond to Match Points (3/1/0).
*   **SCORE**: Correspond to Tie-breaker Score.

**Example:**
```text
RESULT:Agent-1=3.0,Agent-2=0.0
SCORE:Agent-1=12.0,Agent-2=-12.0
WINS:Agent-1=1,Agent-2=0
DRAWS:0
```

### 1.4 Standardized Forfeit Handling
For two-player games terminated by an initialization failure:
*   Set the crashing agent's Match Points for that game to 0. (same as doing nothing)
*   Set the opponent's Match Points to 3.
*   Assign the Tie-Breaker Score: -12 for the crasher, +12 for the winner (or max/min game-specific bounds).
*   Increment other_crash for the crashing agent.

Wizard records an initialization failure in `other_crash`, substitutes a
random fallback agent, and continues the game.

---

## 2. Configuration & Environment Variables

All scripts must respect the following configuration parameters, which should be loaded from the environment (e.g., via a .env file using python-dotenv or system environment variables).

| Variable | Default | Description |
| :--- | :--- | :--- |
| `A1_GAMES_PER_MATCH` | `20` | Battleship games per match. |
| `A2_GAMES_PER_MATCH` | `50` | LieOnce games per match. |
| `A3_GAMES_PER_MATCH` | `24` | Wizard games per directly invoked match. |
| `A3_QUALIFIER_GAMES_PER_MATCH` | `402` | Wizard qualifier games per six-player table. |
| `A3_MAIN_EVENT_GAMES_PER_MATCH` | `6` | Wizard main-event games per six-player table. |
| `A4_MAX_GAMES_PER_MATCH` | `30` | Backgammon game cap for a race to five points. |
| `A5_GAMES_PER_MATCH` | `10` | Connect4 games per match. |
| `A6_GAMES_PER_MATCH` | `10` | Word Matrix games per match. |
| `A7_GAMES_PER_MATCH` | `12` | Mancala games per match. |
| `A8_GAMES_PER_MATCH` | `20` | Surround Morris games per match. |
| `MOVE_TIME_LIMIT` | `1.0` | Maximum time (seconds) allowed for an agent to return a move. |
| `MAX_TURNS_PER_GAME` | `100` | Word Matrix turn cap. |
| `A8_MAX_TURNS_PER_GAME` | `200` | Surround Morris movement turn cap; independent of Word Matrix. |

**Time limits (not environment variables):** every runner hardcodes `GAME_TIME_LIMIT`, the maximum time for one game, as a multiple of `MOVE_TIME_LIMIT`. It is checked before every move, includes agent setup, and a game that reaches it ends as a draw. The match limit is derived as `MATCH_TIME_LIMIT = GAME_TIME_LIMIT × games in the match`; the runner hard-kills the match subprocess at `MATCH_TIME_LIMIT` + 60s (only an agent hung inside a move can cause that). The matchmaker does not enforce any timeout. Per-game values and how they were calibrated: CLAUDE.md, "Game Time Limits".

A match is one runner invocation with fixed participants: two agents in a
two-player game, or six in Wizard. A game is one complete play-through; a
Wizard game includes all ten card rounds. A match can contain many games.

Fixed-count two-player defaults are even for seat balance; Wizard defaults
are multiples of six for its seat rotation. They account for draw potential, randomness, and
opening coverage rather than game simplicity alone; see README.md for the
sampling rationale. Mancala samples openings with replacement in shared,
seat-swapped pairs. Repeating fixed deterministic games does not add new
evidence. The two-player matchmaker repeats each pairing eight times by
default; Backgammon repeats races rather than using its cap as a fixed count.

**Implementation Standard:**
The script must prioritize values found in the environment. Missing, invalid, or non-positive game counts must fall back to that game's default. Match counts are independent: do not derive one game's count by dividing a shared base count. You may use any internal variable name that is clear and maintainable.

```python
from dotenv import load_dotenv
from game_config import games_per_match
import os

# Load variables from .env file if it exists
load_dotenv()

# Robustly loading the configuration.
# These are the true values that are being used in the match runner.
NUM_GAMES = games_per_match("A5")  # A5_GAMES_PER_MATCH, default 10
MOVE_TIMEOUT = float(os.getenv("MOVE_TIME_LIMIT", 1.0))

# Hardcoded per game (seconds per game at the default 1s move limit):
GAME_TIME_LIMIT = 30 * MOVE_TIMEOUT
MATCH_TIME_LIMIT = GAME_TIME_LIMIT * NUM_GAMES
```

---

### 2.1 Turn Order Alternation

In games where players take turns, the starting player **must alternate** each game within a match. Specifically, Agent-1 goes first in odd-numbered games (1, 3, 5, …) and Agent-2 goes first in even-numbered games (2, 4, 6, …). This ensures both agents get an equal number of first-move advantages over the course of a match.

```python
# Alternate who goes first each game
if game_num % 2 == 1:
    a1_class, a2_class = class_1, class_2
else:
    a1_class, a2_class = class_2, class_1
```

---

## 3. Error Handling & Robustness

Agents must never cause the match runner to crash. The runner must implement comprehensive exception handling to distinguish between different failure modes.

### 3.1 Error Counter Standardization
The match_stats dictionary for each agent must track the following five keys to ensure precise debugging and ranking:

*   `make_move_crash`: Any exception raised inside the agent's make_move() function.
*   `other_crash`: Any exception raised during initialization (__init__) or other non-move methods.
*   `timeout`: Moves exceeding `MOVE_TIME_LIMIT`.
*   `invalid`: Formatting errors or illegal moves.
*   `crash`: Sum of `make_move_crash` and `other_crash`.

| Failure Type         | Consequence                                           | Stat to Increment |
| -------------------- | ----------------------------------------------------- | ----------------- |
| make_move() Crash    | Generate a random valid move; game continues.         | make_move_crash   |
| Initialization Crash | Immediate game forfeit. Opponent wins with max score. | other_crash       |
| Move Timeout         | Generate a random valid move; game continues.         | timeout           |
| Invalid Move         | Generate a random valid move; game continues.         | invalid           |

Agents get one attempt per move. The table above describes the usual fallback;
game-specific exceptions are:

- LieOnce: failed guesses lose a turn; failed number selection or responses
  forfeit the game, as specified in its prompt.
- WordMatrix: move failures apply a -10 penalty, leave the board unchanged,
  and count as a pass.
- Wizard: an initialization failure substitutes a random fallback agent.

For Backgammon (A4), a random valid move is a complete legal turn containing exactly `max_dice_usable` sub-moves. Reject an invalid submitted sequence in full before applying the fallback; never keep a valid prefix or substitute a shorter sequence. Each failure increments only its original error counter, while hits and dice used include the fallback. A turn with no legal moves is a legal pass and does not count as an error.

### 3.2 Prohibited: Broad Exception Handlers in `make_move()`
Agent code **must not** wrap the body of `make_move()` in a broad exception handler such as `except Exception`, `except BaseException`, or a bare `except:`. The game engine enforces move time limits via `signal.alarm`, which raises an internal timeout exception. A broad outer catch silently swallows this exception and prevents the engine from enforcing time limits, causing matches to hang. Agents that violate this rule will be flagged by the matchmaker's `--health` check and must be corrected before they can compete. Inform the agents about this rule!

---

## 4. Match Statistics Structure

To support the new tracking requirements, the internal statistics dictionary must follow this exact schema:

```
match_stats = {
    "Agent-1": {
        "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
        "make_move_crash": 0, "other_crash": 0, "crash": 0, 
        "timeout": 0, "invalid": 0
    },
    "Agent-2": {
        "wins": 0, "losses": 0, "draws": 0, "points": 0, "score": 0.0,
        "make_move_crash": 0, "other_crash": 0, "crash": 0, 
        "timeout": 0, "invalid": 0
    },
}
```

Implementation Logic for Stats:

# Aggregate crash stat for backward compatibility with scoreboard
for agent in ["Agent-1", "Agent-2"]:
    match_stats[agent]['crash'] = match_stats[agent]['make_move_crash'] + match_stats[agent]['other_crash']

### 4.1 Stats Block Extraction
The match runner must extract a human-readable "stats block" from the final section of the subprocess output (if present). This block provides a breakdown of all errors (timeouts, crashes, invalid moves) for both agents. In the structured return dict from `run_match`, this is stored under the `stats_block` key and must be included in the final log file.

---

## 5. Resource Management

### 5.1 Temporary Files
Match runners generate temporary Python files to execute agent code (e.g., `battleship_match_<id>.py`).
*   **Requirement:** You **MUST** clean up these files in a `finally` block to prevent disk space leaks.

```python
try:
    # write and execute temp_file
    ...
finally:
    if os.path.exists(temp_file):
        os.remove(temp_file)
```

### 5.2 Concurrency
*   Matches are run in parallel using `asyncio` and `subprocess`.
*   Ensure unique temporary filenames using `uuid`.

---

## 6. Scoreboard Integration

Update the global scoreboard **once per match** (after all games in the match are done), not after every single game.

*   **Library:** Use `utils.scoreboard.update_scoreboard` for two-player games and `update_scoreboard_6p` for Wizard.
*   **Agent Key:** Use the format `{model_folder}:{run_id}`.
*   **Path:** defined in the script header (e.g., `scoreboard/A1-scoreboard.txt`).

```python
# Agent 1 update
agent1_key = f"{folder1}:{result['agent1_run_id']}"
update_scoreboard(
    SCOREBOARD_PATH, agent1_key,
    games_played=NUM_GAMES_PER_MATCH,
    wins=result["agent1_wins"],
    losses=result["agent2_wins"],
    draws=result.get("draws", 0),
    score=result["agent1_score"],
    points=result.get("agent1_points", 0)
)
```

---

## 7. Agent Loading & Execution

Match runners load saved agent source and assemble a standalone executable
script. Their template layout varies: A1 uses a formatted game template;
other runners split engine, match, and/or human-play code into string blocks.

### 7.1 Standardized Agent Extraction (`load_stored_agent`)
To ensure isolation and compatibility with renaming, agents are not loaded via standard Python imports. Instead, a `load_stored_agent` utility function is used to:
1.  Read the agent file from the file system.
2.  Extract only the **class definition** and the **required imports**. 
3.  Discard any top-level executable code, `if __name__ == "__main__":` blocks, or initialization logic that relies on the local environment.

### 7.2 Standardized Script Assembly (`build_game_code`)
Each runner uses `build_game_code` to assemble its temporary execution script.
A common layout combines these components:
1.  **`GAME_ENGINE_CODE`**: The core logic of the game (shared with the human mode code).
2.  **`extra_imports`**: Combined and deduplicated imports from both agents.
3.  **`Agent-1 Code`** and **`Agent-2 Code`**: The extracted and renamed agent classes.
4.  **`MATCH_RUNNER_CODE`**: The script block that instantiates the agents and runs the loops/rounds defined by `NUM_GAMES_PER_MATCH`.

The exact blocks differ by runner. Some human-play modes contain separate
reference engine code, so inspect both paths when changing game rules.

---

## 8. Human Play Modes

Available human-play flags depend on the game:

- A1, A3, A4, A6, A7, A8: `--humanvsbot`, `--humanvshuman`, and
  `--humanvsagent` (with one stored `--agent` spec).
- A2: `--humanvsbot`.
- A5: `--human` for human versus random bot.

Standardized Board Visualization for Humans: To maintain a consistent experience across different games (Battleship, Mancala, Morris), runners should implement a print_state() method for human modes that uses a standard coordinate system (e.g., $(0,0)$ at the top-left).

## 9. Logging & File Naming Conventions
To ensure analysis tools can find results across different games (A1, A2, etc.):

Use these variables (some values are specific to games):

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / <game_name>
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / <game_id>-scoreboard.txt (e.g., A1-scoreboard.txt).
AGENTS_DIR = BASE_DIR / "agents"

This is how to determine the name of the log file explicitly:

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_f = RESULTS_DIR / f"{ts}_{folder1}:{run1}_vs_{folder2}:{run2}_match.txt"

Logs should be directly placed in the RESULTS_DIR. There is no intermediate folder after it.

Each log records a single match and may contain multiple games. There is one
log per match execution. For example, the two-player matchmaker schedules all
four cross-model run pairings for two models with two agents each, then
repeats those pairings according to `--same_opponent_match`. Direct match
runners pair the two supplied run lists by position.


## 10. Metadata Injection (Agent Renaming)
To prevent NameError or AttributeError when two different agents use the same internal helper function names:

Rule: When injecting agent code into the template, all occurrences of the base class name (e.g., BattleshipAgent) must be regex-replaced with BattleshipAgent_1 or BattleshipAgent_2.

Imports: Duplicate imports must be merged and deduplicated before being placed in the {extra_imports} slot.


## 11. Per-Game Log Format
Board-game runners print the final board position in each game's log. The
two-player board-game block format is shown below. LieOnce logs guesses and
responses; Wizard logs rounds, tricks, and rankings instead of a board.

```text
============================================================
Game X
Agent-1: name (color_if_applicable)
Agent-2: name (color_if_applicable)
------------------------------------------------------------
[... move-by-move detail (game-specific, not standardized) ...]
Final Position:
BOARD: <game-specific board display with BOARD: prefix>
<game-specific info, e.g. "Pieces: B=6 W=3">
----------------------------------------
Final Result: Agent-1 wins by elimination.  (or "Draw by Repetition.")
----------------------------------------
Points:
Agent-1: 3
Agent-2: 0
----------------------------------------
Scores:
Agent-1: 5
Agent-2: -5
============================================================
```

*   `============` = game delimiter (between games)
*   `------------` = section delimiter (within a game)
*   Board lines prefixed with `BOARD:`


## 12. Log Storage & Cleanup
| Item         | Specification                                                                                                                     |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| **Location** | `RESULTS_DIR / {timestamp}_{folder1}:{run1}_vs_{folder2}:{run2}_match.txt`                                                                      |
| **Cleanup**  | Raw subprocess stdout should be processed in memory **or** stored in a `.tmp` file and deleted after the filtered log is written. |

## 13. Log Examples

These are illustrative format examples. `MODEL_A` through `MODEL_F` are
placeholders, not recorded participants or benchmark results.

### Two-player match summary

```text
Match Contenders:
MODEL_A:1
MODEL_B:1

RESULT:Agent-1=3.0,Agent-2=0.0
SCORE:Agent-1=12.0,Agent-2=-12.0
WINS:Agent-1=1,Agent-2=0
DRAWS:0
```

### Wizard match summary

Wizard emits six entries in its result and score lines, followed by per-agent
placement and error statistics. A three-way tie or other tied placement can
produce fractional placement points.

```text
RESULT:Agent-1=5.0,Agent-2=4.0,Agent-3=3.0,Agent-4=2.0,Agent-5=1.0,Agent-6=0.0
SCORE:Agent-1=100.0,Agent-2=80.0,Agent-3=60.0,Agent-4=40.0,Agent-5=20.0,Agent-6=0.0
```

---

## 14. Agent Coding Standards

To ensure agents are portable and compatible with the dynamic extraction process:

*   **No Internal Imports:** Agents must not import the game engine, match scripts, or any internal project modules.
*   **Zero Structural Dependency:** Code must not make assumptions regarding the project's file or directory hierarchy.
*   **Single Class Implementation:** Models must not implement any other class than the class present in the given code piece.
*   **Class-Only Focus:** The agent file should be restricted to the agent class definition and its necessary standard library imports. The runner extracts the class text for isolated execution.
