# Competitive LLM Agent Benchmark

Benchmarking framework for evaluating LLMs in competitive multi-agent game environments. Generates agent implementations via OpenRouter API and orchestrates head-to-head/multiplayer matches.

## Features

- **8 Competitive Games**: Battleship, TicTacToe, Wizard, WordFinder, Connect4, WordMatrix, 2x8Chess, SurroundMorris.
- **Model-Agnostic**: OpenRouter integration supports any available LLM.
- **Persistent Agents**: Generated code stored per-model for reuse and analysis.
- **Football-Style Scoring**: Win = 3 pts, Draw = 1 pt, Loss = 0 pts with goal-difference tiebreaker.
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

Edit `config/models.txt` — one model ID per line. Prefix with `!` to disable a model without removing it.

---

## Step 1: Generate Agents

`utils/populate_agents.py` prompts LLMs to generate agent implementations and saves them under `agents/`.

```bash
# All active models, all games
uv run python utils/populate_agents.py --all

# Specific models by substring or index from models.txt
uv run python utils/populate_agents.py --model mistral deepseek

# Filter to specific games
uv run python utils/populate_agents.py --games A1,A8

# Override run count (adds to existing runs, does not overwrite)
uv run python utils/populate_agents.py --all --runs 2

# Interactive model selection (no args)
uv run python utils/populate_agents.py
```

**Model selection rules:**
- `--model mistral` matches any model name containing "mistral" (case-insensitive).
- `--model 0` selects the model at index 0 in `models.txt`.
- Disabled models (prefixed `!`) can still be selected by substring or index.
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

All match scripts require `--agent` for agent-vs-agent mode. Human play modes are available in most scripts (see per-game details below).

---

### A1: Battleship

2-player, 8x8 grid. Ships: [5, 4, 3]. Placement phase then bombing phase.

```bash
# Agent vs agent
uv run python game_scripts/A1-battleship_match.py --agent model1:1 model2:1

# Human modes
uv run python game_scripts/A1-battleship_match.py --humanvsbot
uv run python game_scripts/A1-battleship_match.py --humanvshuman
uv run python game_scripts/A1-battleship_match.py --humanvsagent --agent model:1
```

---

### A2: TicTacToe

2-player, 5x5 board. First-move assignment alternates across games.

```bash
uv run python game_scripts/A2-tictactoe_match.py --agent model1:1 model2:1
uv run python game_scripts/A2-tictactoe_match.py --humanvsbot
uv run python game_scripts/A2-tictactoe_match.py --humanvshuman
uv run python game_scripts/A2-tictactoe_match.py --humanvsagent --agent model:1
```

---

### A3: Wizard

6-player trick-taking card game. 10 rounds, players bid on tricks won.

Requires agents from at least 6 different models (total agent count must be a multiple of 6).

```bash
# Use all runs from 6+ models
uv run python game_scripts/A3-wizard_match.py --agent modelA modelB modelC modelD modelE modelF

# Specific runs
uv run python game_scripts/A3-wizard_match.py --agent a:1:2:3 b:1:2:3 c:1 d:1 e:1 f:1

# Debug mode (interactive, detailed output)
uv run python game_scripts/A3-wizard_match.py --agent model:1 --debug

# Human vs 5 random bots
uv run python game_scripts/A3-wizard_match.py --human
```

---

### A4: WordFinder

2-player word chain game. Each word must start/end with letters from the previous word.

```bash
uv run python game_scripts/A4-word_finder_match.py --agent model1:1 model2:1
uv run python game_scripts/A4-word_finder_match.py --humanvsbot
uv run python game_scripts/A4-word_finder_match.py --humanvshuman
uv run python game_scripts/A4-word_finder_match.py --humanvsagent --agent model:1
```

---

### A5: Connect4 (Random Start)

2-player, 6x7 board. One disc is pre-placed randomly at match start.

```bash
uv run python game_scripts/A5-connect4_match.py --agent model1:1 model2:1

# Human vs random bot
uv run python game_scripts/A5-connect4_match.py --human
```

---

### A6: WordMatrixGame

2-player, 4x4 letter grid. Players trace paths through adjacent cells to form words.

