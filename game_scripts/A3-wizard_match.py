"""
Wizard Match Runner: Orchestrates 6-player Wizard card games between AI models.

Prompts 6 models to implement WizardAgent, extracts their code, runs games,
and reports rankings based on total scores.
"""

import argparse
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

# Add utils directory to sys.path
sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging

logger = setup_logging(__name__)

# Load environment variables
load_dotenv()

# Configuration
NUM_PLAYERS = 6
NUM_MODELS = 3  # 3 models, each prompted twice
NUM_PROMPTS_PER_MODEL = 2  # Each model generates 2 agents
NUM_ROUNDS = 10  # 60 cards / 6 players = 10 rounds
try:
    NUM_GAMES_IN_WIZARD_MATCH = int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100"))
except (ValueError, TypeError):
    NUM_GAMES_IN_WIZARD_MATCH = 100

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

# Results directories
WIZARD_RESULTS_DIR = Path(__file__).parent.parent / "results" / "wizard"
GAME_LOGS_DIR = WIZARD_RESULTS_DIR / "game_logs"
MODEL_RESPONSES_DIR = WIZARD_RESULTS_DIR / "model_responses"

# Stored agents directory
AGENTS_DIR = Path(__file__).parent.parent / "agents"
GAME_NAME = "A3-Wizard"  # Default game for stored agents

