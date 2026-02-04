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
uv run python utils/wizard_match.py --agent mistral gpt-mini

# Use specific runs
uv run python utils/wizard_match.py --agent mistral:1:2:3 gpt-mini:1:2:3
```

#### 2. Battleship (2 Players)
Matches agents from two models head-to-head.

```bash
# Match first N runs of mistral against first N runs of deepseek
uv run python utils/battleship_match.py --agent mistral deepseek

# Match specific runs
uv run python utils/battleship_match.py --agent mistral:1:2 deepseek:3:4
```

#### 3. Tic Tac Toe (2 Players)
Matches agents from two models head-to-head.

```bash
uv run python utils/tictactoe_match.py --agent mistral deepseek
```

### Debug Mode
For Wizard, you can enable interactive debug mode:
```bash
uv run python utils/wizard_match.py --agent mistral:1 --debug
```

## Project Structure

- `agents/`: Stored agent implementations.
- `config/`: Configuration files (models, questions).
- `games/`: Game prompts and rules.
- `utils/`: Core logic, match runners, and population scripts.
- `results/`: Logs and performance data.
