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

**Running Matches:**
```bash
uv run python utils/battleship_match.py --agent model1:1 model2:1
uv run python utils/tictactoe_match.py --agent model1:1:2 model2:1
uv run python utils/wizard_match.py --agent model1:1 model2:1 model3:1
uv run python utils/word_finder_match.py --agent model1:1 model2:1
uv run python utils/word_matrix_match.py --agent model1:1 model2:1
uv run python utils/word_matrix_match.py --human
uv run python utils/surround_morris_match.py --agent model1:1 model2:1
```

## Key Modules

| File | Purpose |
|------|---------|
| `utils/model_api.py` | Async OpenRouter API client with token multipliers |
| `utils/populate_agents.py` | LLM-based agent code generation |
| `utils/*_match.py` | Game-specific match orchestrators |
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

## Development Notes

- Match runners execute agents in subprocesses with 1s move timeout (3s for WordFinder)
- Invalid moves, timeouts, crashes fallback to random valid moves
- Game logs track per-agent error statistics
- Agent code injection uses class renaming to avoid conflicts
