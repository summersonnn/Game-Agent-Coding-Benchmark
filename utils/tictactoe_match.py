"""
Tic Tac Toe Match Runner: Orchestrates head-to-head matches between two AI models.

Prompts two models to implement TicTacToeAgent, extracts their code, renames
them to TicTacToeAgent_1 and TicTacToeAgent_2, runs games, and reports
win/loss statistics.
"""

import asyncio
from datetime import datetime
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
import logging
from dotenv import load_dotenv

from model_api import ModelAPI
from logging_config import setup_logging

logger = setup_logging(__name__)

# Load environment variables
load_dotenv()

# Configuration
NUM_RUNS = int(os.getenv("NUM_RUNS", "4"))
NUM_ROUNDS_PER_TICTACTOE_MATCH = 10
BOARD_SIZE = 3

# Results directories
TICTACTOE_RESULTS_DIR = Path(__file__).parent.parent / "results" / "tictactoe"
GAME_LOGS_DIR = TICTACTOE_RESULTS_DIR / "game_logs"
MODEL_RESPONSES_DIR = TICTACTOE_RESULTS_DIR / "model_responses"

# The game code template with placeholders for agent implementations
GAME_CODE_TEMPLATE = '''
import sys
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Move timeout in seconds
MOVE_TIMEOUT = 1.0

# --- Board Representations ---
EMPTY = ' '
X_MARK = 'X'
O_MARK = 'O'

{extra_imports}

{agent1_code}

{agent2_code}

class TicTacToeGame:
    """Manages the state and rules of the game."""
    def __init__(self):
        self.board = [EMPTY for _ in range(9)]
        self.current_turn = X_MARK

    def make_move(self, position):
        if 0 <= position < 9 and self.board[position] == EMPTY:
            self.board[position] = self.current_turn
            self.current_turn = O_MARK if self.current_turn == X_MARK else X_MARK
            return True
        return False

    def check_winner(self):
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8), # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8), # Columns
            (0, 4, 8), (2, 4, 6)             # Diagonals
        ]
        for combo in win_conditions:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != EMPTY:
                return self.board[combo[0]]
        if EMPTY not in self.board:
            return 'DRAW'
        return None

# --- Stats ---
stats = {{
    "normal": 0,
    "draw": 0,
    "c1": 0,
    "c2": 0,
    "r1_timeout": 0,
    "r1_crash": 0,
    "r1_invalid": 0,
    "r2_timeout": 0,
    "r2_crash": 0,
    "r2_invalid": 0,
}}

def print_board(board):
    print("  0 | 1 | 2")
    print(f" {{board[0]}} | {{board[1]}} | {{board[2]}}")
    print("-----------")
    print(f" {{board[3]}} | {{board[4]}} | {{board[5]}}")
    print("-----------")
    print(f" {{board[6]}} | {{board[7]}} | {{board[8]}}")

def play_game(game_num):
    """Plays a single game of Tic Tac Toe and returns the winner's name or DRAW."""
    game = TicTacToeGame()
    
    # Randomly assign symbols to agents for each game
    # In one game Agent-1 is X, in next Agent-2 is X
    if game_num % 2 == 1:
        x_agent_class = TicTacToeAgent_1
        o_agent_class = TicTacToeAgent_2
        x_name = "Agent-1"
        o_name = "Agent-2"
    else:
        x_agent_class = TicTacToeAgent_2
        o_agent_class = TicTacToeAgent_1
        x_name = "Agent-2"
        o_name = "Agent-1"

    print(f"--- GAME {{game_num}} ---")
    print(f"Symbols: {{x_name}} is {{X_MARK}}, {{o_name}} is {{O_MARK}}")

    try:
        agent_x = x_agent_class(x_name, X_MARK)
    except Exception as e:
        stats["c1" if x_name == "Agent-1" else "c2"] += 1
        return o_name
    
    try:
        agent_o = o_agent_class(o_name, O_MARK)
    except Exception as e:
        stats["c1" if o_name == "Agent-1" else "c2"] += 1
        return x_name

    agents = {{X_MARK: agent_x, O_MARK: agent_o}}
    names = {{X_MARK: x_name, O_MARK: o_name}}

    while True:
        current_symbol = game.current_turn
        current_agent = agents[current_symbol]
        current_name = names[current_symbol]
        
        move = None
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(current_agent.make_move, game.board[:])
                try:
                    move = future.result(timeout=MOVE_TIMEOUT)
                except FuturesTimeoutError:
                    if current_name == "Agent-1": stats["r1_timeout"] += 1
                    else: stats["r2_timeout"] += 1
        except Exception:
            if current_name == "Agent-1": stats["r1_crash"] += 1
            else: stats["r2_crash"] += 1

        if move is None or not isinstance(move, int) or not (0 <= move < 9) or game.board[move] != EMPTY:
            if move is not None:
                if current_name == "Agent-1": stats["r1_invalid"] += 1
                else: stats["r2_invalid"] += 1
            # Auto-fallback to random move
            available = [i for i, spot in enumerate(game.board) if spot == EMPTY]
            if available:
                move = random.choice(available)
            else:
                break # Should not happen

        game.make_move(move)
        
        winner = game.check_winner()
        if winner:
            print("Final Board:")
            print_board(game.board)
            if winner == 'DRAW':
                print("Result: DRAW")
                stats["draw"] += 1
                return "DRAW"
            else:
                print(f"Result: {{names[winner]}} wins!")
                stats["normal"] += 1
                return names[winner]

def main():
    scores = {{"Agent-1": 0, "Agent-2": 0}}
    num_games = {num_games}

    for i in range(num_games):
        result = play_game(i + 1)
        if result == "DRAW":
            scores["Agent-1"] += 0.5
            scores["Agent-2"] += 0.5
        elif result in scores:
            scores[result] += 1
        
        print(f"PROGRESS:Agent-1={{scores['Agent-1']}},Agent-2={{scores['Agent-2']}},N={{stats['normal']}},D={{stats['draw']}},C1={{stats['c1']}},C2={{stats['c2']}},R1T={{stats['r1_timeout']}},R1C={{stats['r1_crash']}},R1I={{stats['r1_invalid']}},R2T={{stats['r2_timeout']}},R2C={{stats['r2_crash']}},R2I={{stats['r2_invalid']}}")
        sys.stdout.flush()

    print(f"RESULT:Agent-1={{scores['Agent-1']}},Agent-2={{scores['Agent-2']}}")
    print(f"STATS:Normal={{stats['normal']}},Draw={{stats['draw']}},C1={{stats['c1']}},C2={{stats['c2']}},R1T={{stats['r1_timeout']}},R1C={{stats['r1_crash']}},R1I={{stats['r1_invalid']}},R2T={{stats['r2_timeout']}},R2C={{stats['r2_crash']}},R2I={{stats['r2_invalid']}}")

if __name__ == "__main__":
    main()
'''