# The game code template with placeholders for agent implementations
GAME_CODE_TEMPLATE = '''
import sys
import random
import signal
# Move timeout in seconds
MOVE_TIMEOUT = {move_timeout}

class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")

NUM_PLAYERS = {num_players}
NUM_ROUNDS = {num_rounds}
NUM_GAMES = {num_games}
DEBUG_MODE = {debug_mode}
HUMAN_MODE = {human_mode}

{extra_imports}

{card_class}

{agent_code}

{game_class}

# --- Stats ---
stats = {{
    "p1_timeout": 0, "p1_crash": 0, "p1_invalid": 0,
    "p2_timeout": 0, "p2_crash": 0, "p2_invalid": 0,
    "p3_timeout": 0, "p3_crash": 0, "p3_invalid": 0,
    "p4_timeout": 0, "p4_crash": 0, "p4_invalid": 0,
    "p5_timeout": 0, "p5_crash": 0, "p5_invalid": 0,
    "p6_timeout": 0, "p6_crash": 0, "p6_invalid": 0,
}}

def debug_wait(message="Press Enter to continue..."):
    """Wait for user input in debug mode."""
    if DEBUG_MODE:
        input(f"\\n[DEBUG] {{message}}")

def call_agent_with_timeout(agent, phase, game_state):
    """Call agent's make_move with timeout protection."""
    agent_idx = int(agent.name.split("-")[1])
    stat_prefix = f"p{{agent_idx}}"
    
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(MOVE_TIMEOUT))
        try:
            return agent.make_move(phase, game_state)
        finally:
            signal.alarm(0)
    except MoveTimeoutException:
        stats[f"{{stat_prefix}}_timeout"] += 1
        return None
    except Exception:
        stats[f"{{stat_prefix}}_crash"] += 1
        return None

def play_game(game_num, total_scores):
    """Play one complete game of Wizard (10 rounds) and update scores."""
    game = WizardGame(NUM_PLAYERS)
    
    # Initialize agents
    agents = []
    for i in range(NUM_PLAYERS):
        class_name = f"WizardAgent_{{i+1}}"
        try:
            agent_class = globals()[class_name]
            agent = agent_class(f"Player-{{i+1}}")
            agents.append(agent)
        except Exception as e:
            print(f"ERROR: Failed to initialize {{class_name}}: {{e}}")
            return False
    
    print(f"\\n{{'='*60}}")
    print(f"GAME {{game_num}}")
    print(f"{{'='*60}}")
    
    # Play all rounds
    for round_num in range(1, NUM_ROUNDS + 1):
        game.start_round(round_num)
        print(f"\\n--- Round {{round_num}} ({{round_num}} cards each) ---")
        print(f"Trump: {{game.trump_suit if game.trump_suit else 'None'}}")
        
        if DEBUG_MODE or HUMAN_MODE:
            print(f"\\n[DEBUG] Cards dealt:")
            for i in range(NUM_PLAYERS):
                if HUMAN_MODE and i != 0: continue # Only show Human's cards or debug all
                hand_str = ", ".join([str(card) for card in game.hands[i]])
                print(f"  Player-{{i+1}}: {{hand_str}}")
            if DEBUG_MODE:
                debug_wait("Cards dealt. Press Enter to start bidding...")
        
        # Bidding phase
        for i, agent in enumerate(agents):
            game_state = game.get_game_state(i, "bid")
            bid = call_agent_with_timeout(agent, "bid", game_state)
            
            # Validate bid
            if not isinstance(bid, int) or bid < 0 or bid > game.cards_this_round:
                stats[f"p{{i+1}}_invalid"] += 1
                bid = random.randint(0, game.cards_this_round)
            
            # Hook rule: last bidder cannot make total bids equal total tricks
            if i == NUM_PLAYERS - 1:
                current_sum = sum(b for b in game.bids if b is not None)
                forbidden_bid = game.cards_this_round - current_sum
                if 0 <= forbidden_bid <= game.cards_this_round and bid == forbidden_bid:
                    stats[f"p{{i+1}}_invalid"] += 1
                    # Pick a random valid bid that isn't forbidden
                    valid_bids = [b for b in range(0, game.cards_this_round + 1) if b != forbidden_bid]
                    bid = random.choice(valid_bids) if valid_bids else 0
            
            game.record_bid(i, bid)
            
            if DEBUG_MODE:
                print(f"  Player-{{i+1}} bids: {{bid}}")
        
        print(f"Bids: {{game.bids}}")
        
        print(f"Bids: {{game.bids}}")
        
        if DEBUG_MODE:
            debug_wait("Bidding complete. Press Enter to start playing tricks...")
        
        # Playing phase - play all tricks for this round
        for trick_num in range(game.cards_this_round):
            game.start_trick()
            
            if DEBUG_MODE:
                print(f"\\n  Trick {{trick_num + 1}}/{{game.cards_this_round}}:")
            
            for _ in range(NUM_PLAYERS):
                current_player = game.current_player
                agent = agents[current_player]
                game_state = game.get_game_state(current_player, "play")
                
                card = call_agent_with_timeout(agent, "play", game_state)
                
                # Validate and play card
                valid_card = game.validate_and_play(current_player, card)
                if valid_card != card:
                    stats[f"p{{current_player+1}}_invalid"] += 1
                
                if DEBUG_MODE:
                    print(f"    Player-{{current_player+1}} plays: {{valid_card}}")
            
            winner = game.finish_trick()
            
            if DEBUG_MODE:
                print(f"  → Player-{{winner+1}} wins the trick!")
                debug_wait(f"Trick {{trick_num + 1}} complete. Press Enter to continue...")
        
        # Score the round
        game.score_round()
        print(f"Tricks won: {{game.tricks_won}}")
        print(f"Round scores: {{[game.total_scores[i] - total_scores[i] for i in range(NUM_PLAYERS)]}}")
        
        if DEBUG_MODE:
            print("\\n[DEBUG] Round scoring details:")
            for i in range(NUM_PLAYERS):
                bid = game.bids[i]
                won = game.tricks_won[i]
                round_score = game.total_scores[i] - total_scores[i]
                status = "✓" if bid == won else "✗"
                print(f"  Player-{{i+1}}: Bid {{bid}}, Won {{won}} {{status}} → {{round_score:+d}} points")
            debug_wait(f"Round {{round_num}} complete. Press Enter to continue...")
    
    # Update total scores
    for i in range(NUM_PLAYERS):
        total_scores[i] += game.total_scores[i]
    
    print(f"\\nGame {{game_num}} complete!")
    print(f"Game scores: {{game.total_scores}}")
    print(f"Running totals: {{total_scores}}")
    
    # Print progress
    progress_str = f"PROGRESS:Game={{game_num}}"
    for i in range(NUM_PLAYERS):
        progress_str += f",P{{i+1}}={{total_scores[i]}}"
    for i in range(NUM_PLAYERS):
        progress_str += f",P{{i+1}}T={{stats[f'p{{i+1}}_timeout']}},P{{i+1}}C={{stats[f'p{{i+1}}_crash']}},P{{i+1}}I={{stats[f'p{{i+1}}_invalid']}}"
    print(progress_str)
    sys.stdout.flush()
    
    return True

def main():
    """Main function to run the Wizard simulation."""
    total_scores = [0] * NUM_PLAYERS
    
    for i in range(NUM_GAMES):
        success = play_game(i + 1, total_scores)
        if not success:
            print(f"ERROR: Game {{i+1}} failed to complete")
            break
    
    # Final results
    result_str = "RESULT:"
    result_str += ",".join([f"P{{i+1}}={{total_scores[i]}}" for i in range(NUM_PLAYERS)])
    print(f"\\n{{result_str}}")
    
    stats_str = "STATS:"
    stats_parts = []
    for i in range(NUM_PLAYERS):
        stats_parts.append(f"P{{i+1}}T={{stats[f'p{{i+1}}_timeout']}}")
        stats_parts.append(f"P{{i+1}}C={{stats[f'p{{i+1}}_crash']}}")
        stats_parts.append(f"P{{i+1}}I={{stats[f'p{{i+1}}_invalid']}}")
    print(stats_str + ",".join(stats_parts))

if __name__ == "__main__":
    main()
'''

CARD_CLASS = '''
class Card:
    """Represents a single card in the Wizard deck."""
    def __init__(self, card_type, suit=None, rank=None):
        """
        card_type: "wizard", "jester", or "standard"
        suit: "Hearts", "Diamonds", "Clubs", "Spades" (only for standard cards)
        rank: 2-14 where Jack=11, Queen=12, King=13, Ace=14 (only for standard cards)
        """
        self.card_type = card_type
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        if self.card_type == "wizard":
            return "Wizard"
        elif self.card_type == "jester":
            return "Jester"
        else:
            rank_str = {11: "J", 12: "Q", 13: "K", 14: "A"}.get(self.rank, str(self.rank))
            suit_str = self.suit[0]
            return f"{rank_str}{suit_str}"
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return (self.card_type == other.card_type and 
                self.suit == other.suit and 
                self.rank == other.rank)
    
    def __hash__(self):
        return hash((self.card_type, self.suit, self.rank))
'''