```bash
uv run python game_scripts/A6-word_matrix_match.py --agent model1:1 model2:1
uv run python game_scripts/A6-word_matrix_match.py --humanvsbot
uv run python game_scripts/A6-word_matrix_match.py --humanvshuman
uv run python game_scripts/A6-word_matrix_match.py --humanvsagent --agent model:1
```

---

### A7: 2x8 Mini Chess

2-player, 2x8 board. Each side has K, N, R, P. Pawns promote to Rook.

```bash
uv run python game_scripts/A7-twobyeight_chess_match.py --agent model1:1 model2:1

# Human vs random bot
uv run python game_scripts/A7-twobyeight_chess_match.py --human
```

---

### A8: SurroundMorris

2-player, Nine Men's Morris variant. Capture by surrounding (overwhelm rule) instead of mills.

```bash
uv run python game_scripts/A8-surround_morris_match.py --agent model1:1 model2:1
uv run python game_scripts/A8-surround_morris_match.py --humanvsbot
uv run python game_scripts/A8-surround_morris_match.py --humanvshuman
uv run python game_scripts/A8-surround_morris_match.py --humanvsagent --agent model:1
```

---

## Step 3: Run Tournaments

`game_scripts/matchmaker.py` automates round-robin tournaments. It discovers all agents for a game, generates cross-model fixtures, and runs them concurrently as subprocesses.

```bash
# Full tournament for SurroundMorris, each cross-model pair plays 4 times
uv run python game_scripts/matchmaker.py --game A8 --same_opponent_match 4

# Preview fixtures without executing
uv run python game_scripts/matchmaker.py --game A8 --dry-run

# Wizard tournament with 8 concurrent workers
uv run python game_scripts/matchmaker.py --game A3 --same_opponent_match 2 --workers 8

# Only run matches involving newly added models (incremental update)
uv run python game_scripts/matchmaker.py --game A8 --new-model model-folder-name

# Verify agent syntax before running
uv run python game_scripts/matchmaker.py --game A8 --health
```

### Matchmaker Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `--game` | str | required | Game ID: A1 through A8 |
| `--same_opponent_match` | int | 2 | Minimum times each cross-model pair must meet |
| `--workers` | int | 16 | Max concurrent match subprocesses |
| `--dry-run` | flag | false | Print fixture list without executing |
| `--new-model` | str | — | Comma-separated model folder names; only generate fixtures involving these models |
| `--health` | flag | false | Run syntax + exception-handler checks on all agents before execution |

### How `--same_opponent_match` Works

**2-player games (A1, A2, A4–A8):** Every cross-model agent pair plays a direct match `N` times. Example: 20 models × 2 runs = 40 agents → 760 cross-model pairs → `--same_opponent_match 4` = 3040 matches.

**6-player games (A3 Wizard):** No direct head-to-head; 6 agents from different models share each table. A greedy pairwise-coverage algorithm generates groups ensuring every cross-model pair co-occurs in at least `N` games.

### Incremental Tournaments (`--new-model`)

When you add new models and regenerate agents, use `--new-model` to avoid replaying all existing cross-model pairs. Only fixtures involving the specified model folders are scheduled.

```bash
uv run python game_scripts/matchmaker.py --game A8 --new-model new-gpt-model,new-claude-model
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

## Scoreboard

Each game maintains a scoreboard at `scoreboard/<game-id>-scoreboard.txt`.

**Format:**
```
Agent | Games | Wins | Losses | Draws | Points | Score
```

**Sorting:** Primary by Points (descending), tiebreaker by Score (descending).

Scoreboards are updated atomically via file-locking after each match. Match runners only update the scoreboard when called with `--update-scoreboard` (added automatically by the matchmaker).

---

## Project Structure

```
agents/           # Generated agent code (organized by model name)
config/           # models.txt, max_tokens.txt
games/            # Game prompts/rules for agent generation
game_scripts/     # Match runners (*_match.py) and matchmaker.py
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

### `config/models.txt`

One model ID per line. Lines starting with `!` are disabled (excluded from `--all` but still selectable by name/index in `populate_agents.py`).

### `config/max_tokens.txt`

Per-game token multipliers applied to `MODEL_MAX_TOKENS`. Example: `A1: 4` means Battleship generation uses `4 × MODEL_MAX_TOKENS` tokens.