def load_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "games" / "A2-TicTacToe.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()

def select_models(api: ModelAPI) -> tuple[str, str]:
    print("\n" + "=" * 60)
    print("TIC TAC TOE MATCH - MODEL SELECTION")
    print("=" * 60)
    print("\nAvailable models:")
    for i, model in enumerate(api.models):
        print(f"  [{i}] {model}")

    print()
    while True:
        try:
            idx1 = int(input("Select Model 1 (index): ").strip())
            if 0 <= idx1 < len(api.models): break
            print(f"Invalid index. Must be 0-{len(api.models) - 1}")
        except ValueError: print("Please enter a number.")

    while True:
        try:
            idx2 = int(input("Select Model 2 (index): ").strip())
            if 0 <= idx2 < len(api.models): break
            print(f"Invalid index. Must be 0-{len(api.models) - 1}")
        except ValueError: print("Please enter a number.")

    return api.models[idx1], api.models[idx2]

async def prompt_model(api: ModelAPI, model_name: str, prompt: str, run_id: int) -> tuple[int, str, str]:
    try:
        max_tokens = api.get_max_tokens("A2-TicTacToe")
        response = await api.call(prompt, model_name=model_name, reasoning=True, max_tokens=max_tokens)
        return run_id, model_name, response.choices[0].message.content or ""
    except Exception as e:
        logger.error("Error prompting %s: %s", model_name, e)
        return run_id, model_name, ""