GAME_CLASS = '''
class WizardGame:
    """Manages the complete Wizard game state and rules."""
    
    SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
    
    def __init__(self, num_players):
        self.num_players = num_players
        self.deck = self._create_deck()
        self.total_scores = [0] * num_players
        
        # Round state
        self.round_number = 0
        self.cards_this_round = 0
        self.trump_suit = None
        self.hands = [[] for _ in range(num_players)]
        self.bids = [None] * num_players
        self.tricks_won = [0] * num_players
        
        # Trick state
        self.current_trick = []
        self.current_player = 0
        self.trick_leader = 0
    
    def _create_deck(self):
        """Create a full 60-card Wizard deck."""
        deck = []
        
        # Add 4 Wizards
        for _ in range(4):
            deck.append(Card("wizard"))
        
        # Add 4 Jesters
        for _ in range(4):
            deck.append(Card("jester"))
        
        # Add 52 standard cards
        for suit in self.SUITS:
            for rank in range(2, 15):  # 2-14 (Ace=14)
                deck.append(Card("standard", suit, rank))
        
        return deck
    
    def start_round(self, round_num):
        """Start a new round by dealing cards and determining trump."""
        self.round_number = round_num
        self.cards_this_round = round_num
        self.bids = [None] * self.num_players
        self.tricks_won = [0] * self.num_players
        
        # Shuffle and deal
        random.shuffle(self.deck)
        self.hands = [[] for _ in range(self.num_players)]
        
        card_idx = 0
        for i in range(self.num_players):
            for _ in range(self.cards_this_round):
                self.hands[i].append(self.deck[card_idx])
                card_idx += 1
        
        # Determine trump
        total_dealt = self.num_players * self.cards_this_round
        if total_dealt < len(self.deck):
            trump_card = self.deck[total_dealt]
            if trump_card.card_type == "wizard":
                # Dealer chooses - for simplicity, choose random suit
                self.trump_suit = random.choice(self.SUITS)
            elif trump_card.card_type == "jester":
                self.trump_suit = None
            else:
                self.trump_suit = trump_card.suit
        else:
            self.trump_suit = None
        
        self.current_player = 0
    
    def record_bid(self, player_idx, bid):
        """Record a player's bid."""
        self.bids[player_idx] = bid
    
    def start_trick(self):
        """Start a new trick."""
        self.current_trick = []
    
    def get_game_state(self, player_idx, phase):
        """Get the complete public game state for a player."""
        return {
            "round_number": self.round_number,
            "cards_this_round": self.cards_this_round,
            "trump_suit": self.trump_suit,
            "my_hand": self.hands[player_idx][:],
            "my_position": player_idx,
            "current_trick": self.current_trick[:],
            "trick_leader": self.trick_leader if self.current_trick else None,
            "bids": self.bids[:],
            "tricks_won": self.tricks_won[:],
            "scores": self.total_scores[:],
        }
    
    def _get_led_suit(self):
        """Determine the suit that was led (first non-Wizard/Jester standard card)."""
        for _, card in self.current_trick:
            if card.card_type == "standard":
                return card.suit
        return None
    
    def _get_valid_cards(self, player_idx):
        """Get list of valid cards the player can play."""
        hand = self.hands[player_idx]
        
        # First to play or only Wizards/Jesters played - can play anything
        led_suit = self._get_led_suit()
        if led_suit is None:
            return hand[:]
        
        # Check if player has cards in led suit
        cards_in_suit = [c for c in hand if c.card_type == "standard" and c.suit == led_suit]
        wizards_and_jesters = [c for c in hand if c.card_type in ["wizard", "jester"]]
        
        if cards_in_suit:
            # Must play led suit or Wizard/Jester
            return cards_in_suit + wizards_and_jesters
        else:
            # No cards in led suit - can play anything
            return hand[:]
    
    def validate_and_play(self, player_idx, card):
        """Validate the card play and execute it. Returns the actual card played."""
        hand = self.hands[player_idx]
        valid_cards = self._get_valid_cards(player_idx)
        
        # Check if card is in hand and valid
        if card not in hand:
            # Card not in hand - play random valid card
            card = random.choice(valid_cards) if valid_cards else random.choice(hand)
        elif card not in valid_cards:
            # Card is in hand but not valid - play random valid card
            card = random.choice(valid_cards)
        
        # Play the card
        self.hands[player_idx].remove(card)
        self.current_trick.append((player_idx, card))
        self.current_player = (self.current_player + 1) % self.num_players
        
        return card
    
    def finish_trick(self):
        """Determine trick winner and award the trick."""
        winner = self._determine_trick_winner()
        self.tricks_won[winner] += 1
        self.current_player = winner
        self.trick_leader = winner
        return winner
    
    def _determine_trick_winner(self):
        """Determine who won the current trick."""
        # Check for Wizards (first Wizard wins)
        for player_idx, card in self.current_trick:
            if card.card_type == "wizard":
                return player_idx
        
        # Check if all Jesters (first Jester wins)
        if all(card.card_type == "jester" for _, card in self.current_trick):
            return self.current_trick[0][0]
        
        # Find highest card
        led_suit = self._get_led_suit()
        best_player = None
        best_card = None
        
        for player_idx, card in self.current_trick:
            if card.card_type == "jester":
                continue
            
            if best_card is None:
                best_player = player_idx
                best_card = card
                continue
            
            # Compare cards
            if self._card_beats(card, best_card, led_suit):
                best_player = player_idx
                best_card = card
        
        return best_player
    
    def _card_beats(self, card1, card2, led_suit):
        """Returns True if card1 beats card2."""
        # Wizards handled separately
        # Jesters always lose
        if card1.card_type == "jester":
            return False
        if card2.card_type == "jester":
            return True
        
        # Both standard cards
        card1_is_trump = (card1.suit == self.trump_suit)
        card2_is_trump = (card2.suit == self.trump_suit)
        
        if card1_is_trump and not card2_is_trump:
            return True
        if card2_is_trump and not card1_is_trump:
            return False
        
        # Both trump or both non-trump
        # If both in led suit or both trump, compare ranks
        if card1.suit == card2.suit:
            return card1.rank > card2.rank
        
        # Different suits - card in led suit wins
        if card1.suit == led_suit:
            return True
        if card2.suit == led_suit:
            return False
        
        # Neither in led suit (shouldn't happen with valid play)
        return card1.rank > card2.rank
    
    def score_round(self):
        """Score the round based on bids vs tricks won."""
        for i in range(self.num_players):
            bid = self.bids[i]
            won = self.tricks_won[i]
            
            if bid == won:
                # Correct bid
                score = 20 + (10 * won)
            else:
                # Incorrect bid
                score = -10 * abs(bid - won)
            
            self.total_scores[i] += score
'''


