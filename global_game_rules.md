# Competitive LLM Agents: Global Game Script Standards

**Version:** 1.0  
**Last Updated:** 2026-02-10

This document defines the **mandatory** standards for all game match runner scripts (e.g., `A1-battleship_match.py`, `A8-surround_morris_match.py`). Adhering to these rules ensures compatibility with the central matchmaker, scoreboard system, and analysis tools.

---

## 1. Scoring & Game Outcome

All games must use a standardized 3-point system for match results and a separate "score" for tie-breaking.

### 1.1 Match Points (Primary Metric)
*   **Win:** 3 points
*   **Draw:** 1 point
*   **Loss:** 0 points

### 1.2 Tie-Breaker Score (Secondary Metric)
*   A granular score reflecting performance (e.g., remaining ships, pieces on board).
*   **Winner:** Positive score (e.g., +12).
*   **Loser:** Negative score (e.g., -12).
*   **Draw:** 0 (usually).
*   Used to rank agents that have the same number of match points. Also used in scoreboard.
*   If an agent crashes (not in make_move) and thus forfeits the game, the winner will get max possible score (e.g., +12). And the loser (crashing agent) will get min possible score (e.g., -12). If there are no such max and min scores for the game in the game logic (meaning that the score is not bounded by any number), they will get fixed scores of +12 and -12 respectively.

### 1.3 Standard Output Format
The match runner **must** print the following lines to `stdout` at the end of execution. The matchmaker parses these exact keys.

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
If a game is terminated due to an other_crash (initialization failure):
*   Set the crashing agent's Match Points for that game to 0. (same as doing nothing)
*   Set the opponent's Match Points to 3.
*   Assign the Tie-Breaker Score: -12 for the crasher, +12 for the winner (or max/min game-specific bounds).
*   Increment other_crash for the crashing agent.

---

## 2. Configuration & Environment Variables

All scripts must respect the following configuration parameters, which should be loaded from the environment (e.g., via a .env file using python-dotenv or system environment variables).

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NUM_OF_GAMES_IN_A_MATCH` | `100` | Number of games to play in a single match execution. |
| `MOVE_TIME_LIMIT` | `1.0` | Maximum time (seconds) allowed for an agent to return a move. |

**Implementation Standard:**
The script must prioritize values found in the environment. If the variables are missing or invalid, it must gracefully fall back to the default values. You may use any internal variable name that is clear and maintainable.

```python
from dotenv import load_dotenv
import os

# Load variables from .env file if it exists
load_dotenv()

# Robustly loading the configuration.
# These are the true values that are being used in the match runner.
NUM_GAMES = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", 100))
MOVE_TIMEOUT = float(os.getenv("MOVE_TIME_LIMIT", 1.0))
```

---

## 3. Error Handling & Robustness

Agents must never cause the match runner to crash. The runner must implement comprehensive exception handling to distinguish between different failure modes.

### 3.1 Error Counter Standardization
The match_stats dictionary for each agent must track the following five keys to ensure precise debugging and ranking:

*   `make_move_crash`: Any exception raised inside the agent's make_move() function.
*   `other_crash`: Any exception raised during initialization (__init__) or other non-move methods.
*   `timeout`: Moves exceeding `MOVE_TIME_LIMIT`.
*   `invalid`: Formatting errors, illegal moves, or failing to provide a valid move after max retries.

| Failure Type         | Consequence                                           | Stat to Increment |
| -------------------- | ----------------------------------------------------- | ----------------- |
| make_move() Crash    | Generate a random valid move; game continues.         | make_move_crash   |
| Initialization Crash | Immediate game forfeit. Opponent wins with max score. | other_crash       |
| Move Timeout         | Generate a random valid move; game continues.         | timeout           |
| Invalid Move         | Generate a random valid move; game continues.         | invalid           |

There is no retry mechanism in anywhere of the game!

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

*   **Library:** Use `utils.scoreboard.update_scoreboard`.
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

*   **Discovery:** Load agents from `agents/{model_folder}/{game}_{run}.py`.
*   **Isolation:** Extract only the agent class text.
*   **Renaming:** Rename class to `Agent_1` / `Agent_2` dynamically to avoid name collisions in the generated script.
*   **Imports:** Cleanly extract and merge imports from both agents.

---

## 8. Human Play Modes

Scripts must support interactive modes for testing.
*   `--humanvsbot`: Human vs Random Bot.
*   `--humanvshuman`: Hotseat multiplayer.
*   `--humanvsagent`: Human vs Stored Agent (requires 1 agent arg).

Standardized Board Visualization for Humans: To maintain a consistent experience across different games (Battleship, Chess, Morris), runners should implement a print_state() method for human modes that uses a standard coordinate system (e.g., $(0,0)$ at the top-left).

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
    agent_suffix = f"{folder1}_vs_{folder2}"
    log_f = RESULTS_DIR / f"{ts}_{agent_suffix}_match.txt"

Logs should be directly placed in the RESULTS_DIR. There is no intermediate folder after it.

Each log records information for a single match, though it may contain multiple games within that match. However, only one match is represented per log. So, if the matchmaker runs two matches—such as mistral vs. opus—the number of log files will correspond to the number of agents involved. For example, if there are two agents, one log file will be generated for mistral:1 vs. opus:1 and another for mistral:2 vs. opus:2.


## 10. Metadata Injection (Agent Renaming)
To prevent NameError or AttributeError when two different agents use the same internal helper function names:

Rule: When injecting agent code into the template, all occurrences of the base class name (e.g., BattleshipAgent) must be regex-replaced with BattleshipAgent_1 or BattleshipAgent_2.

Imports: Duplicate imports must be merged and deduplicated before being placed in the {extra_imports} slot.


## 11. Log Filtering & Extraction

To prevent disk bloat and ensure logs remain readable for both humans and analysis tools, the runner must implement a strict output filter. Instead of saving the entire raw stream from the subprocess, the runner must selectively preserve only lines that provide meaningful progression and outcome data. This includes all agent-specific actions (prefixed with Agent-1: or Agent-2:), game state markers (such as GAME, Turn, or Winner:), and essential session dividers.

Critically, the logs must preserve central system data (such as RESULT, SCORE, and CRASH counts) and the final game state. To ensure the final board or position is not stripped by the filter, the runner should prefix these lines with BOARD: or FINAL STATE:. Any line containing the word ENDED or empty lines used for visual spacing should also be kept. All other repetitive debug data, intermediate UI frames, or non-essential agent chatter should be discarded before the final write to the results directory.

### 11.1 Per-Game Log Format
Every game match runner must print the final board position in the logs of each game. The standardized per-game log block format is:

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
| **Location** | `RESULTS_DIR / {timestamp}_{folder1}_vs_{folder2}_match.txt`                                                                      |
| **Cleanup**  | Raw subprocess stdout should be processed in memory **or** stored in a `.tmp` file and deleted after the filtered log is written. |

## 13. Log Examples
These examples demonstrate how the standardized headers, separators, and machine-readable tags are implemented in practice.

### A1 Battleship Example
```text
Match Contenders:
mistralai-mistral-large-2512:1
openai-gpt-oss-120b-fp8:1

