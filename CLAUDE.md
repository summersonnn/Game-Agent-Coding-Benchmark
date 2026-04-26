# Competitive LLM Agents

Benchmarking framework for evaluating LLMs in competitive multi-agent game environments. Generates agent implementations via OpenRouter API and orchestrates head-to-head/multiplayer matches.

## Project Structure

```
agents/           # Generated agent code (organized by model name)
config/           # Configuration: models.txt
games/            # Game prompts/rules (A1-Battleship, A2-LieOnce, ...)
results/          # Match logs and outcomes
utils/            # Core logic - API client, match runners, agent generation
```

## Entry Points

**Agent Generation:**
```bash
uv run utils/populate_agents.py --all                           # All models, all games
uv run utils/populate_agents.py --model mistral gpt             # Specific models
uv run utils/populate_agents.py --game A1,A5 --runs 3           # Specific games
```

**Running Individual Matches:**
```bash
uv run game_scripts/A1-battleship_match.py --agent model1:1 model2:1
uv run game_scripts/A2-lie_once_match.py --agent model1:1 model2:1
uv run game_scripts/A4-backgammon_match.py --agent model1:1 model2:1
uv run game_scripts/A5-connect4_match.py --agent model1:1 model2:1
uv run game_scripts/A6-word_matrix_match.py --agent model1:1 model2:1
uv run game_scripts/A7-twobyeight_chess_match.py --agent model1:1 model2:1
uv run game_scripts/A8-surround_morris_match.py --agent model1:1 model2:1
```

> Individual match runners also accept `--update-scoreboard` to persist results to the scoreboard file. Omit it for ad-hoc test matches; the matchmaker appends it automatically for tournament runs.

**Running Tournaments (Matchmaker):**
```bash
uv run game_scripts/matchmaker.py --game A8 --same_opponent_match 4
uv run game_scripts/matchmaker.py --game A8 --dry-run
uv run game_scripts/matchmaker.py --game A8 --new-model new-model-folder --health
```

**Agent Enhancement:**
```bash
uv run utils/try_enhancing_agents.py --model mistral --game A5        # Single model, single game
uv run utils/try_enhancing_agents.py --model mistral minimax --game A1,A5  # Multiple
uv run utils/try_enhancing_agents.py --model all --game all           # All 2-player combos
```

## Key Modules

| File | Purpose |
|------|---------|
| `utils/model_api.py` | Async OpenRouter API client |
| `utils/populate_agents.py` | LLM-based agent code generation |
| `utils/try_enhancing_agents.py` | Agent quality improvement via same-model benchmarking |
| `game_scripts/*_match.py` | Game-specific match orchestrators |
| `game_scripts/matchmaker.py` | Round-robin tournament scheduler |
| `utils/logging_config.py` | Centralized logging setup |
| `global_game_rules.md` | Canonical specification for all match runners: scoring system, output format, error taxonomy, log format, agent coding standards |

## Configuration

**.env Variables:**
- `MODEL_API_BASE_URL` - OpenRouter endpoint
- `MODEL_API_KEY` - API key
- `MODEL_MAX_TOKENS` - Base token limit (8192)
- `MODEL_TEMPERATURE` - Sampling temperature (0.7)
- `MODEL_API_TIMEOUT` - Per-request timeout for OpenRouter API calls in seconds (600)
- `MAX_WORKERS` - Concurrency limit for agent generation
- `NUM_RUNS` - Default agent runs per model/game
- `NUM_OF_GAMES_IN_A_MATCH` - Games per match pairing

**config/models.txt:** One model per line. All non-empty lines are treated as active models. (The `!` prefix to disable models was removed; see commit `27748a8`.)

## Games Overview

| ID | Game | Players | Status |
|----|------|---------|--------|
| A1 | Battleship | 2 | Playable |
| A2 | LieOnce | 2 | Playable |
| A3 | Wizard | 6 | Playable |
| A4 | Backgammon | 2 | Playable |
| A5 | Connect4RandomStart | 2 | Playable |
| A6 | WordMatrixGame | 2 | Playable |
| A7 | TwoByEightChess | 2 | Playable |
| A8 | SurroundMorris | 2 | Playable |

---

## Game Details

### A8: Surround Morris

**Type:** 2-player competitive board game
**Match File:** `game_scripts/A8-surround_morris_match.py`
**Game Prompt:** `games/A8-SurroundMorris.txt`
**Scoreboard:** `scoreboard/A8-scoreboard.txt`