def load_prompt() -> str:
    """Load the Wizard prompt from the games directory."""
    prompt_path = Path(__file__).parent.parent / "games" / "A3-Wizard.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text()


def find_model_folder(pattern: str) -> str | None:
    """
    Find a model folder matching the given pattern.
    
    Returns the folder name if exactly one match found, None otherwise.
    Prints warning if multiple matches found.
    """
    if not AGENTS_DIR.exists():
        print(f"ERROR: Agents directory not found: {AGENTS_DIR}")
        return None

    # Exact match first (matchmaker passes full folder names)
    exact = AGENTS_DIR / pattern
    if exact.is_dir():
        return pattern

    # Substring fallback for interactive CLI use
    matches = [
        d.name for d in AGENTS_DIR.iterdir()
        if d.is_dir() and pattern.lower() in d.name.lower()
    ]

    if not matches:
        print(f"ERROR: No model folder matches pattern '{pattern}'")
        return None
    
    if len(matches) > 1:
        return ModelAPI.resolve_model_interactive(pattern, matches, context="folder")
    
    return matches[0]


def load_stored_agent(model_folder: str, game: str, run: int, agent_idx: int) -> tuple[str, str]:
    """
    Load agent code from a stored file and rename the class.
    
    Returns tuple of (renamed_code, imports).
    """
    agent_file = AGENTS_DIR / model_folder / f"{game}_{run}.py"
    
    if not agent_file.exists():
        print(f"ERROR: Agent file not found: {agent_file}")
        return "", ""
    
    content = agent_file.read_text()
    
    # Extract the class definition (everything after the docstring header)
    # The file format has a docstring header then imports then class
    lines = content.split("\n")
    
    # Skip the header docstring (lines starting with """ or within it)
    code_start = 0
    in_docstring = False
    for i, line in enumerate(lines):
        if '"""' in line:
            if in_docstring:
                code_start = i + 1
                break
            else:
                in_docstring = True
    
    code_lines = lines[code_start:]
    code = "\n".join(code_lines)
    
    # Extract imports
    imports = []
    for line in code_lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:  # random is in template
                imports.append(stripped)
    
    # Rename WizardAgent to WizardAgent_{agent_idx}
    new_class_name = f"WizardAgent_{agent_idx}"
    code = re.sub(r"class\s+WizardAgent\b", f"class {new_class_name}", code)
    
    return code.strip(), "\n".join(imports)


def parse_agent_specs(agents_str: str) -> list[tuple[str, int]]:
    """
    Parse agent specification string into list of (model_pattern, run_number) tuples.
    
    Format: "model1:run1,model1:run2,model2:run1,..."
    """
    specs = []
    for spec in agents_str.split(","):
        spec = spec.strip()
        if ":" not in spec:
            print(f"ERROR: Invalid agent spec '{spec}'. Expected format: model:run")
            continue
        
        parts = spec.split(":", 1)
        try:
            model_pattern = parts[0].strip()
            run_num = int(parts[1].strip())
            specs.append((model_pattern, run_num))
        except ValueError:
            print(f"ERROR: Invalid run number in spec '{spec}'")
    
    return specs


def load_all_stored_agents(agent_specs: list[tuple[str, int]], game: str) -> list[tuple[str, str, str]]:
    """
    Load all agents from stored files.
    
    Returns list of (agent_idx, model_folder, code) tuples.
    """
    agents = []
    all_imports = []
    
    for i, (model_pattern, run_num) in enumerate(agent_specs, 1):
        model_folder = find_model_folder(model_pattern)
        if not model_folder:
            return []
        
        code, imports = load_stored_agent(model_folder, game, run_num, i)
        if not code:
            return []
        
        agents.append((i, model_folder, code))
        if imports:
            all_imports.extend(imports.split("\n"))
    
    return agents, list(set(imp for imp in all_imports if imp.strip()))



