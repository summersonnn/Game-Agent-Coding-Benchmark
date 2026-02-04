"""
Agent Population Script: Prompts LLMs to generate agent code and saves results.

Sends game prompts to selected models and saves the extracted agent code to the
agents/ directory, organized by model and game with numbered runs.

Usage:
    uv run python utils/populate_agents.py --all           # All models, all games
    uv run python utils/populate_agents.py --model 0 1 2   # Specific models by index
    uv run python utils/populate_agents.py --games A1,A3   # Specific games by prefix
"""

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from model_api import ModelAPI
from logging_config import setup_logging

logger = setup_logging(__name__)

load_dotenv()

# Configuration
try:
    DEFAULT_NUM_RUNS = int(os.getenv("NUM_RUNS", "4"))
except (ValueError, TypeError):
    DEFAULT_NUM_RUNS = 4

try:
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "16"))
except (ValueError, TypeError):
    MAX_WORKERS = 16

AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAMES_DIR = Path(__file__).parent.parent / "games"


def sanitize_model_name(model_name: str) -> str:
    """Convert model name to a valid folder name."""
    # User rule: Do not trim if you don't have to.
    # Take the first part before "@" and if there's a second part after "/", take that too.
    
    # Part 1: everything before "@"
    name_to_use = model_name.split("@")[0]
    
    # Check for "second part after '/'" (part after the second slash, if it exists)
    # Common format: provider/model@preset/flavor
    parts = model_name.split("/")
    if len(parts) >= 3:
        # Third segment (after second slash) is the flavor
        flavor = parts[2]
        if flavor not in name_to_use:
            name_to_use = f"{name_to_use}-{flavor}"
    
    # Replace slashes with hyphens and remove other invalid chars
    sanitized = name_to_use.replace("/", "-")
    return re.sub(r"[^\w\-.]", "_", sanitized)


def get_game_prefix(game_file: str) -> str:
    """Extract game prefix from filename (e.g., 'A1-Battleship.txt' -> 'A1')."""
    return game_file.split("-")[0]


def get_game_name(game_file: str) -> str:
    """Extract game name without extension (e.g., 'A1-Battleship.txt' -> 'A1-Battleship')."""
    return game_file.replace(".txt", "")


def load_game_prompts(game_filter: list[str] | None = None) -> dict[str, str]:
    """
    Load game prompts from the games directory.
    
    Args:
        game_filter: Optional list of game prefixes to include (e.g., ['A1', 'A3'])
    
    Returns:
        Dict mapping game name to prompt content
    """
    prompts = {}
    
    if not GAMES_DIR.exists():
        logger.error("Games directory not found: %s", GAMES_DIR)
        return prompts
    
    for game_file in sorted(GAMES_DIR.glob("*.txt")):
        prefix = get_game_prefix(game_file.name)
        
        # Apply filter if specified
        if game_filter and prefix not in game_filter:
            continue
        
        game_name = get_game_name(game_file.name)
        prompts[game_name] = game_file.read_text()
        logger.info("Loaded prompt for %s", game_name)
    
    return prompts


def get_next_run_ids(model_dir: Path, game_name: str, num_runs: int) -> list[int]:
    """
    Determine the next available run IDs for a model/game combination.
    
    Scans existing files to find the highest run number and returns the next
    N consecutive run IDs.
    
    Args:
        model_dir: Directory containing agent files for the model
        game_name: Name of the game (e.g., 'A1-Battleship')
        num_runs: Number of run IDs to allocate
        
    Returns:
        List of run IDs to use (e.g., [5, 6, 7, 8] if runs 1-4 exist)
    """
    existing_runs: set[int] = set()
    pattern = re.compile(rf"^{re.escape(game_name)}_(\d+)\.py$")
    
    for file in model_dir.glob(f"{game_name}_*.py"):
        match = pattern.match(file.name)
        if match:
            existing_runs.add(int(match.group(1)))
    
    if not existing_runs:
        # No existing runs, start from 1
        return list(range(1, num_runs + 1))
    
    # Start from the highest existing run + 1
    max_run = max(existing_runs)
    return list(range(max_run + 1, max_run + 1 + num_runs))


