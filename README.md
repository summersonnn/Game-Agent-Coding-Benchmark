# Competitive LLM Agent Benchmark

This project is a benchmarking framework for evaluating Large Language Models (LLMs) in competitive environments through multi-agent games.

## Features

- **Multi-Agent Games**: Support for various games like Wizard, Battleship, and Tic-Tac-Toe.
- **Model-Agnostic API**: Integration with OpenRouter to test a wide range of LLMs.
- **Persistence**: Generate and save agent implementations for reuse and analysis.
- **Head-to-Head Evaluation**: Compare model performance through direct competition.

## Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed on your system.
- An OpenRouter API Key.

### Installation

1. Clone the repository.
2. Create and configure your `.env` file:
   ```bash
   cp .env.example .env  # If one exists, or create manually
   ```

### Configuration

Your `.env` file should contain:
- `MODEL_API_KEY`: Your OpenRouter API key.
- `NUM_RUNS`: Default number of agents to generate per model/game (e.g., `4`).
- `MAX_WORKERS`: For parallel execution.

Models are listed in `config/models.txt`. Lines starting with `!` are disabled.

---

## Tool: Agent Population (`populate_agents.py`)

The `populate_agents.py` script prompts LLMs to generate agent implementations for specific games and saves them to the `agents/` directory.

### Usage

Run the script using `uv`:

```bash
# Populate for all active models and all available games
uv run python utils/populate_agents.py --all

# Specify models by substring or index (from models.txt)
# This also works for disabled models (starting with !)
uv run python utils/populate_agents.py --model mistral deepseek 0

# Filter by game prefix
uv run python utils/populate_agents.py --games A1,A3

# Override the default number of runs
uv run python utils/populate_agents.py --all --runs 3
```

- **Substring matching**: `--model mistral` matches any model name containing "mistral".
- **Index matching**: `--model 0` selects the first model defined in `models.txt`.
- **Disabled models**: You can select models marked with `!` by using their substring or index.

### Folder Structure

Generated agents are stored as follows:
```
agents/
├── <model_name>/
│   ├── A1-Battleship_1.py
│   ├── A1-Battleship_2.py
│   └── ...
```

---

## Running Matches

Matches are run using pre-generated agents from the `agents/` folder. The scripts match agents in pairs (for 2-player games) or groups of 6 (for Wizard).

### General Usage

All match scripts use the `--agent` argument to specify which models and runs to use.

**Format**: `--agent model_pattern[:run1:run2:...]`

- `model_pattern`: A substring to match the model's folder name in `agents/`.
- `run1:run2...`: Optional. Specific run numbers to use. If omitted, all available runs for that model are used.

### Games

#### 1. Wizard (6 Players)
Requires a total number of agents that is a multiple of 6.

```bash
# Use all runs from mistral and gpt-mini
uv run python game_scripts/A3-wizard_match.py --agent mistral gpt-mini

# Use specific runs
uv run python game_scripts/A3-wizard_match.py --agent mistral:1:2:3 gpt-mini:1:2:3
```

#### 2. Battleship (2 Players)
Matches agents from two models head-to-head.

```bash
# Match first N runs of mistral against first N runs of deepseek
uv run python game_scripts/A1-battleship_match.py --agent mistral deepseek

# Match specific runs
uv run python game_scripts/A1-battleship_match.py --agent mistral:1:2 deepseek:3:4
```

#### 3. Tic Tac Toe (2 Players)
Matches agents from two models head-to-head.

```bash
uv run python game_scripts/A2-tictactoe_match.py --agent mistral deepseek
```

### Debug Mode
For Wizard, you can enable interactive debug mode:
```bash
uv run python game_scripts/A3-wizard_match.py --agent mistral:1 --debug
```

---

## Tool: Matchmaker (`matchmaker.py`)

The matchmaker automates full round-robin tournaments. It discovers all agents for a game, generates every cross-model fixture, and executes them concurrently as subprocesses — each delegated to the appropriate match runner.

### Usage

```bash
# Full tournament for SurroundMorris, each pair plays 4 times
uv run python game_scripts/matchmaker.py --game A8 --same_opponent_match 4

# Preview fixtures without running anything
uv run python game_scripts/matchmaker.py --game A8 --same_opponent_match 1 --dry-run

# Wizard tournament with 8 concurrent workers
uv run python game_scripts/matchmaker.py --game A3 --same_opponent_match 2 --workers 8
```

### Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `--game` | str | required | Game ID: A1 through A8 |
| `--same_opponent_match` | int | 1 | Minimum encounters per cross-model agent pair |
| `--workers` | int | 4 | Max concurrent match subprocesses |
| `--dry-run` | flag | false | Print fixture list without executing |

### How `--same_opponent_match` works

This controls how many times every cross-model agent pair is guaranteed to encounter each other.

**2-player games (A1, A2, A4-A8):** Each cross-model pair plays a direct head-to-head match `same_opponent_match` times. All `itertools.combinations` of agents are generated, same-model pairs are filtered out, and the remainder is repeated. For example, 20 models with 2 runs each (40 agents) produce 760 cross-model pairs — with `--same_opponent_match 4` that's 3040 total matches.

**6-player games (A3 Wizard):** There is no head-to-head; instead, 6 agents from 6 different models share a table per game. The matchmaker uses a greedy pairwise-coverage algorithm to generate groups such that every cross-model agent pair co-occurs in at least `same_opponent_match` games. This ensures sufficient statistical signal to compare any two models even in a multiplayer setting.

### What the matchmaker does NOT do

The matchmaker is purely a scheduler. Each subprocess call to a match runner handles game execution, result parsing, scoreboard updates, and log writing internally. The matchmaker only tracks success/failure counts and reports a summary at the end.

## Project Structure

- `agents/`: Stored agent implementations.
- `config/`: Configuration files (models, questions).
- `games/`: Game prompts and rules.
- `game_scripts/`: Match runners and tournament scheduler.
- `utils/`: Core logic and population scripts.
- `results/`: Logs and performance data.