def select_models(api: ModelAPI) -> list[str]:
    """Interactive model selection for the 3 competing models."""
    print("\n" + "=" * 60)
    print("WIZARD MATCH - MODEL SELECTION")
    print("=" * 60)
    print("\nAvailable models:")
    for i, model in enumerate(api.models):
        print(f"  [{i}] {model}")

    print(f"\nSelect {NUM_MODELS} models. Each model will control 2 agents (total {NUM_PLAYERS} players).")
    
    selected = []
    for model_num in range(1, NUM_MODELS + 1):
        while True:
            try:
                idx = int(input(f"Select Model {model_num} (index): ").strip())
                if 0 <= idx < len(api.models):
                    selected.append(api.models[idx])
                    break
                print(f"Invalid index. Must be 0-{len(api.models) - 1}")
            except ValueError:
                print("Please enter a number.")
    
    print("\nMatch setup:")
    for i, model in enumerate(selected, 1):
        # Consistent with populate_agents.py naming rule
        name_to_use = model.split("@")[0]
        parts = model.split("/")
        if len(parts) >= 3:
            flavor = parts[2]
            if flavor not in name_to_use:
                name_to_use = f"{name_to_use}-{flavor}"
        short_name = name_to_use.replace("/", "-")
        print(f"  Model {i} ({short_name}): Will be prompted {NUM_PROMPTS_PER_MODEL} times → Agent-{i*2-1} and Agent-{i*2}")
    print(f"  Total: 1 game with {NUM_ROUNDS} rounds")
    
    return selected


async def prompt_model(api: ModelAPI, model_name: str, prompt: str, run_id: int) -> tuple[int, str, str]:
    """Call a model with the Wizard prompt and return its response."""
    try:
        logger.info("Prompting model: %s (run %d)", model_name, run_id)
        max_tokens = api.get_max_tokens(GAME_NAME)
        response = await api.call(prompt, model_name=model_name, reasoning=True, max_tokens=max_tokens)
        content = response.choices[0].message.content or ""
        logger.info("Received response from %s (run %d): %d chars", model_name, run_id, len(content))
        return run_id, model_name, content
    except Exception as e:
        logger.error("Error prompting %s: %s", model_name, e)
        return run_id, model_name, ""


def extract_agent_code(response: str, class_name: str) -> tuple[str, str]:
    """Extract WizardAgent class from model response and rename it."""
    # Find code blocks
    blocks = re.findall(r"```(?:python)?\\s*(.*?)```", response, re.DOTALL)
    code = ""
    
    # Look for WizardAgent class
    for b in blocks:
        if "class WizardAgent" in b:
            code = b
            break
    
    # Fallback: search in raw text
    if not code and "class WizardAgent" in response:
        match = re.search(r"(class WizardAgent.*?)(?=\\nclass\\s|\\ndef\\s|$|if __name__)", response, re.DOTALL)
        if match:
            code = match.group(1)
    
    if not code:
        return "", ""
    
    # Rename the class
    code = re.sub(r"class\\s+WizardAgent\\b", f"class {class_name}", code)
    
    # Extract imports (excluding random which is in template)
    imports = []
    for line in response.split("\\n"):
        if (line.startswith("import ") or line.startswith("from ")) and "random" not in line:
            imports.append(line.strip())
    
    return code.strip(), "\\n".join(imports)


def run_match(game_code: str, debug_mode: bool = False) -> str:
    """Execute the match and return output."""
    temp_file = os.path.join(tempfile.gettempdir(), f"wizard_{uuid.uuid4().hex[:8]}.py")
    try:
        with open(temp_file, "w") as f:
            f.write(game_code)
        # In debug mode, run with stdin=sys.stdin to allow input
        if debug_mode:
            result = subprocess.run(["python", temp_file], text=True, timeout=600)
            return "DEBUG_MODE_RUN"
        else:
            result = subprocess.run(["python", temp_file], capture_output=True, text=True, timeout=600)
        return result.stdout
    except Exception as e:
        return f"ERROR: {{e}}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def run_match_human(game_code: str) -> None:
    temp_file = os.path.join(tempfile.gettempdir(), f"wizard_human_{{uuid.uuid4().hex[:8]}}.py")
    try:
        with open(temp_file, "w") as f: f.write(game_code)
        subprocess.call(["python", temp_file])
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)


async def run_single_game(responses, log_f, resp_f, models, debug_mode=False):
    """Run a single game with the 6 agents from the responses."""
    # Log responses
    with open(resp_f, "a") as f:
        f.write(f"--- AGENT RESPONSES ---\\n")
        for i, (prompt_id, mname, content) in enumerate(responses, 1):
            f.write(f"Agent {i} from {mname} (prompt #{prompt_id}):\\n{content}\\n\\n")
        f.write("-" * 80 + "\\n\\n")
    
    # Extract agent code for all 6 agents (already 6 responses, no duplication needed)
    agent_codes = []
    all_imports = []
    
    for i, (_, _, content) in enumerate(responses, 1):
        code, imports = extract_agent_code(content, f"WizardAgent_{i}")
        if not code:
            return {"success": False, "error": f"Code extraction failed for Agent {i}"}
        
        agent_codes.append(code)
        if imports:
            all_imports.extend(imports.split("\\n"))
    
    # Check if extraction succeeded
    if len(agent_codes) != NUM_PLAYERS:
        return {"success": False, "error": "Code extraction failed"}
        
    # Build game code
    extra_imports = "\\n".join(set(imp for imp in all_imports if imp.strip()))
    combined_agent_code = "\\n\\n".join(agent_codes)
    
    game_code = GAME_CODE_TEMPLATE.format(
        num_players=NUM_PLAYERS,
        num_rounds=NUM_ROUNDS,
        num_games=NUM_GAMES_IN_WIZARD_MATCH,
        debug_mode=str(debug_mode),
        extra_imports=extra_imports,
        card_class=CARD_CLASS,
        agent_code=combined_agent_code,
        move_timeout=MOVE_TIME_LIMIT,
        game_class=GAME_CLASS
    )
        
    # Run match
    if debug_mode:
        output = run_match(game_code, debug_mode)
    else:
        output = await asyncio.get_event_loop().run_in_executor(None, run_match, game_code, False)
    
    with open(log_f, "a") as f:
        f.write(f"--- GAME LOG ---\\n")
        f.write(output)
        f.write("-" * 40 + "\\n\\n")
    
    # Parse results
    if debug_mode:
        return {"success": True, "scores": {f"P{i+1}": 0 for i in range(NUM_PLAYERS)}}
    
    result_match = re.search(r"RESULT:(.+)", output)
    if result_match:
        result_str = result_match.group(1)
        scores = {}
        for part in result_str.split(","):
            if "=" in part:
                player, score = part.split("=")
                scores[player.strip()] = int(score.strip())
        return {"success": True, "scores": scores}
    else:
        return {"success": False, "error": "Result parsing failed"}


