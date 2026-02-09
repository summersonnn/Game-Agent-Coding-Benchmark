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

## Games

| ID | Game | Players | Status |
|----|------|---------|--------|
| A1 | Battleship | 2 | Playable |
| A2 | TicTacToe | 2 | Playable |
| A3 | Wizard | 6 | Playable |
| A4 | WordFinder | 2 | Playable |
| A6 | WordMatrixGame | 2 | Playable |
| A8 | SurroundMorris | 2 | Playable |
| A5,A7 | (Placeholders) | - | Not implemented |

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