def extract_agent_code(response: str, game_name: str) -> tuple[str, str]:
    """
    Extract agent class from model response.
    
    Returns:
        Tuple of (agent_code, extra_imports)
    """
    # Determine expected class name based on game
    if "Battleship" in game_name:
        class_pattern = r"class\s+BattleshipAgent"
        class_search = "class BattleshipAgent"
    elif "TicTacToe" in game_name:
        class_pattern = r"class\s+TicTacToeAgent"
        class_search = "class TicTacToeAgent"
    elif "Wizard" in game_name:
        class_pattern = r"class\s+WizardAgent"
        class_search = "class WizardAgent"
    elif "WordFinder" in game_name:
        class_pattern = r"class\s+WordFinderAgent"
        class_search = "class WordFinderAgent"
    else:
        # Generic fallback
        class_pattern = r"class\s+\w+Agent"
        class_search = "class "
    
    # Find code blocks
    blocks = re.findall(r"```(?:python)?\s*(.*?)```", response, re.DOTALL)
    code = ""
    
    # Look for agent class in code blocks
    for block in blocks:
        if re.search(class_pattern, block):
            code = block
            break
    
    # Fallback: search in raw text
    if not code and class_search in response:
        match = re.search(
            rf"({class_pattern}.*?)(?=\nclass\s|\ndef\s|$|if __name__)",
            response,
            re.DOTALL
        )
        if match:
            code = match.group(1)
    
    if not code:
        return "", ""
    
    # Extract imports (excluding random which is usually in template)
    imports = []
    for line in response.split("\n"):
        line = line.strip()
        if (line.startswith("import ") or line.startswith("from ")) and "random" not in line:
            imports.append(line)
    
    return code.strip(), "\n".join(imports)


async def prompt_model(
    api: ModelAPI,
    model_name: str,
    prompt: str,
    run_id: int,
    game_name: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str, int, str]:
    """Call a model with a game prompt and return its response."""
    async with semaphore:
        try:
            logger.info("Prompting %s for %s (run %d)...", model_name, game_name, run_id)
            max_tokens = api.get_max_tokens(game_name)
            response = await api.call(
                prompt, model_name=model_name, reasoning=True, max_tokens=max_tokens
            )
            content = response.choices[0].message.content or ""
            logger.info(
                "Received response from %s for %s (run %d): %d chars",
                model_name, game_name, run_id, len(content)
            )
            return game_name, model_name, run_id, content
        except Exception as e:
            logger.error("Error prompting %s for %s: %s", model_name, game_name, e)
            return game_name, model_name, run_id, ""


async def populate_agents(
    api: ModelAPI,
    models: list[str],
    prompts: dict[str, str],
    num_runs: int = DEFAULT_NUM_RUNS,
) -> None:
    """
    Prompt models and save generated agent code.
    
    Fires all API calls in parallel (across models, games, and runs) with a
    semaphore-based concurrency limit from MAX_WORKERS.
    
    Args:
        api: ModelAPI instance
        models: List of model names to prompt
        prompts: Dict mapping game name to prompt content
        num_runs: Number of times to prompt each model per game
    """
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    semaphore = asyncio.Semaphore(MAX_WORKERS)
    
    # Create model directories upfront
    model_dirs: dict[str, Path] = {}
    for model in models:
        model_short = sanitize_model_name(model)
        model_dir = AGENTS_DIR / model_short
        model_dir.mkdir(parents=True, exist_ok=True)
        model_dirs[model] = model_dir
    
    # Build all tasks across models, games, and runs
    tasks = []
    for model in models:
        model_dir = model_dirs[model]
        for game_name, prompt in prompts.items():
            run_ids = get_next_run_ids(model_dir, game_name, num_runs)
            for run_id in run_ids:
                tasks.append(
                    asyncio.create_task(
                        prompt_model(api, model, prompt, run_id, game_name, semaphore)
                    )
                )
    
    print(f"\nFiring {len(tasks)} API calls with max {MAX_WORKERS} concurrent...")
    
    # Await all tasks
    responses = await asyncio.gather(*tasks)
    
    # Process and save each response
    results: dict[str, dict[str, list[tuple[int, str]]]] = {}  # model -> game -> [(run, status)]
    
    for game_name, model_name, run_id, content in responses:
        model_short = sanitize_model_name(model_name)
        model_dir = model_dirs[model_name]
        
        if model_short not in results:
            results[model_short] = {}
        if game_name not in results[model_short]:
            results[model_short][game_name] = []
        
        if not content:
            results[model_short][game_name].append((run_id, "FAILED (empty response)"))
            continue
        
        code, imports = extract_agent_code(content, game_name)
        
        if not code:
            results[model_short][game_name].append((run_id, "FAILED (no agent code found)"))
            continue
        
        # Build file content with metadata header
        file_content = f'''"""
Agent Code: {game_name}
Model: {model_name}
Run: {run_id}
Generated: {timestamp}
"""

{imports}

{code}
'''
        
        # Save to file
        output_file = model_dir / f"{game_name}_{run_id}.py"
        output_file.write_text(file_content)
        results[model_short][game_name].append(
            (run_id, f"Saved to {output_file.relative_to(AGENTS_DIR.parent)}")
        )
    
    # Print summary grouped by model and game
    for model_short in sorted(results.keys()):
        print(f"\n{'='*60}")
        print(f"Model: {model_short}")
        print(f"{'='*60}")
        for game_name in sorted(results[model_short].keys()):
            print(f"\n  Game: {game_name}")
            for run_id, status in sorted(results[model_short][game_name]):
                print(f"    Run {run_id}: {status}")


