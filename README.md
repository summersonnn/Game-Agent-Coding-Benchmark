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

The `populate_agents.py` script prompts LLMs to generate agent implementations for specific games and saves them to the `agents/` directory. This avoids generating code on-the-fly for every match.

### Usage

Run the script using `uv`:

```bash
# Populate for all enabled models and all available games
uv run python utils/populate_agents.py --all

# Specify model indices (from models.txt)
uv run python utils/populate_agents.py --model 0 2 5

# Filter by game prefix
uv run python utils/populate_agents.py --games A1,A3

# Override the default number of runs
uv run python utils/populate_agents.py --all --runs 3
```

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

### Stored Agent Mode (Recommended)

Use pre-generated agents from the `agents/` folder:

```bash
# Run with 6 agents: 3 from mistral, 3 from fp8
uv run python utils/wizard_match.py --stored --agents "mistral:1,mistral:2,mistral:3,fp8:1,fp8:2,fp8:3"
```

Format: `--agents model_pattern:run_number,...` (must specify exactly 6 agents)

- Model patterns are partial matches (e.g., `mistral` matches `mistral-large-2512`)
- If a pattern matches multiple folders, a warning is shown and the first match is used

### On-the-Fly Mode

Prompt models in real-time (requires API calls):

```bash
uv run python utils/wizard_match.py
uv run python utils/battleship_match.py
```

## Project Structure

- `agents/`: Stored agent implementations.
- `config/`: Configuration files (models, questions).
- `games/`: Game prompts and rules.
- `utils/`: Core logic, match runners, and population scripts.
- `results/`: Logs and performance data.
