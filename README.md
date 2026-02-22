# Competitive LLM Agent Benchmark

Benchmarking framework for evaluating LLMs in competitive multi-agent game environments. Generates agent implementations via OpenRouter API and orchestrates head-to-head/multiplayer matches.

Models produce code that can play games rather than playing the games themselves. Their sole interaction occurs at the stage of code creation. As a result, this benchmark is hybrid in nature, combining elements of both code generation and reasoning.

The live league standings can be accessed at [gameagentcodingleague.com](https://gameagentcodingleague.com/).

## Features

- **8 Competitive Games**: Battleship, TicTacToe, Wizard, WordFinder, Connect4, WordMatrix, 2x8 Mini Chess, SurroundMorris.
- **Model-Agnostic**: OpenRouter integration supports any available LLM.
- **Persistent Agents**: Generated code stored per-model for reuse and analysis.
- **Points-Based Scoring**: All matches, except for the A3 game, follow the standard scoring format: a win earns 3 points, a draw earns 1 point, and a loss earns 0 points, with goal difference used to break ties.
The A3 game uses a different approach — there are no win, loss, or draw outcomes. Instead, the six agents are ranked from first to last: the top agent receives 5 points, the second earns 4 points, and the points continue decreasing by one down to 0 points for the last-place agent.
- **Tournament Automation**: Round-robin matchmaker with configurable concurrency.

---

## Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed on your system.
- An OpenRouter API key.

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
NUM_RUNS=4
NUM_OF_GAMES_IN_A_MATCH=100
```

Edit `config/models.txt` — one model ID per line.

---

## Step 1: Generate Agents

`utils/populate_agents.py` prompts LLMs to generate agent implementations and saves them under `agents/`.

```bash
# All active models, all games
uv run utils/populate_agents.py --all

# Specific models by substring or index from models.txt
uv run utils/populate_agents.py --model mistral deepseek

# Filter to specific games
uv run utils/populate_agents.py --games A1,A8

# Override run count (adds to existing runs, does not overwrite)
uv run utils/populate_agents.py --all --runs 2

# Interactive model selection (no args)
uv run utils/populate_agents.py
```

**Model selection rules:**
- `--model mistral` matches any model name containing "mistral" (case-insensitive).
- `--model 0` selects the model at index 0 in `models.txt`.

- If a substring matches multiple models, an interactive prompt resolves the ambiguity.

**Output:** `agents/<sanitized_model_name>/<game_id>_<run>.py`

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

All match scripts require `--agent` for agent-vs-agent mode. Human play modes (`--humanvsbot`, `--humanvshuman`, `--humanvsagent`) are available in most scripts but not all games support them — check the per-game details below.

---

### A1: Battleship

2-player, 8x8 grid. Ships: [5, 4, 3]. Placement phase then bombing phase.

```bash
# Agent vs agent
uv run game_scripts/A1-battleship_match.py --agent model1:1 model2:1

# Human modes
uv run game_scripts/A1-battleship_match.py --humanvsbot
uv run game_scripts/A1-battleship_match.py --humanvshuman
uv run game_scripts/A1-battleship_match.py --humanvsagent --agent model:1
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
uv run game_scripts/matchmaker.py --game A8 --new-model model-folder-name

# Verify agent syntax before running
uv run game_scripts/matchmaker.py --game A8 --health
```

### Matchmaker Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `--game` | str | required | Game ID: A1, A2, A3, A4, A5, A6, A7, A8 |
| `--same_opponent_match` | int | 8 | Minimum times each cross-model pair must meet |
| `--workers` | int | 24 | Max concurrent match subprocesses |
| `--dry-run` | flag | false | Print fixture list without executing |
| `--new-model` | str | — | Comma-separated model folder names; only generate fixtures involving these models |
| `--health` | flag | false | Run syntax + exception-handler checks on all agents before execution |

### How `--same_opponent_match` Works

Every cross-model agent pair plays a direct match `N` times. Example: 20 models × 2 runs = 40 agents → 760 cross-model pairs → `--same_opponent_match 4` = 3040 matches.

### Incremental Tournaments (`--new-model`)

When you add new models and regenerate agents, use `--new-model` to avoid replaying all existing cross-model pairs. Only fixtures involving the specified model folders are scheduled.

```bash
uv run game_scripts/matchmaker.py --game A8 --new-model new-gpt-model,new-claude-model
```

### Agent Health Checks (`--health`)

Before executing a tournament, `--health` validates every agent:
1. **Syntax check** — parses each file with `ast.parse`.
2. **Broad except in `make_move`** — detects `except Exception`, `except BaseException`, or bare `except:` at the top level of `make_move`. These swallow `MoveTimeoutException` and prevent the time limit from being enforced.

Execution aborts if any agent fails.

### What the Matchmaker Does NOT Do

The matchmaker is a scheduler only. Each subprocess call to a match runner handles: game execution, result parsing, scoreboard updates, and log writing. The matchmaker only tracks success/failure counts and prints a summary.

**Timeout:** 900 seconds per match subprocess. Timed-out matches are killed and recorded as failures.

---

## Step 4: Enhance Agents

`utils/try_enhancing_agents.py` improves agent quality over time. For each selected model/game combo, it generates one new agent, benchmarks it against existing same-model agents in extended matches (10x the base game count), and prunes the worst performer.

```bash
# Enhance a specific model on a specific game
uv run utils/try_enhancing_agents.py --model mistral --game A4

# Enhance multiple models across multiple games
uv run utils/try_enhancing_agents.py --model mistral minimax --game A1,A4

# Enhance all models on all 2-player games
uv run utils/try_enhancing_agents.py --model all --game all
```

### How It Works

1. **Populate** — generates 1 new agent per combo (same as `populate_agents.py`).
2. **Match** — runs the new agent against every existing same-model agent with 10x games (e.g. 1000 instead of 100).
3. **Evaluate** — determines the worst agent by comparing match points.
4. **Prune** — deletes the worst agent and renames if needed to keep run IDs contiguous.

All combos run concurrently: API calls fire in parallel and each combo's matches begin as soon as its agent is generated — even while other combos are still populating. Match subprocess concurrency is capped at 24.

> **Biweekly Enhancement Cycle:** Every two weeks, all models across all games are put through the enhancement process. This accounts for upstream API model updates (e.g. weight changes, quantization tweaks) and eliminates the luck effect from one-shot code generation.

### Exclusions

- **6-player games** (A3) are not supported and are automatically skipped.
- Each model/game combo must have **at least 2 existing agents** to proceed.

---

## Scoreboard

Each game maintains a scoreboard at `scoreboard/<game-id>-scoreboard.txt`.

**Format:**
```
Agent | Games | Wins | Losses | Draws | Points | Score
```

**Sorting:** Primary by Points (descending), tiebreaker by Score (descending). Score only affects ranking when two agents are tied on Points. How Score is accumulated varies by game (e.g. pieces remaining, cells cleared) — it acts as a goal-difference equivalent rather than a win condition.

Scoreboards are updated atomically via file-locking after each match. Match runners only update the scoreboard when called with `--update-scoreboard` (added automatically by the matchmaker).

---

## Project Structure

```
agents/           # Generated agent code (organized by model name)
config/           # models.txt, max_tokens.txt
games/            # Game prompts/rules for agent generation
game_scripts/     # Match runners (*_match.py) and matchmaker.py
tools/            # One-off diagnostic and analysis scripts (not part of the main pipeline)
utils/            # Core logic: API client, agent generation, scoreboard, logging
results/          # Match logs and outcomes per game
scoreboard/       # Per-game leaderboard files
```

### Key Modules

| File | Purpose |
|------|---------|
| `utils/model_api.py` | Async OpenRouter API client with per-game token multipliers |
| `utils/populate_agents.py` | LLM-based agent code generation |
| `utils/scoreboard.py` | Atomic scoreboard read/write with file locking |
| `utils/logging_config.py` | Centralized logging setup |
| `game_scripts/*_match.py` | Game-specific match orchestrators |
| `game_scripts/matchmaker.py` | Round-robin tournament scheduler |
| `tools/debug_syntax.py` | Validates agent code merging for syntax errors (mirrors match runner injection logic) |
| `tools/spot_inconsistent_performances.py` | Reports same-model agents with divergent scoreboard rankings |

### `config/models.txt`

One model ID per line.

### `config/max_tokens.txt`

Per-game token multipliers applied to `MODEL_MAX_TOKENS`. Example: `A1-Battleship: 2` means Battleship generation uses `2 × MODEL_MAX_TOKENS` tokens.