#### Overview

Nine Men's Morris variant where capture uses spatial surrounding instead of mill formation. Players place and move pieces on a 24-spot board, attempting to surround opponent pieces using the "overwhelm" capture rule.

#### Board Structure

24 spots arranged in three concentric squares with connecting lines:
```
 0----------1----------2
 |           |           |
 |   3-------4-------5   |
 |   |       |       |   |
 |   |   6---7---8   |   |
 |   |   |       |   |   |
 9---10--11      12--13--14
 |   |   |       |   |   |
 |   |   15--16--17  |   |
 |   |       |       |   |
 |   18------19------20  |
 |           |           |
 21----------22----------23
```

**Adjacency:** Each spot connects only to directly adjacent spots (horizontal/vertical lines). See `ADJACENCY` dict in code for complete mapping.

#### Game Phases

**1. Placement Phase**
- Each player starts with 7 pieces in hand (reduced from traditional 9)
- Players alternate placing one piece per turn on any empty spot
- Black (B) moves first
- Phase ends when both players have placed all 7 pieces

**2. Movement Phase**
- Players alternate moving one piece to an adjacent empty spot
- No flying (must move along board lines)
- Continues until game end condition met

#### Capture Mechanics: The "Overwhelm" Rule

A piece is captured when it satisfies BOTH conditions:
1. **Zero empty neighbors** (completely surrounded)
2. **More opponent neighbors than friendly neighbors**

**Capture Timing:** After every move (placement or movement), a two-pass capture sweep occurs:
1. **Self-harm priority:** Remove mover's captured pieces first
2. **Enemy capture:** Re-check opponent pieces (may gain empty neighbors from step 1)

**Suicide Moves:** Placing/moving into a captured position immediately removes your own piece.

#### Win/Draw Conditions

**Win by Elimination:**
- Opponent has 0 pieces on board AND 0 pieces in hand
- Self-harm priority: mover checked first for elimination

**Win by Mate:**
- Opponent has no legal moves at start of their turn
- Scored as +7/-7 (winner/loser)

**Draw by Repetition:**
- Same board state + current player occurs 3 times
- Checked before move execution

**Draw by Turn Limit:**
- 200 movement turns reached (configurable: `MAX_TURNS_PER_GAME`)
- Checked after move execution

#### Scoring System (Football League Style)

**Points (Primary Ranking Metric):**
- Win = 3 points
- Draw = 1 point
- Loss = 0 points

**Score (Tiebreaker, Goal Difference):**
- **Normal Win:** Winner gets +pieces_on_board, loser gets -pieces_on_board
- **Mate Win:** Winner gets +7, loser gets -7
- **Draw:** Each player gets +(total_pieces_on_board / 2.0)

**Example:** Agent wins 5-2 elimination → +3 points, +5 score. Loser → 0 points, -5 score.

#### Leaderboard

**File:** `scoreboard/A8-scoreboard.txt`

**Format:**
```
Agent | Games | Wins | Losses | Draws | Points | Score
```

**Sorting:** Primary by Points (descending), tiebreaker by Score (descending)

**Update Logic:** Atomic file-locking via `utils/scoreboard.py:update_scoreboard()` using `fcntl.flock`. A sibling `.lock` file (e.g., `A8-scoreboard.lock`) is created during writes and persists if a process crashes — safe to delete manually if no matches are running. Backward-compatible with legacy 6-column format; missing Points column defaults to 0.

#### Code Architecture

**Embedded Subprocess Model:**

The match runner uses a multi-layer architecture:

1. **Outer Layer (`main_async`):**
   - CLI argument parsing
   - Agent discovery and loading
   - Match orchestration (parallel via `asyncio.gather`)
   - Result aggregation and logging
   - Scoreboard updates

2. **Middle Layer (`run_match`):**
   - Generates temporary Python file with embedded code
   - Spawns subprocess with 600s timeout
   - Parses stdout for structured results (`RESULT:`, `POINTS:`, `WINS:`, `DRAWS:`)
   - Returns result dict

3. **Inner Layer (Embedded `MATCH_RUNNER_CODE`):**
   - Executed inside subprocess
   - Runs `NUM_GAMES_PER_MATCH` games (default 100)
   - Tracks match statistics (wins, points, scores, errors)
   - Emits structured output lines for outer parsing

**Code Modules:**