async def main_async(debug_mode=False):
    """Main async entry point."""
    api = ModelAPI()
    
    # Validate minimum models
    if len(api.models) < NUM_MODELS:
        print(f"ERROR: Need at least {NUM_MODELS} models available. Found {len(api.models)}.")
        return
    
    models = select_models(api)
    prompt = load_prompt()
    
    # Create directories
    WIZARD_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GAME_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_f = GAME_LOGS_DIR / f"{ts}_game.txt"
    resp_f = MODEL_RESPONSES_DIR / f"{ts}_responses.txt"
    
    # Fire all prompts concurrently (3 models × 2 prompts each = 6 total)
    print("\nPrompting models...")
    tasks = []
    prompt_id = 1
    for model in models:
        for _ in range(NUM_PROMPTS_PER_MODEL):
            tasks.append(asyncio.create_task(prompt_model(api, model, prompt, prompt_id)))
            prompt_id += 1
    
    responses = await asyncio.gather(*tasks)
    
    # Run the single game
    if debug_mode:
        print("\n" + "=" * 60)
        print("DEBUG MODE ENABLED")
        print("=" * 60)
        print("You will be prompted at each stage of the game.")
        print("Game state and decisions will be displayed in detail.\n")
    
    print("\nRunning game...")
    result = await run_single_game(responses, log_f, resp_f, models, debug_mode)
    
    if not result["success"]:
        print(f"\nERROR: {result.get('error', 'Game failed')}")
        return
    
    # Calculate final rankings
    print("\n" + "=" * 60)
    print("FINAL RANKINGS")
    print("=" * 60)
    
    agent_scores = result["scores"]
    
    # Aggregate by model
    model_scores = {}
    for i, model in enumerate(models, 1):
        agent1 = f"P{i*2-1}"
        agent2 = f"P{i*2}"
        total = agent_scores[agent1] + agent_scores[agent2]
        model_short = model.split("/")[-1].split("@")[0]
        model_scores[model_short] = {
            "total": total,
            "agent1_score": agent_scores[agent1],
            "agent2_score": agent_scores[agent2],
            "agent1_name": agent1,
            "agent2_name": agent2,
        }
    
    # Sort by total score
    rankings = sorted(model_scores.items(), key=lambda x: x[1]["total"], reverse=True)
    
    # Show individual agents first
    print("\\nIndividual Agent Leaderboard:")
    agent_rankings = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (agent, score) in enumerate(agent_rankings, 1):
        agent_idx = int(agent[1:]) - 1
        model_idx = agent_idx // 2
        model_name = models[model_idx].split("/")[-1].split("@")[0]
        print(f"  {rank}. {agent} ({model_name}): {score} points")
    
    # Then show aggregated by model
    print("\\nAggregated by Model (combined score of both agents):")
    for rank, (model_name, data) in enumerate(rankings, 1):
        print(f"  {rank}. {model_name}: {data['total']} points")
        print(f"      {data['agent1_name']}: {data['agent1_score']} | {data['agent2_name']}: {data['agent2_score']}")


def run_stored_game(agent_codes: list[tuple[int, str, str]], imports: list[str], debug_mode: bool = False) -> dict:
    """Run a game with pre-loaded stored agents."""
    # Build the combined agent code
    combined_agent_code = "\n\n".join(code for _, _, code in agent_codes)
    extra_imports = "\n".join(imports)
    
    game_code = GAME_CODE_TEMPLATE.format(
        num_players=NUM_PLAYERS,
        num_rounds=NUM_ROUNDS,
        num_games=NUM_GAMES_IN_WIZARD_MATCH,
        debug_mode=str(debug_mode),
        extra_imports=extra_imports,
        card_class=CARD_CLASS,
        agent_code=combined_agent_code,
        move_timeout=MOVE_TIME_LIMIT,
        game_class=GAME_CLASS
    )
    
    # Run the match
    if debug_mode:
        output = run_match(game_code, debug_mode)
    else:
        output = run_match(game_code, False)
    
    # Parse results
    if debug_mode:
        return {"success": True, "scores": {f"P{i+1}": 0 for i in range(NUM_PLAYERS)}}
    
    result_match = re.search(r"RESULT:(.+)", output)
    if result_match:
        result_str = result_match.group(1)
        scores = {}
        for part in result_str.split(","):
            if "=" in part:
                player, score = part.split("=")
                scores[player.strip()] = int(score.strip())
        return {"success": True, "scores": scores}
    else:
        return {"success": False, "error": f"Result parsing failed. Output:\n{output[:500]}"}