def select_models_interactive(api: ModelAPI) -> list[str]:
    """Interactive model selection using substring matching."""
    print("\nAvailable models (including disabled ones marked with !):")
    for i, model in enumerate(api.all_models):
        print(f"  [{i}] {model}")
    
    print("\nEnter model substrings (space-separated), indices, or 'all' for all active models:")
    choice = input("> ").strip().lower()
    
    if choice == "all":
        return api.models[:]
    
    selected_models = []
    queries = choice.split()
    
    for query in queries:
        # Check if it's an index
        if query.isdigit():
            idx = int(query)
            if 0 <= idx < len(api.all_models):
                model = api.all_models[idx]
                selected_models.append(model.lstrip("!"))
            else:
                print(f"WARNING: Model index {idx} out of range, skipping")
            continue
            
        # Otherwise, treat as substring
        matches = [m for m in api.all_models if query in m.lower()]
        if not matches:
            print(f"WARNING: No model matches substring '{query}', skipping")
            continue
        
        if len(matches) > 1:
            selected_model = api.resolve_model_interactive(query, matches)
            if selected_model:
                selected_models.append(selected_model.lstrip("!"))
        else:
            selected_models.append(matches[0].lstrip("!"))
    
    return list(dict.fromkeys(selected_models)) # Preserve order, remove duplicates


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Populate agent code by prompting LLMs"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Populate for all models and all games"
    )
    parser.add_argument(
        "--model",
        type=str,
        nargs="+",
        help="Model substrings or indices to use (e.g., --model mistral gpt-5)"
    )
    parser.add_argument(
        "--games",
        type=str,
        help="Comma-separated game prefixes (e.g., --games A1,A3)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_NUM_RUNS,
        help=f"Number of runs per model/game (default: {DEFAULT_NUM_RUNS})"
    )
    
    args = parser.parse_args()
    
    # Initialize API
    api = ModelAPI()
    
    if not api.models:
        print("ERROR: No models loaded from config/models.txt")
        sys.exit(1)
    
    # Determine models to use
    if args.all:
        models = api.models[:]
    elif args.model is not None:
        models = []
        for query in args.model:
            # Check if it's an index
            if query.isdigit():
                idx = int(query)
                if 0 <= idx < len(api.all_models):
                    model = api.all_models[idx]
                    models.append(model.lstrip("!"))
                else:
                    print(f"WARNING: Model index {idx} out of range, skipping")
                continue

            # Substring matching
            matches = [m for m in api.all_models if query.lower() in m.lower()]
            if not matches:
                print(f"WARNING: No model matches substring '{query}', skipping")
                continue
            
            if len(matches) > 1:
                selected_model = api.resolve_model_interactive(query, matches)
                if selected_model:
                    models.append(selected_model.lstrip("!"))
            else:
                models.append(matches[0].lstrip("!"))
        
        # Remove duplicates while preserving order
        models = list(dict.fromkeys(models))
        
        if not models:
            print("ERROR: No valid models selected")
            sys.exit(1)
    else:
        models = select_models_interactive(api)
    
    # Determine games to include
    game_filter = None
    if args.games:
        game_filter = [g.strip() for g in args.games.split(",")]
    
    # Load prompts
    prompts = load_game_prompts(game_filter)
    
    if not prompts:
        print("ERROR: No game prompts found")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("AGENT POPULATION")
    print("=" * 60)
    print(f"Models: {len(models)}")
    for m in models:
        print(f"  - {sanitize_model_name(m)}")
    print(f"\nGames: {len(prompts)}")
    for g in prompts:
        print(f"  - {g}")
    print(f"\nRuns per model/game: {args.runs}")
    print(f"Total API calls: {len(models) * len(prompts) * args.runs}")
    print("=" * 60)
    
    # Confirm
    confirm = input("\nProceed? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)
    
    # Run
    asyncio.run(populate_agents(api, models, prompts, args.runs))
    
    print("\n" + "=" * 60)
    print("COMPLETE")
    print(f"Agent code saved to: {AGENTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