| Module | Location | Purpose |
|--------|----------|---------|
| `GAME_ENGINE_CODE` | Lines 62-309 | `SurroundMorrisGame` class, adjacency map, board logic |
| `MATCH_RUNNER_CODE` | Lines 315-722 | `play_game()`, `main()`, timeout handling, stats tracking |
| `HUMAN_PLAY_CODE` | Lines 728-1003 | Human vs Bot/Human/Agent interactive mode |

**Agent Interface:**

Generated agents must implement:
```python
class SurroundMorrisAgent:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'B' or 'W'

    def make_move(self, state: dict, feedback: dict | None):
        # Placement phase: return int (spot 0-23)
        # Movement phase: return tuple (from_spot, to_spot)
```

**State Dictionary:**
```python
{
    "board": list[str],           # 24 elements: '', 'B', or 'W'
    "phase": str,                 # 'placement' or 'movement'
    "your_color": str,            # 'B' or 'W'
    "opponent_color": str,        # 'W' or 'B'
    "pieces_in_hand": dict,       # {'B': int, 'W': int}
    "pieces_on_board": dict,      # {'B': int, 'W': int}
    "move_count": int,            # Movement turns elapsed
    "history": list[tuple],       # (board_state, current_player) history
}
```

**Feedback Dictionary (on invalid move):**
```python
{
    "error_code": str,            # "INVALID_SPOT_OOB", "INVALID_OUTPUT", etc.
    "error_message": str,         # Human-readable description
    "attempted_move": Any,        # What agent returned
    "attempt_number": int,        # 1, 2, or 3
}
```

#### Constants and Configuration

**Environment Variables:**
- `NUM_OF_GAMES_IN_A_MATCH` (default: 100) — Base games per match pairing; A8 divides this by 10 (effective default: 10 games per match) to keep match durations reasonable given board evaluation overhead
- `MAX_TURNS_PER_GAME` (default: 200) — Movement phase turn limit
- `MOVE_TIME_LIMIT` (default: 1.0s) — Per-move timeout

**Hardcoded:**
- Pieces per player: 7
- Max placement/movement attempts: 3 (fallback to random)
- Board size: 24 spots

**Error Handling:**
- Invalid moves: Agent gets feedback, max 3 attempts, then random fallback
- Timeouts: Random fallback
- Crashes: Random fallback
- All errors tracked in match statistics (printed at end)

#### File Locations

**Results:**
- Match logs: `results/surround_morris/<timestamp>_<agent1>_vs_<agent2>_match.txt`
- Global scoreboard: `scoreboard/A8-scoreboard.txt`

**Agents:**
- Generated agents: `agents/<model_folder>/A8-SurroundMorris_<run>.py`

#### Running Matches

**Single match (2 agents):**
```bash
uv run game_scripts/A8-surround_morris_match.py --agent model1:1 model2:2
```

**Human play modes:**
```bash
uv run game_scripts/A8-surround_morris_match.py --humanvsbot       # vs random
uv run game_scripts/A8-surround_morris_match.py --humanvshuman    # local 2P
uv run game_scripts/A8-surround_morris_match.py --humanvsagent --agent model:1
```

**Tournament (all cross-model pairings):**
```bash
uv run game_scripts/matchmaker.py --game A8 --same_opponent_match 4 --workers 4
```

#### Match Output Format

**Subprocess stdout includes:**
```
RESULT:Agent-1=<score1>,Agent-2=<score2>
POINTS:Agent-1=<pts1>,Agent-2=<pts2>
WINS:Agent-1=<wins1>,Agent-2=<wins2>
DRAWS:<draw_count>
--- MATCH STATISTICS ---
Agent-1 Crashes: <count>
Agent-2 Crashes: <count>
Agent-1 Captures: <count>
Agent-2 Captures: <count>
Agent-1 Stalemates: <count>
Agent-2 Stalemates: <count>
Total Turns: <count>
```

**Outer layer parses these lines** via regex to populate result dict and update scoreboard.

---

### A1: Battleship

**Type:** 2-player naval strategy
**Match File:** `game_scripts/A1-battleship_match.py`
**Game Prompt:** `games/A1-Battleship.txt`
**Scoreboard:** `scoreboard/A1-scoreboard.txt`

**Overview:** Classic Battleship on an 8x8 grid. Ships: [5, 4, 3]. Two phases — placement then bombing. Players call shots until all opponent ships are sunk.

**Agent Interface:** `class BattleshipAgent` with `place_ships(board_size, ships)` returning placement coordinates and `make_move(state, feedback)` returning a target cell.

