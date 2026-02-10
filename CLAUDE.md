# Competitive LLM Agents

Benchmarking framework for evaluating LLMs in competitive multi-agent game environments. Generates agent implementations via OpenRouter API and orchestrates head-to-head/multiplayer matches.

## Project Structure

```
agents/           # Generated agent code (organized by model name)
config/           # Configuration: models.txt, max_tokens.txt
games/            # Game prompts/rules (A1-Battleship, A2-TicTacToe, A3-Wizard, A4-WordFinder)
results/          # Match logs and outcomes
utils/            # Core logic - API client, match runners, agent generation
```

## Entry Points

**Agent Generation:**
```bash
uv run python utils/populate_agents.py --all                    # All models, all games
uv run python utils/populate_agents.py --model mistral gpt      # Specific models
uv run python utils/populate_agents.py --games A1,A3 --runs 3   # Specific games
```

**Running Individual Matches:**
```bash
uv run python game_scripts/A1-battleship_match.py --agent model1:1 model2:1
uv run python game_scripts/A2-tictactoe_match.py --agent model1:1:2 model2:1
uv run python game_scripts/A3-wizard_match.py --agent model1:1 model2:1 model3:1
uv run python game_scripts/A4-word_finder_match.py --agent model1:1 model2:1
uv run python game_scripts/A6-word_matrix_match.py --agent model1:1 model2:1
uv run python game_scripts/A6-word_matrix_match.py --human
uv run python game_scripts/A8-surround_morris_match.py --agent model1:1 model2:1
```

**Running Tournaments (Matchmaker):**
```bash
uv run python game_scripts/matchmaker.py --game A8 --same_opponent_match 4
uv run python game_scripts/matchmaker.py --game A8 --same_opponent_match 1 --dry-run
uv run python game_scripts/matchmaker.py --game A3 --same_opponent_match 2 --workers 8
```

## Key Modules

| File | Purpose |
|------|---------|
| `utils/model_api.py` | Async OpenRouter API client with token multipliers |
| `utils/populate_agents.py` | LLM-based agent code generation |
| `game_scripts/*_match.py` | Game-specific match orchestrators |
| `game_scripts/matchmaker.py` | Round-robin tournament scheduler |
| `utils/logging_config.py` | Centralized logging setup |

## Configuration

**.env Variables:**
- `MODEL_API_BASE_URL` - OpenRouter endpoint
- `MODEL_API_KEY` - API key
- `MODEL_MAX_TOKENS` - Base token limit (16384)
- `MODEL_TEMPERATURE` - Sampling temperature (0.7)
- `MAX_WORKERS` - Concurrency limit for agent generation
- `NUM_RUNS` - Default agent runs per model/game
- `NUM_OF_GAMES_IN_A_MATCH` - Games per match pairing

**config/models.txt:** One model per line. Prefix with `!` to disable.

**config/max_tokens.txt:** Token multipliers per game (e.g., `A1: 4` = 4x base tokens).

## Games Overview

| ID | Game | Players | Status |
|----|------|---------|--------|
| A1 | Battleship | 2 | Playable |
| A2 | TicTacToe | 2 | Playable |
| A3 | Wizard | 6 | Playable |
| A4 | WordFinder | 2 | Playable |
| A6 | WordMatrixGame | 2 | Playable |
| A8 | SurroundMorris | 2 | Playable |
| A5,A7 | (Placeholders) | - | Not implemented |

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

**Update Logic:** Atomic file-locking via `utils/scoreboard.py:update_scoreboard()`. Backward-compatible with legacy 6-column format (points default to 0).

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
- `NUM_OF_GAMES_IN_A_MATCH` (default: 100) — Games per match pairing
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
- Match logs: `results/surround_morris/game_logs/<timestamp>_match.txt`
- Global scoreboard: `scoreboard/A8-scoreboard.txt`

**Agents:**
- Generated agents: `agents/<model_folder>/A8-SurroundMorris_<run>.py`

#### Running Matches

**Single match (2 agents):**
```bash
uv run python game_scripts/A8-surround_morris_match.py --agent model1:1 model2:2
```

**Human play modes:**
```bash
uv run python game_scripts/A8-surround_morris_match.py --humanvsbot       # vs random
uv run python game_scripts/A8-surround_morris_match.py --humanvshuman    # local 2P
uv run python game_scripts/A8-surround_morris_match.py --humanvsagent --agent model:1
```

**Tournament (all cross-model pairings):**
```bash
uv run python game_scripts/matchmaker.py --game A8 --same_opponent_match 4 --workers 4
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
*Details to be added*

### A2: TicTacToe
*Details to be added*

### A3: Wizard
*Details to be added*

### A4: WordFinder
*Details to be added*

### A6: WordMatrixGame
*Details to be added*

---

## Agent File Convention

Generated agents saved to: `agents/<sanitized_model_name>/<game_id>_<run_id>.py`

Example: `agents/openai-gpt-5-mini/A1-Battleship_1.py`

## Matchmaker (Tournament Scheduler)

`game_scripts/matchmaker.py` automates full round-robin tournament execution across all agents for a given game. It discovers agents, generates cross-model fixtures, and runs them concurrently as subprocesses — each delegated to the appropriate game match runner.

**Arguments:**

| Argument | Type | Default | Description |
|---|---|---|---|
| `--game` | str | required | Game ID: A1 through A8 |
| `--same_opponent_match` | int | 1 | Minimum encounters per cross-model agent pair (see below) |
| `--workers` | int | 4 | Max concurrent match subprocesses |
| `--dry-run` | flag | false | Print fixture list without executing |

**How `--same_opponent_match` works:**

This controls how many times every cross-model agent pair is guaranteed to encounter each other.

- **2-player games (A1, A2, A4-A8):** Each cross-model pair plays a head-to-head match `same_opponent_match` times. With 20 models x 2 runs = 40 agents, there are 760 cross-model pairs, so `--same_opponent_match 4` produces 3040 matches.

- **6-player games (A3 Wizard):** There is no head-to-head; instead, 6 agents from 6 different models share a table. The matchmaker uses a greedy pairwise-coverage algorithm to generate groups such that every cross-model agent pair co-occurs in at least `same_opponent_match` games. This ensures sufficient statistical signal to compare any two models even in a multiplayer setting.

**Agent discovery:** Scans `agents/*/` for files matching `{game_name}_{run}.py`. Only cross-model pairings are generated — agents from the same model folder never face each other.

**Execution:** Each match is a subprocess calling the game's match runner (e.g. `A8-surround_morris_match.py --agent modelA:1 modelB:2`). The match runner handles game execution, result parsing, scoreboard updates, and log writing internally. The matchmaker only orchestrates scheduling and reports success/failure counts.

**Timeout:** 900 seconds per match subprocess. Timed-out matches are killed and recorded as failures.

## Development Notes

- Match runners execute agents in subprocesses with 1s move timeout (3s for WordFinder)
- Invalid moves, timeouts, crashes fallback to random valid moves
- Game logs track per-agent error statistics
- Agent code injection uses class renaming to avoid conflicts
