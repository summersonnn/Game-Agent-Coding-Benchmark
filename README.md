# Competitive LLM Agent Benchmark

Benchmarking framework for evaluating LLMs in competitive multi-agent game environments. Generates agent implementations via OpenRouter API and orchestrates head-to-head/multiplayer matches.

Models produce code that can play games rather than playing the games themselves. Their sole interaction occurs at the stage of code creation. As a result, this benchmark is hybrid in nature, combining elements of both code generation and reasoning.

The [published league website](https://gameagentcodingleague.com/) is maintained
separately and may describe an earlier roster or methodology. The code and
configuration in this repository define the current eight-game benchmark.

## Features

- **8 Competitive Games**: Battleship, LieOnce, Wizard, Backgammon, Connect4, WordMatrix, Mancala, SurroundMorris.
- **Model-Agnostic**: OpenRouter integration supports any available LLM.
- **Persistent Agents**: Generated code stored per-model for reuse and analysis.
- **Points-Based Scoring**: All matches, except for the A3 game, follow the standard scoring format: a win earns 3 points, a draw earns 1 point, and a loss earns 0 points, with goal difference used to break ties.
The A3 game uses a different approach — there are no win, loss, or draw outcomes. Instead, the six agents are ranked from first to last: the top agent receives 5 points, the second earns 4 points, and the points continue decreasing by one down to 0 points for the last-place agent.
- **Tournament Automation**: Round-robin matchmaker with configurable concurrency.

---

## Getting Started

### Prerequisites

- Python 3.12+ and [uv](https://github.com/astral-sh/uv) on Linux or macOS. Match runners use POSIX signals and file locking.
- An API key for generating or enhancing agents. Running saved agents needs no API key.

### Installation

```bash
git clone <repo>
cd Competitive-LLM-Agents
uv sync
```

### Configuration

Create a `.env` file:

```
MODEL_API_KEY=your_openrouter_api_key
MODEL_API_BASE_URL=https://openrouter.ai/api/v1
MODEL_MAX_TOKENS=16384
MODEL_TEMPERATURE=0.7
MAX_WORKERS=16
NUM_RUNS=2
A1_GAMES_PER_MATCH=20
A2_GAMES_PER_MATCH=50
A3_GAMES_PER_MATCH=24
A3_QUALIFIER_GAMES_PER_MATCH=402
A3_MAIN_EVENT_GAMES_PER_MATCH=6
A4_MAX_GAMES_PER_MATCH=30
A5_GAMES_PER_MATCH=10
A6_GAMES_PER_MATCH=10
A7_GAMES_PER_MATCH=12
A8_GAMES_PER_MATCH=20
```

`config/models.txt` lists the 12 current model names, matching the folder names
under `agents/` exactly. Each model currently has two agents for each of the
eight games (192 agent files total).

Population and enhancement send each configured name unchanged to
`MODEL_API_BASE_URL` (OpenRouter by default). The saved agents do not record
provider API IDs, so use an endpoint that accepts these names or supply the
correct API identifiers before generating agents. These names alone do not
verify API availability. The tournament scheduler discovers saved agents
directly from `agents/`.

Each game reads its own match count directly. Missing, invalid, or non-positive
counts use that game's default from `utils/game_config.py`. Backgammon plays
until an agent reaches five points, subject to its configured game cap.

Match sizes account for draws, randomness, and opening/seat coverage. LieOnce
gets 50 games because its tie-attempt rule can draw between similar strategies;
Battleship gets 20 to sample hidden placements and search luck. Connect4 and
Word Matrix get 10 each to sample random openings or boards. Mancala gets 12:
six pairs of games with seats swapped and a shared opening within each pair.
Openings are sampled with replacement, so six pairs do not guarantee all six
possible openings appear. Surround Morris gets 20 to average stochastic play;
deterministic agents still replay the same two games with seats swapped.
Extra games cannot resolve deterministic draws or compensate for restrictive
turn/time limits. These counts are starting budgets, not measured precision
guarantees for the current agents.

The two-player matchmaker repeats each agent pairing eight times by default
(`--same_opponent_match 8`). This yields 160 Battleship, 400 LieOnce, 80
Connect4, 80 Word Matrix, 96 Mancala, and 160 Surround Morris games per agent
pairing. Backgammon gets eight races to five points; its cap of 30 is a safety
limit, and current scoring ends each race within ten completed games.

Wizard's tournament has two phases. Qualifiers seat both agents from each of
three models at a six-player table and select the higher-scoring agent from
each model. The main event seats those representatives in every combination of
six models. With 12 models, that is four qualifier tables and 924 main-event
tables. At the default counts, that is 1,608 qualifier games and 5,544
main-event games; each representative plays 2,772 games across 462 main-event
tables. A Wizard game includes all 10 card rounds. The phase settings above
control games per table
directly, while `A3_GAMES_PER_MATCH` controls direct match-runner invocations.
The tournament requires at least six models and exactly two agents per model.
Use `--dry-run` to see table counts, games per table, and total games before
starting. Seating rotates across games within each table. The defaults of 24
direct-match games, 402 qualifier games, and six main-event games are all
multiples of six, giving every agent equal time in every seat at its table.

The sample configuration uses two runs per model/game for a fresh Wizard
roster. Population appends new runs; generating more Wizard agents for an
existing model will exceed the tournament's requirement of exactly two.

---

## Step 1: Generate Agents

`utils/populate_agents.py` prompts LLMs to generate agent implementations and saves them under `agents/`.

```bash
# All active models, all games
uv run utils/populate_agents.py --all

# Specific models by substring
uv run utils/populate_agents.py --model Terra Opus

# Filter to specific games
uv run utils/populate_agents.py --game A1,A8

# Override run count
uv run utils/populate_agents.py --all --runs 2

# Interactive model selection (no args)
uv run utils/populate_agents.py
```

**Model selection rules:**
- `--model Terra` matches `GPT-6.1-Terra-Extrahigh` (case-insensitive).
- If a substring matches multiple models, an interactive prompt resolves the ambiguity.

**Output:** `agents/<sanitized_model_name>/<game_name>_<run>.py`, for example
`agents/GPT-6.1-Terra-Extrahigh/A1-Battleship_1.py`.

Run IDs are appended automatically — existing agents are never overwritten.

---

## Step 2: Run Matches

Match scripts load pre-generated agents from `agents/` and run a series of games between them.

### Agent Spec Format

```
model_pattern[:run1:run2:...]
```

- `model_pattern`: substring matched against folder names inside `agents/`.
- `run1:run2...`: optional, specific run numbers. If omitted, all available runs are used.

This format applies to two-player games. Wizard requires six `MODEL:RUN`
arguments with one explicit run per player. Direct two-player runners pair
their run lists by position; the matchmaker generates all cross-model pairings.

All match scripts require `--agent` for agent-vs-agent mode. Human play modes (`--humanvsbot`, `--humanvshuman`, `--humanvsagent`) are available in most scripts but not all games support them — check the per-game details below.

---

### A1: Battleship

2-player, 8x8 grid. Ships: [5, 4, 3]. Placement phase then bombing phase.

```bash
# Agent vs agent
uv run game_scripts/A1-battleship_match.py --agent Terra:1 Opus:1

# Human modes
uv run game_scripts/A1-battleship_match.py --humanvsbot
uv run game_scripts/A1-battleship_match.py --humanvshuman
uv run game_scripts/A1-battleship_match.py --humanvsagent --agent Terra:1
```

> **Note:** Running matches directly like this does **not** affect scoreboards. The `--update-scoreboard` flag defaults to `false`, so this is safe to use for testing agents without polluting the leaderboard.

---

## Step 3: Run Tournaments

`game_scripts/matchmaker.py` automates round-robin tournaments. It discovers all agents for a game, generates cross-model fixtures, and runs them concurrently as subprocesses.

```bash
# Full tournament for SurroundMorris, each cross-model pair plays 4 times
uv run game_scripts/matchmaker.py --game A8 --same_opponent_match 4

# Preview fixtures without executing
uv run game_scripts/matchmaker.py --game A8 --dry-run

# Only run matches involving newly added models (incremental update)
uv run game_scripts/matchmaker.py --game A8 --new-model GPT-6.2-Astra-Extrahigh

# Verify agent syntax before running
uv run game_scripts/matchmaker.py --game A8 --health
```

### Matchmaker Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `--game` | str | required | Game ID: A1, A2, A3, A4, A5, A6, A7, A8 |
| `--same_opponent_match` | int | 8 | Exact match repetitions for each two-player agent pair |
| `--workers` | int | 24 | Max concurrent match subprocesses |
| `--dry-run` | flag | false | Preview schedule size and match settings without executing |
| `--new-model` | str | — | Two-player games: comma-separated model folder names; only generate fixtures involving these models |
| `--health` | flag | false | Run syntax + exception-handler checks on all agents before execution |
| `--random16` | flag | false | Sample up to 16 two-player fixtures |
| `--mini` | flag | false | Run a two-player mini league including same-model pairs; requires `--agent` |
| `--agent` | list | — | Mini league participants as `MODEL:RUN` specs, or one model substring to use all its agents |
| `--auto-yes` | flag | false | Skip Wizard's confirmation between qualifiers and main event |

### How `--same_opponent_match` Works

For two-player games, every cross-model agent pair plays a direct match `N`
times. The current 12 models × 2 runs = 24 agents produce 264 cross-model
pairings; `--same_opponent_match 4` schedules 1,056 matches. Wizard uses its
qualifier and main-event phases, with independent games-per-table settings.

### Incremental Tournaments (`--new-model`)

For two-player games, use `--new-model` to schedule only fixtures involving
the specified model folders. Wizard's separate tournament path does not apply
this filter.

```bash
uv run game_scripts/matchmaker.py --game A8 --new-model GPT-6.2-Astra-Extrahigh,Sonnet-5.5-Max
```

### Agent Health Checks (`--health`)

Before executing a tournament, `--health` validates every agent:
1. **Syntax check** — parses each file with `ast.parse`.
2. **Broad except in `make_move`** — detects `except Exception`, `except BaseException`, or bare `except:` at the top level of `make_move`. These swallow `MoveTimeoutException` and prevent the time limit from being enforced.

Execution aborts if any agent fails.

### What the Matchmaker Does NOT Do

The matchmaker is a scheduler only. Each subprocess call to a match runner handles: game execution, result parsing, scoreboard updates, and log writing. The matchmaker only tracks success/failure counts and prints a summary.

**Timeout:** The matchmaker sets none. Each runner has a game time budget
(for example 30s for Connect4, 150s for SurroundMorris at a 1s move limit).
A game that reaches that budget normally ends as a draw. The subprocess has
a hard timeout of the game budget times the match's game count, plus 60s of
grace; a hung subprocess can fail rather than return normal game results.
See "Game Time Limits" in CLAUDE.md for the current settings.

---

## Step 4: Enhance Agents

`utils/try_enhancing_agents.py` improves agent quality over time. For each selected model/game combo, it generates one new agent, benchmarks it against existing same-model agents in extended matches (10x that game's configured count), and prunes the worst performer. Backgammon keeps its race-to-five format and configured game cap.

```bash
# Enhance a specific model on a specific game
uv run utils/try_enhancing_agents.py --model Terra --game A5

# Enhance multiple models across multiple games
uv run utils/try_enhancing_agents.py --model Terra Opus --game A1,A5

# Enhance all models on all 2-player games
uv run utils/try_enhancing_agents.py --model all --game all
```

### How It Works

1. **Populate** — generates 1 new agent per combo (same as `populate_agents.py`).
2. **Match** — runs the new agent against every existing same-model agent with 10x that game's configured count (e.g. Battleship: 200 instead of 20). Backgammon keeps its race-to-five format and configured game cap.
3. **Evaluate** — determines the worst agent by comparing match points.
4. **Prune** — deletes the worst agent and renames if needed to keep run IDs contiguous.

All combos run concurrently: API calls fire in parallel and each combo's matches begin as soon as its agent is generated — even while other combos are still populating. Match subprocess concurrency is capped at 24.

Enhancement runs when invoked. The repository contains no scheduler that
automatically starts a biweekly enhancement cycle.

### Exclusions

- **Wizard (A3) is excluded from enhancement.** Its match runner and tournament are supported.
- Each model/game combo must have **at least 2 existing agents** to proceed.

---

## Scoreboard

Each game maintains a scoreboard at `scoreboard/<game-id>-scoreboard.txt`.

**Two-player format:**
```
Agent | Games | Wins | Losses | Draws | Points | Score
```

**Wizard format:**
```
Agent | Games | 1st | 2nd | 3rd | 4th | 5th | 6th | Points | Score
```

**Sorting:** Primary by Points (descending), tiebreaker by Score (descending). Score only affects ranking when two agents are tied on Points. How Score is accumulated varies by game (e.g. pieces remaining, cells cleared) — it acts as a goal-difference equivalent rather than a win condition.

Scoreboards are updated atomically via file-locking after each match. Match runners only update the scoreboard when called with `--update-scoreboard` (added automatically by the matchmaker).

New tournament runs accumulate results into the scoreboard files. Result
directories and scoreboard headers are created when needed; `.gitkeep` files
preserve the empty storage directories in the repository.

---

## Project Structure

```
agents/           # Generated agent code (organized by model name)
config/           # models.txt
games/            # Game prompts/rules for agent generation
game_scripts/     # Match runners (*_match.py) and matchmaker.py
utils/            # Core logic: API client, agent generation, scoreboard, logging
results/          # Match logs and outcomes per game
scoreboard/       # Per-game leaderboard files
```

### Key Modules

| File | Purpose |
|------|---------|
| `utils/model_api.py` | Async OpenRouter API client |
| `utils/game_config.py` | Independent per-game match counts and Wizard phase settings |
| `utils/populate_agents.py` | LLM-based agent code generation |
| `utils/scoreboard.py` | Atomic scoreboard read/write with file locking |
| `utils/logging_config.py` | Centralized logging setup |
| `game_scripts/*_match.py` | Game-specific match orchestrators |
| `game_scripts/matchmaker.py` | Round-robin tournament scheduler |

### `config/models.txt`

One current model name per line, matching an `agents/` folder. API generation
passes that name unchanged to the configured endpoint.