Result:
mistralai-mistral-large-2512:1 : Pts: 3 - Score: -1.0
openai-gpt-oss-120b-fp8:1 : Pts: 6 - Score: 1.0

============================================================
Game 1
Agent-1: mistralai-mistral-large-2512
Agent-2: openai-gpt-oss-120b-fp8
------------------------------------------------------------
Final Position:
BOARD: mistralai-mistral-large-2512 Ships:
BOARD:    0 1 2 3 4 5 6 7
BOARD: 0  # O O O O O O O
...
BOARD: 7  S S S S S O O O

BOARD: openai-gpt-oss-120b-fp8 Ships:
BOARD:    0 1 2 3 4 5 6 7
...
----------------------------------------
Final Result: mistralai-mistral-large-2512 wins by Elimination.
----------------------------------------
Points:
Agent-1: 3
Agent-2: 0
----------------------------------------
Scores:
Agent-1: 5
Agent-2: -5
============================================================
============================================================
Agent-1: mistralai-mistral-large-2512
Agent-2: openai-gpt-oss-120b-fp8
RESULT:Agent-1=3.0,Agent-2=6.0
SCORE:Agent-1=-1.0,Agent-2=1.0
WINS:Agent-1=1,Agent-2=2
DRAWS:0
STATS:Agent-1={...},Agent-2={...}

--- MATCH STATISTICS ---
Agent-1 make_move_crash: 0
Agent-2 make_move_crash: 0
...
------------------------------------------------------------
```

### A8 Surround Morris Example
```text
Match Contenders:
anthropic-claude-opus-4.6:1
google-gemini-3-pro-preview:1

Result:
anthropic-claude-opus-4.6:1 : Pts: 5 - Score: 6.0
google-gemini-3-pro-preview:1 : Pts: 2 - Score: -6.0

============================================================
Game 1
Agent-1: anthropic-claude-opus-4.6:1 (W)
Agent-2: google-gemini-3-pro-preview:1 (B)
------------------------------------------------------------

Final Position:
BOARD:  .----------B----------.
BOARD:  |           |           |
...
BOARD:  .----------B----------B
Pieces: B=7 W=4
----
Final Result: Draw by Repetition
----------------------------------------
Points:
Agent-1: 1
Agent-2: 1
----------------------------------------
Scores:
Agent-1: 0
Agent-2: 0
============================================================
============================================================
Agent-1: anthropic-claude-opus-4.6:1
Agent-2: google-gemini-3-pro-preview:1
RESULT:Agent-1=5,Agent-2=2
SCORE:Agent-1=6.0,Agent-2=-6.0
WINS:Agent-1=1,Agent-2=0
DRAWS:2
STATS:Agent-1={...},Agent-2={...}

--- MATCH STATISTICS ---
Agent-1 make_move_crash: 0
Agent-2 make_move_crash: 0
...
------------------------------------------------------------
```