**Scoring:** Winner gets +remaining_ship_cells, loser gets -remaining_ship_cells.

**Human modes:** `--humanvsbot`, `--humanvshuman`, `--humanvsagent --agent model:1`

---

### A2: LieOnce

**Type:** 2-player number-guessing game with bluffing
**Match File:** `game_scripts/A2-lie_once_match.py`
**Game Prompt:** `games/A2-LieOnce.txt`
**Scoreboard:** `scoreboard/A2-scoreboard.txt`

**Overview:** Each player picks a hidden integer in [1, 100]. Players alternate guessing the opponent's number; the responder must answer "Up", "Down", or "Correct". Each player may lie at most ONCE per game, AND only on their first 10 responses (response 11+ cannot be a lie). A guess wins only when it is genuinely correct AND the responder confirms with "Correct"; if the responder lies and says "Up"/"Down", the lie is consumed and play continues.

**Agent Interface:** `class LieOnceAgent` with three methods:
- `pick_number() -> int` — called once at game start, must return integer in [1, 100].
- `guess(state: dict) -> int` — return integer guess. Non-integer = lose turn; out-of-range integer is legal.
- `respond(state: dict, opponent_guess: int) -> str` — return one of `"Up"`, `"Down"`, `"Correct"`. Anything else = forfeit; second lie = forfeit; lie on response ≥ 11 = forfeit.

**State dict** (passed to both `guess` and `respond`):
```python
{
    "your_number": int,
    "your_lie_used": bool,
    "your_response_count": int,  # responses given so far (lies only legal while < 10)
    "turn": int,                 # 1-indexed combined turn number
    "you_started": bool,
    "is_tie_attempt": bool,
}
```
Agents see ONLY their own state. The runner does not replay history — agents track their own.

**Tie-Attempt:** If the starter wins on turn N (N < 100), the non-starter gets one final guess on turn N+1. Starter responds. If non-starter's guess is genuinely correct AND starter says "Correct" truthfully → DRAW. If starter lies (says "Up"/"Down" with lie still available), the lie is consumed and starter wins (the lie acts as a joker to deny the tie). Second-lie or invalid response in tie → starter forfeits, non-starter wins.

**Starter alternation:** Agent-1 starts game 1, Agent-2 starts game 2, alternating thereafter. Over 100 games each agent starts equally often.

**Scoring:**
- Win = 3 points; tiebreaker score = `100 - winner_guess_count`.
- Loss = 0 points; tiebreaker score = `-(100 - winner_guess_count)`.
- Draw (turn cap or successful tie-attempt) = 1 point each, score 0.
- Forfeit before any guess (e.g. invalid `pick_number`) gives the opponent the maximum score of 100.

**Total turn cap:** 100 combined turns. A non-integer guess still consumes a turn (no feedback exchanged).

**Error Handling:**
- `pick_number` non-integer / out-of-range / crash / timeout → immediate forfeit, opponent score = 100.
- `guess` non-integer / crash / timeout → lose turn (no feedback exchanged); play passes to opponent.
- `respond` invalid string / crash / timeout / second lie → immediate forfeit, opponent treated as having guessed correctly on this turn.

**Game count:** Loads `NUM_OF_GAMES_IN_A_MATCH` directly (no division). Default 100 games per match.

**Human mode:** `--humanvsbot` plays interactively against a random bot.

---

### A3: Wizard

**Status: Playable.**

---

### A4: Backgammon

**Type:** 2-player race game
**Match File:** `game_scripts/A4-backgammon_match.py`
**Game Prompt:** `games/A4-Backgammon.txt`
**Scoreboard:** `scoreboard/A4-scoreboard.txt`

**Overview:** Standard backgammon on a 24-point board. 15 checkers per player, two six-sided dice. White moves toward index 0; Black moves toward index 23. Each subprocess invocation plays one **race-to-5 in-game points**: Single Win = 1 point, Gammon Win = 2 points, turn-limit Draw = 0.5 each. Match (race) caps at `MAX_GAMES_PER_MATCH = 30` for safety. No doubling cube. No Backgammon (3-point) tier.

**Agent Interface:** `class BackgammonAgent` with `make_move(state, feedback)` returning a list of `(from, to)` sub-move tuples. State includes pre-computed `legal_sub_moves` (single-step) and `max_dice_usable` (target sequence length); the returned sequence length must equal `max_dice_usable` exactly.