def main_stored(agents_str: str, game: str, debug_mode: bool = False):
    """Main function for stored agent mode."""
    print("\n" + "=" * 60)
    print("WIZARD MATCH - STORED AGENT MODE")
    print("=" * 60)
    
    # Parse agent specifications
    agent_specs = parse_agent_specs(agents_str)
    
    if len(agent_specs) != NUM_PLAYERS:
        print(f"\nERROR: Need exactly {NUM_PLAYERS} agents, got {len(agent_specs)}")
        print("Example: --agents mistral:1,mistral:2,mistral:3,fp8:1,fp8:2,fp8:3")
        return
    
    print(f"\nLoading {NUM_PLAYERS} agents for game: {game}")
    for i, (model, run) in enumerate(agent_specs, 1):
        print(f"  Agent-{i}: {model} (run {run})")
    
    # Load all agents
    result = load_all_stored_agents(agent_specs, game)
    if not result or not result[0]:
        print("\nERROR: Failed to load agents")
        return
    
    agents, imports = result
    print(f"\nLoaded {len(agents)} agents successfully")
    
    # Create log directories
    WIZARD_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GAME_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_f = GAME_LOGS_DIR / f"{ts}_stored_game.txt"
    
    # Log agent info
    with open(log_f, "w") as f:
        f.write(f"Stored Agent Game - {ts}\n")
        f.write("=" * 60 + "\n")
        for i, (model, run) in enumerate(agent_specs, 1):
            f.write(f"Agent-{i}: {model} (run {run})\n")
        f.write("\n")
    
    # Run game
    if debug_mode:
        print("\n" + "=" * 60)
        print("DEBUG MODE ENABLED")
        print("=" * 60)
    
    print("\nRunning game...")
    result = run_stored_game(agents, imports, debug_mode)
    
    # Log output
    with open(log_f, "a") as f:
        f.write(f"Result: {result}\n")
    
    if not result["success"]:
        print(f"\nERROR: {result.get('error', 'Game failed')}")
        return
    
    # Show rankings
    print("\n" + "=" * 60)
    print("FINAL RANKINGS")
    print("=" * 60)
    
    agent_scores = result["scores"]
    
    # Individual agent rankings with model info
    print("\nIndividual Agent Leaderboard:")
    agent_rankings = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (agent, score) in enumerate(agent_rankings, 1):
        agent_idx = int(agent[1:]) - 1
        model_pattern, run_num = agent_specs[agent_idx]
        print(f"  {rank}. {agent} ({model_pattern}:{run_num}): {score} points")
    
    print(f"\nGame log saved to: {log_f}")


def get_available_runs(model_folder: str, game: str) -> list[int]:
    """Get list of available run IDs for a model and game."""
    model_dir = AGENTS_DIR / model_folder
    runs = []
    pattern = re.compile(rf"^{re.escape(game)}_(\d+)\.py$")
    
    for file in model_dir.glob(f"{game}_*.py"):
        match = pattern.match(file.name)
        if match:
            runs.append(int(match.group(1)))
    
    return sorted(runs)


def parse_agent_spec(spec: str) -> tuple[str, list[int]]:
    """Parse agent spec (model:run1:run2) into model pattern and list of runs."""
    parts = spec.split(":")
    model_pattern = parts[0]
    runs = [int(r) for r in parts[1:]]
    return model_pattern, runs


async def run_game_async(game_id: int, game_agents: list[tuple[str, int]], log_f: Path, debug_mode: bool = False):
    """Run a single 6-player Wizard game and return the results."""
    loaded_agents = []
    all_imports = []
    
    for idx, (folder, run) in enumerate(game_agents, 1):
        code, imports = load_stored_agent(folder, GAME_NAME, run, idx)
        if not code:
            return {"success": False, "error": f"Failed to load agent {idx}", "game_id": game_id}
        loaded_agents.append((idx, folder, code))
        if imports:
            all_imports.extend(imports.split("\n"))

    result = await asyncio.get_event_loop().run_in_executor(None, run_stored_game, loaded_agents, list(set(all_imports)), debug_mode)
    
    with open(log_f, "a") as f:
        f.write(f"--- Game {game_id} ---\n")
        for idx, (folder, run) in enumerate(game_agents, 1):
            f.write(f"Slot {idx}: {folder} (run {run})\n")
        f.write(f"Result: {result}\n")
        f.write("-" * 40 + "\n\n")
        
    result["game_id"] = game_id
    result["game_agents"] = game_agents
    return result