def extract_agent_code(response: str, class_name: str) -> tuple[str, str]:
    blocks = re.findall(r"```(?:python)?\s*(.*?)```", response, re.DOTALL)
    code = ""
    for b in blocks:
        if "class TicTacToeAgent" in b:
            code = b
            break
    if not code and "class TicTacToeAgent" in response:
        match = re.search(r"(class TicTacToeAgent.*?)(?=\nclass\s|\ndef\s|$|if __name__)", response, re.DOTALL)
        if match: code = match.group(1)
    
    if not code: return "", ""
    code = re.sub(r"class\s+TicTacToeAgent\b", f"class {class_name}", code)
    
    imports = []
    for line in response.split("\n"):
        if (line.startswith("import ") or line.startswith("from ")) and "random" not in line:
            imports.append(line.strip())
    return code.strip(), "\n".join(imports)

def run_match(game_code: str):
    temp_file = os.path.join(tempfile.gettempdir(), f"ttt_{uuid.uuid4().hex[:8]}.py")
    try:
        with open(temp_file, "w") as f: f.write(game_code)
        result = subprocess.run(["python", temp_file], capture_output=True, text=True, timeout=300)
        return result.stdout
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

async def match_coordinator(m1_queue, m2_queue, results, num_runs, log_f, resp_f):
    for i in range(num_runs):
        id1, name1, res1 = await m1_queue.get()
        id2, name2, res2 = await m2_queue.get()
        
        code1, imp1 = extract_agent_code(res1, "TicTacToeAgent_1")
        code2, imp2 = extract_agent_code(res2, "TicTacToeAgent_2")
        
        with open(resp_f, "a") as f:
            f.write(f"--- RUN {i+1} ---\nModel 1: {res1}\nModel 2: {res2}\n\n")

        if not code1 or not code2:
            results.append({"success": False, "error": "Code extraction failed"})
            continue

        game_code = GAME_CODE_TEMPLATE.format(
            extra_imports="\n".join(set(imp1.split("\n") + imp2.split("\n"))),
            agent1_code=code1,
            agent2_code=code2,
            num_games=NUM_ROUNDS_PER_TICTACTOE_MATCH
        )
        
        output = await asyncio.get_event_loop().run_in_executor(None, run_match, game_code)
        
        with open(log_f, "a") as f:
            f.write(f"--- Run {i+1} ---\n")
            f.write(output)
            f.write("-" * 40 + "\n\n")

        res_match = re.search(r"RESULT:Agent-1=([\d.]+),Agent-2=([\d.]+)", output)
        if res_match:
            a1, a2 = float(res_match.group(1)), float(res_match.group(2))
            results.append({"success": True, "a1": a1, "a2": a2})
            print(f"  Run {i+1} complete: {a1} - {a2}")
        else:
            results.append({"success": False, "error": "Result parsing failed"})

async def main_async():
    api = ModelAPI()
    m1, m2 = select_models(api)
    prompt = load_prompt()
    
    q1, q2 = asyncio.Queue(), asyncio.Queue()
    results = []
    
    TICTACTOE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GAME_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_f = GAME_LOGS_DIR / f"{ts}_match.txt"
    resp_f = MODEL_RESPONSES_DIR / f"{ts}_responses.txt"

    tasks = []
    for i in range(1, NUM_RUNS + 1):
        tasks.append(asyncio.create_task(prompt_model(api, m1, prompt, i)))
        tasks.append(asyncio.create_task(prompt_model(api, m2, prompt, i)))
    
    p_results = await asyncio.gather(*tasks)
    for i, res in enumerate(p_results):
        if i % 2 == 0: await q1.put(res)
        else: await q2.put(res)
        
    await match_coordinator(q1, q2, results, NUM_RUNS, log_f, resp_f)
    
    print("\nFINAL RESULTS:")
    total1 = sum(r["a1"] for r in results if r["success"])
    total2 = sum(r["a2"] for r in results if r["success"])
    print(f"Agent-1 Total: {total1}")
    print(f"Agent-2 Total: {total2}")

if __name__ == "__main__":
    asyncio.run(main_async())