**Scoring:**
- In-game (per game): Single = 1, Gammon = 2, Draw (turn limit) = 0.5/0.5.
- League (per match): Match Win (first to 5) = 3 points, Match Draw = 1 each, Match Loss = 0.
- Tie-break score = ±(in-game-points diff). E.g., 5–1 in-game → +4/-4.

**Constants (hardcoded):** `MAX_TURNS_PER_GAME = 300`, `POINTS_TO_WIN_MATCH = 5`, `MAX_GAMES_PER_MATCH = 30`. The framework's `NUM_OF_GAMES_IN_A_MATCH` env var is ignored — game count is variable per race.

**Error handling (project deviation):** Crashes, timeouts, AND invalid moves all forfeit the turn — no random fallback. The turn counter still increments. Stats track each failure mode separately (`make_move_crash`, `timeout`, `invalid`).

**Forced-use rule:** Agents must use as many dice as legally possible. The "must play larger die" sub-rule is NOT enforced — if both dice are individually playable but not together, agent picks either.

**Color/turn assignment:** Within each game, White is randomly determined; turn order alternates by color across games (Agent-1 is W in odd-numbered games, B in even).

**Human modes:** `--humanvsbot`, `--humanvshuman`, `--humanvsagent --agent model:1`

**Subprocess output extras:** `GAMES_PLAYED:<int>` line is parsed by the outer layer for scoreboard `games_played` (variable per match).

---

### A5: Connect4 (Random Start)

**Type:** 2-player connection game
**Match File:** `game_scripts/A5-connect4_match.py`
**Game Prompt:** `games/A5-Connect4RandomStart.txt`
**Scoreboard:** `scoreboard/A5-scoreboard.txt`

**Overview:** Standard Connect4 on a 6x7 board with one twist: one disc is pre-placed at a random column before each match to break standard opening theory. Colors alternate between odd/even games.

**Agent Interface:** `class Connect4Agent` with `make_move(state, feedback)` returning a column index (0–6).

**Scoring:** Score = empty cells remaining at win (min 3). Forfeit score: 41 cells.

**Game count:** Loads `NUM_OF_GAMES_IN_A_MATCH` from the environment and divides by 10. Effective default: 10 games per match.

**Human mode:** `--human` plays interactively against a random bot.

---

### A6: WordMatrixGame

**Type:** 2-player word path game
**Match File:** `game_scripts/A6-word_matrix_match.py`
**Game Prompt:** `games/A6-WordMatrixGame.txt`
**Scoreboard:** `scoreboard/A6-scoreboard.txt`

**Overview:** 4x4 letter grid. Each turn a player traces a path through adjacent cells (min 2) to form a valid word. Matched cells are cleared and replaced with new letters. 6 consecutive passes end the game.

**Agent Interface:** `class WordMatrixAgent` with `make_move(state, feedback)` returning a list of cell indices forming the path.

**Scoring:** 10 base + 10 per cleared cell per word. Invalid move penalty: -10 (no fallback to random). Forfeit score: 12.

**Human modes:** `--humanvsbot`, `--humanvshuman`, `--humanvsagent --agent model:1`

---

### A7: 2x8 Mini Chess

**Type:** 2-player abstract chess variant
**Match File:** `game_scripts/A7-twobyeight_chess_match.py`
**Game Prompt:** `games/A7-TwoByEightChess.txt`
**Scoreboard:** `scoreboard/A7-scoreboard.txt`

**Overview:** Chess played on a 2x8 board. Each side starts with King, Knight, Rook, and Pawn. Pawns promote to Rook upon reaching the far edge. Knight movement is modified (L-shape + 2-step linear). Full chess rules: check, checkmate, stalemate, repetition draw, insufficient material draw. Move limit: 200.

**Agent Interface:** `class TwoByEightChessAgent` with `make_move(state, feedback)` returning a move in UCI notation (e.g. `"a1b1"`).

**Scoring:** Win in ≤5 full moves = +10, ≤10 = +5, >10 = +3. Draw = 0 for both. 100 games per match.

**Human mode:** `--human` plays interactively against a random bot.

---

## Agent File Convention

Generated agents saved to: `agents/<sanitized_model_name>/<game_id>_<run_id>.py`

Example: `agents/openai-gpt-5-mini/A1-Battleship_1.py`

**Model name sanitization** (`utils/populate_agents.py:sanitize_model_name()`): Converts an OpenRouter model ID into a valid folder name.
1. Strip everything after `@` (preset/flavor suffix removed)
2. If the third path segment exists and is not already part of the base name, append it with a hyphen
3. Replace `/` with `-`
4. Replace remaining invalid filesystem characters with `_`