async def main_async():
    parser = argparse.ArgumentParser(description="Run Wizard matches between stored AI agents")
    parser.add_argument("--agent", nargs="+", help="Agent specs: model1[:run1:run2] model2[:run3:run4] ...")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--human", action="store_true", help="Play interactively against random bots")
    args = parser.parse_args()

    if args.human:
        print("\n" + "=" * 60)
        print("WIZARD HUMAN MODE")
        print("You are playing against 5 RandomBots.")
        print("=" * 60)
        
        # Build agent aliases code
        agent_code = """
class RandomAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, phase, game_state):
        if phase == "bid":
            return random.randint(0, game_state['cards_this_round'])
        else: # play
            return random.choice(game_state['my_hand'])

class HumanAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, phase, game_state):
        print(f"\\n--- YOUR TURN ({phase}) ---")
        if phase == "bid":
             print(f"Round: {game_state['round_number']} ({game_state['cards_this_round']} cards)")
             print(f"Trump: {game_state['trump_suit']}")
             print(f"Hand: {[str(c) for c in game_state['my_hand']]}")
             while True:
                try:
                    bid = int(input(f"Enter Bid [0-{game_state['cards_this_round']}]: ").strip())
                    if 0 <= bid <= game_state['cards_this_round']: return bid
                    print("Invalid bid.")
                except ValueError: print("Enter a number.")
        else:
             print(f"Trick so far: {[(i+1, str(c)) for i,c in game_state['current_trick']]}")
             # trick_leader is player index. Derived led suit is implicit.
             print(f"Hand: {[(i, str(c)) for i,c in enumerate(game_state['my_hand'])]}")
             while True:
                try:
                    idx = int(input(f"Select Card Index [0-{len(game_state['my_hand'])-1}]: ").strip())
                    if 0 <= idx < len(game_state['my_hand']):
                        return game_state['my_hand'][idx]
                    print("Invalid index.")
                except ValueError: print("Enter a number.")

class WizardAgent_1(HumanAgent): pass
class WizardAgent_2(RandomAgent): pass
class WizardAgent_3(RandomAgent): pass
class WizardAgent_4(RandomAgent): pass
class WizardAgent_5(RandomAgent): pass
class WizardAgent_6(RandomAgent): pass
"""
        
        game_code = GAME_CODE_TEMPLATE.format(
            num_players=NUM_PLAYERS,
            num_rounds=NUM_ROUNDS,
            num_games=1,
            debug_mode=False,
            human_mode=True,
            extra_imports="",
            card_class=CARD_CLASS,
            agent_code=agent_code,
            game_class=GAME_CLASS,
            move_timeout=99999
        )
        run_match_human(game_code)
        return

    if not args.agent:
        print("ERROR: Need agent specifications.")
        print("Example: --agent mistral:1:2 gpt-mini:1:2 gemma:1:2")
        sys.exit(1)

    # Group agent runs by model folder
    runs_by_model = {} # folder -> list of runs
    
    for spec in args.agent:
        model_pattern, runs = parse_agent_spec(spec)
        folder = find_model_folder(model_pattern)
        if not folder:
            sys.exit(1)
            
        if not runs:
            runs = get_available_runs(folder, GAME_NAME)
            
        if folder not in runs_by_model:
            runs_by_model[folder] = []
        runs_by_model[folder].extend(runs)

    folders = list(runs_by_model.keys())
    num_models = len(folders)
    
    if num_models == 0:
        print("ERROR: No valid models found.")
        sys.exit(1)

    # Calculate slots per model for a 6-player game
    # Distribute 6 slots as evenly as possible
    base_slots = 6 // num_models
    remainder = 6 % num_models
    slots_per_model = {folder: base_slots for folder in folders}
    for i in range(remainder):
        slots_per_model[folders[i]] += 1

    # How many games can we run?
    # Based on the limiting model's available runs
    num_games = 1000000 # Large initial value
    for folder in folders:
        possible = len(runs_by_model[folder]) // slots_per_model[folder]
        num_games = min(num_games, possible)
    
    if num_games == 0:
        print(f"ERROR: Not enough runs to fill slots for {num_models} models.")
        for folder in folders:
            print(f"  {folder}: slots required={slots_per_model[folder]}, available={len(runs_by_model[folder])}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("WIZARD MATCH - STORED AGENTS")
    print("=" * 60)
    print(f"Total Models: {num_models}")
    for folder in folders:
        print(f"  {folder}: {len(runs_by_model[folder])} runs, {slots_per_model[folder]} slots/game")
    print(f"Total Games: {num_games}")
    print("=" * 60)

    WIZARD_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GAME_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_f = GAME_LOGS_DIR / f"{ts}_match.txt"

    print(f"\nRunning {num_games} games in parallel...")
    game_tasks = []
    
    for i in range(num_games):
        game_agents = []
        for folder in folders:
            num_slots = slots_per_model[folder]
            # Take consecutive runs for this game
            for j in range(num_slots):
                run_idx = i * num_slots + j
                game_agents.append((folder, runs_by_model[folder][run_idx]))
        
        # Ensure we have exactly 6 agents
        if len(game_agents) != 6:
            logger.error("Game %d has %d agents instead of 6", i + 1, len(game_agents))
            continue
            
        game_tasks.append(run_game_async(i + 1, game_agents, log_f, args.debug))

    results = await asyncio.gather(*game_tasks)
    
    total_stats = {} # model_folder -> total_score
    
    # Sort results for display
    results.sort(key=lambda x: x["game_id"])

    for res in results:
        game_id = res["game_id"]
        game_agents = res["game_agents"]
        print(f"\nGame {game_id}:")
        
        if res["success"]:
            scores = res["scores"]
            for idx, (folder, run) in enumerate(game_agents, 1):
                p_key = f"P{idx}"
                score = scores.get(p_key, 0)
                total_stats[folder] = total_stats.get(folder, 0) + score
                print(f"  Slot {idx}: {folder} (run {run}) -> {score}")
        else:
            print(f"  FAILED: {res.get('error', 'Unknown error')}")

    print("\nFINAL RESULTS (Aggregated Scores):")
    sorted_ranks = sorted(total_stats.items(), key=lambda x: x[1], reverse=True)
    for rank, (folder, score) in enumerate(sorted_ranks, 1):
        print(f"  {rank}. {folder}: {score}")
    print(f"\nLogs saved to: {log_f}")


if __name__ == "__main__":
    asyncio.run(main_async())