Example: `deepseek/deepseek-v3@preset/fp8` → `deepseek-deepseek-v3-fp8`

**Run ID collision avoidance**: `get_next_run_ids()` scans existing files for the highest run number already present and allocates from `max + 1` onward. Re-running `populate_agents.py` for a model that already has runs will never overwrite them.

**Interactive model resolution**: When `--model <substring>` matches multiple entries in `models.txt`, the CLI presents a numbered menu and prompts the user to select. The command does not silently pick one or fail.

## Matchmaker (Tournament Scheduler)

`game_scripts/matchmaker.py` automates full round-robin tournament execution across all agents for a given game. It discovers agents, generates cross-model fixtures, and runs them concurrently as subprocesses — each delegated to the appropriate game match runner.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `--game` | str | required | Game ID: A1 through A8 |
| `--same_opponent_match` | int | 2 | Minimum encounters per cross-model agent pair (see below) |
| `--workers` | int | 16 | Max concurrent match subprocesses |
| `--dry-run` | flag | false | Print fixture list without executing |
| `--new-model` | str | — | Comma-separated model folder names; restrict fixtures to those involving these models |
| `--health` | flag | false | Run syntax + broad-except checks on all agents before execution |

**How `--same_opponent_match` works:**

This controls how many times every cross-model agent pair is guaranteed to encounter each other. Each cross-model pair plays a head-to-head match `same_opponent_match` times. With 20 models x 2 runs = 40 agents, there are 760 cross-model pairs, so `--same_opponent_match 4` produces 3040 matches.

**Incremental tournaments (`--new-model`):** When new models are added, pass their folder names (comma-separated) to generate only the fixtures where at least one side is a new model. Avoids replaying all existing cross-model pairs.

**Agent health checks (`--health`):** Before executing, validates every discovered agent for:
1. Syntax validity (`ast.parse`).
2. Broad exception handlers in `make_move` (`except Exception`, `except BaseException`, bare `except:`) — these swallow `MoveTimeoutException` and disable per-move time limits.

**Agent discovery:** Scans `agents/*/` for files matching `{game_name}_{run}.py`. Only cross-model pairings are generated — agents from the same model folder never face each other.

**Execution:** Each match is a subprocess calling the game's match runner with `--update-scoreboard` appended automatically. The match runner handles game execution, result parsing, scoreboard updates, and log writing internally. The matchmaker only orchestrates scheduling and reports success/failure counts.

**Game-count scaling:** A5, A7, and A8 match runners divide `NUM_OF_GAMES_IN_A_MATCH` by 10 internally, yielding 10 games per match by default rather than 100. This compensates for slower per-game execution (complex board evaluation in A7/A8).

**Timeout:** 900 seconds per match subprocess. Timed-out matches are killed and recorded as failures.

## Agent Enhancement

`utils/try_enhancing_agents.py` automates iterative improvement of agent quality. For each selected model/game combo, it:

1. Generates 1 new agent (using the same `prompt_model` / `extract_agent_code` pipeline as `populate_agents.py`)
2. Runs same-model matches with 10x the base game count (e.g. 1000 games instead of 100)
3. Evaluates performance based on match points
4. Prunes the worst agent (new or existing) and renames files to keep run IDs contiguous

**Architecture:** Fully pipelined. All combos run concurrently via `asyncio.gather`. Each combo independently populates → matches → evaluates → prunes. API calls share a semaphore (`MAX_WORKERS`). Match subprocesses share a separate semaphore (capped at 24).

**Worst agent determination:**
- New agent lost to all existing → delete new agent
- New agent beat all existing → run additional old-vs-old matches to find worst existing
- Mixed results → worst is the agent that lost to the new agent with fewest points

**Constraints:**
- Only 2-player games (A3/6-player is excluded automatically)
- Requires ≥ 2 existing agents per model/game combo
- Enhancement matches do not update scoreboards (`--update-scoreboard` is not passed)

**Biweekly cycle:** Every two weeks, all models across all games go through enhancement. This accounts for upstream API model changes (weight updates, quantization tweaks) and eliminates luck from one-shot code generation.

## Development Notes

- Match runners execute agents in subprocesses with 1s move timeout (configurable via `MOVE_TIME_LIMIT`)
- Invalid moves, timeouts, crashes fallback to random valid moves
- Game logs track per-agent error statistics
- Agent code injection uses class renaming to avoid conflicts
