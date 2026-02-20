"""
Wizard Match Runner: Orchestrates 6-player Wizard card game matches between AI agents.

Three-layer architecture (matching A8 pattern): GAME_ENGINE_CODE defines Card +
WizardGame classes, MATCH_RUNNER_CODE runs games inside a subprocess with timeout
and stats tracking, and the outer layer handles CLI, agent loading, subprocess
orchestration, logging, and scoreboard updates.
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

sys.path.append(str(Path(__file__).parent.parent / "utils"))

from model_api import ModelAPI
from logging_config import setup_logging
from scoreboard import update_scoreboard_6p

logger = setup_logging(__name__)

load_dotenv()

# Configuration
NUM_PLAYERS = 6
NUM_ROUNDS = 10

try:
    NUM_GAMES_PER_MATCH = int(int(os.getenv("NUM_OF_GAMES_IN_A_MATCH", "100")) / 10)
except (ValueError, TypeError):
    NUM_GAMES_PER_MATCH = 10

try:
    MOVE_TIME_LIMIT = float(os.getenv("MOVE_TIME_LIMIT", "1.0"))
except (ValueError, TypeError):
    MOVE_TIME_LIMIT = 1.0

try:
    MATCH_TIME_LIMIT = int(os.getenv("MATCH_TIME_LIMIT", "900"))
except (ValueError, TypeError):
    MATCH_TIME_LIMIT = 900

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results" / "wizard"
SCOREBOARD_PATH = BASE_DIR / "scoreboard" / "A3-scoreboard.txt"
AGENTS_DIR = BASE_DIR / "agents"
GAME_NAME = "A3-Wizard"


# ============================================================
# Shared game engine code (Card + WizardGame classes)
# ============================================================
GAME_ENGINE_CODE = r'''
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
        for _ in range(4):
            deck.append(Card("wizard"))
        for _ in range(4):
            deck.append(Card("jester"))
        for suit in self.SUITS:
            for rank in range(2, 15):
                deck.append(Card("standard", suit, rank))
        return deck

    def start_round(self, round_num):
        """Start a new round by dealing cards and determining trump."""
        self.round_number = round_num
        self.cards_this_round = round_num
        self.bids = [None] * self.num_players
        self.tricks_won = [0] * self.num_players

        random.shuffle(self.deck)
        self.hands = [[] for _ in range(self.num_players)]

        card_idx = 0
        for i in range(self.num_players):
            for _ in range(self.cards_this_round):
                self.hands[i].append(self.deck[card_idx])
                card_idx += 1

        total_dealt = self.num_players * self.cards_this_round
        if total_dealt < len(self.deck):
            trump_card = self.deck[total_dealt]
            if trump_card.card_type == "wizard":
                self.trump_suit = random.choice(self.SUITS)
            elif trump_card.card_type == "jester":
                self.trump_suit = None
            else:
                self.trump_suit = trump_card.suit
        else:
            self.trump_suit = None

        self.current_player = 0

    def record_bid(self, player_idx, bid):
        self.bids[player_idx] = bid

    def start_trick(self):
        self.current_trick = []

    def get_game_state(self, player_idx, phase):
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
        for _, card in self.current_trick:
            if card.card_type == "standard":
                return card.suit
        return None

    def _get_valid_cards(self, player_idx):
        hand = self.hands[player_idx]
        led_suit = self._get_led_suit()
        if led_suit is None:
            return hand[:]
        cards_in_suit = [c for c in hand if c.card_type == "standard" and c.suit == led_suit]
        wizards_and_jesters = [c for c in hand if c.card_type in ["wizard", "jester"]]
        if cards_in_suit:
            return cards_in_suit + wizards_and_jesters
        else:
            return hand[:]

    def validate_and_play(self, player_idx, card):
        hand = self.hands[player_idx]
        valid_cards = self._get_valid_cards(player_idx)
        if card not in hand:
            card = random.choice(valid_cards) if valid_cards else random.choice(hand)
        elif card not in valid_cards:
            card = random.choice(valid_cards)
        self.hands[player_idx].remove(card)
        self.current_trick.append((player_idx, card))
        self.current_player = (self.current_player + 1) % self.num_players
        return card

    def finish_trick(self):
        winner = self._determine_trick_winner()
        self.tricks_won[winner] += 1
        self.current_player = winner
        self.trick_leader = winner
        return winner

    def _determine_trick_winner(self):
        for player_idx, card in self.current_trick:
            if card.card_type == "wizard":
                return player_idx
        if all(card.card_type == "jester" for _, card in self.current_trick):
            return self.current_trick[0][0]
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
            if self._card_beats(card, best_card, led_suit):
                best_player = player_idx
                best_card = card
        return best_player

    def _card_beats(self, card1, card2, led_suit):
        if card1.card_type == "jester":
            return False
        if card2.card_type == "jester":
            return True
        card1_is_trump = (card1.suit == self.trump_suit)
        card2_is_trump = (card2.suit == self.trump_suit)
        if card1_is_trump and not card2_is_trump:
            return True
        if card2_is_trump and not card1_is_trump:
            return False
        if card1.suit == card2.suit:
            return card1.rank > card2.rank
        if card1.suit == led_suit:
            return True
        if card2.suit == led_suit:
            return False
        return card1.rank > card2.rank

    def score_round(self):
        for i in range(self.num_players):
            bid = self.bids[i]
            won = self.tricks_won[i]
            if bid == won:
                score = 20 + (10 * won)
            else:
                score = -10 * abs(bid - won)
            self.total_scores[i] += score
'''


# ============================================================
# Match runner code (play_game + main for agent-vs-agent)
# ============================================================
MATCH_RUNNER_CODE = r'''
class MoveTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise MoveTimeoutException("Move timeout")


class RandomFallbackAgent:
    """Replaces agents that crash during initialization."""
    def __init__(self, name):
        self.name = name

    def make_move(self, phase, game_state):
        if phase == "bid":
            return random.randint(0, game_state["cards_this_round"])
        else:
            return random.choice(game_state["my_hand"])


def call_agent_with_timeout(agent, phase, game_state, agent_label, match_stats):
    """Call agent's make_move with timeout protection."""
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(max(1, int(MOVE_TIMEOUT)))
        try:
            return agent.make_move(phase, game_state)
        finally:
            signal.alarm(0)
    except MoveTimeoutException:
        match_stats[agent_label]["timeout"] += 1
        return None
    except Exception:
        match_stats[agent_label]["make_move_crash"] += 1
        return None


def play_game(game_num, match_stats):
    """Play one complete 6-player Wizard game and update match_stats."""
    game = WizardGame(NUM_PLAYERS)

    # Rotate seating for fairness: offset by (game_num - 1) % 6
    offset = (game_num - 1) % NUM_PLAYERS
    seat_order = [(i + offset) % NUM_PLAYERS for i in range(NUM_PLAYERS)]
    # seat_order[seat_idx] = original agent index (0-based)

    # Map: seat position -> agent label, agent object
    agents = [None] * NUM_PLAYERS
    agent_labels = [None] * NUM_PLAYERS  # Agent-1 through Agent-6 labels per seat

    for seat_idx in range(NUM_PLAYERS):
        orig_idx = seat_order[seat_idx]
        agent_label = f"Agent-{orig_idx + 1}"
        class_name = f"WizardAgent_{orig_idx + 1}"
        agent_labels[seat_idx] = agent_label
        try:
            agent_class = globals()[class_name]
            agents[seat_idx] = agent_class(agent_label)
        except Exception as e:
            print(f"{agent_label}: init crash - {str(e)[:80]}")
            match_stats[agent_label]["other_crash"] += 1
            agents[seat_idx] = RandomFallbackAgent(agent_label)

    print()
    print("=" * 60)
    print(f"Game {game_num}")
    for seat_idx in range(NUM_PLAYERS):
        orig_idx = seat_order[seat_idx]
        info_var = f"AGENT{orig_idx + 1}_INFO"
        info = globals().get(info_var, f"agent-{orig_idx + 1}")
        print(f"Seat {seat_idx}: {agent_labels[seat_idx]} ({info})")
    print("-" * 60)

    # Play all 10 rounds
    for round_num in range(1, NUM_ROUNDS + 1):
        game.start_round(round_num)
        print(f"Round {round_num} ({round_num} cards) - Trump: {game.trump_suit if game.trump_suit else 'None'}")

        # Bidding phase
        for seat_idx in range(NUM_PLAYERS):
            agent = agents[seat_idx]
            label = agent_labels[seat_idx]
            game_state = game.get_game_state(seat_idx, "bid")
            bid = call_agent_with_timeout(agent, "bid", game_state, label, match_stats)

            if not isinstance(bid, int) or bid < 0 or bid > game.cards_this_round:
                match_stats[label]["invalid"] += 1
                bid = random.randint(0, game.cards_this_round)

            # Hook rule: last bidder cannot make total bids equal total tricks
            if seat_idx == NUM_PLAYERS - 1:
                current_sum = sum(b for b in game.bids if b is not None)
                forbidden_bid = game.cards_this_round - current_sum
                if 0 <= forbidden_bid <= game.cards_this_round and bid == forbidden_bid:
                    match_stats[label]["invalid"] += 1
                    valid_bids = [b for b in range(0, game.cards_this_round + 1) if b != forbidden_bid]
                    bid = random.choice(valid_bids) if valid_bids else 0

            game.record_bid(seat_idx, bid)

        print(f"Bids: {game.bids}")

        # Playing phase
        for trick_num in range(game.cards_this_round):
            game.start_trick()
            for _ in range(NUM_PLAYERS):
                current_player = game.current_player
                agent = agents[current_player]
                label = agent_labels[current_player]
                game_state = game.get_game_state(current_player, "play")

                card = call_agent_with_timeout(agent, "play", game_state, label, match_stats)

                valid_card = game.validate_and_play(current_player, card)
                if valid_card != card:
                    match_stats[label]["invalid"] += 1

            winner = game.finish_trick()

        game.score_round()
        print(f"Tricks won: {game.tricks_won}")
        round_scores = [game.total_scores[i] for i in range(NUM_PLAYERS)]
        print(f"Running scores: {round_scores}")

    # Game complete - rank by game score
    game_scores = list(game.total_scores)
    print(f"Game {game_num} final scores: {game_scores}")

    # Build (seat_idx, score) pairs and sort descending
    indexed = [(seat_idx, game_scores[seat_idx]) for seat_idx in range(NUM_PLAYERS)]
    indexed.sort(key=lambda x: x[1], reverse=True)

    # Assign rank-based points with tie handling
    # Points: 1st=5, 2nd=4, 3rd=3, 4th=2, 5th=1, 6th=0
    rank_points = [5, 4, 3, 2, 1, 0]
    placement_labels = ["1st", "2nd", "3rd", "4th", "5th", "6th"]

    # Group by score to handle ties
    i = 0
    while i < NUM_PLAYERS:
        j = i
        while j < NUM_PLAYERS and indexed[j][1] == indexed[i][1]:
            j += 1
        # Positions i through j-1 are tied
        tied_points = sum(rank_points[k] for k in range(i, j)) / (j - i)
        for k in range(i, j):
            seat_idx = indexed[k][0]
            label = agent_labels[seat_idx]
            match_stats[label]["points"] += tied_points
            match_stats[label]["score"] += game_scores[seat_idx]
            # For placement tracking, share the best position label
            # Each tied agent gets credited at the highest tied position
            for pos in range(i, j):
                placement_key = placement_labels[pos]
                # Distribute evenly: each tied agent gets 1/(j-i) of each tied position
                match_stats[label][placement_key] += 1.0 / (j - i)
        i = j

    # Print per-game result block
    print("-" * 40)
    print("Rankings:")
    for rank_idx, (seat_idx, score) in enumerate(indexed):
        label = agent_labels[seat_idx]
        pts = rank_points[rank_idx] if rank_idx < NUM_PLAYERS else 0
        # Approximate — ties handled above, this is just display
        print(f"  {rank_idx + 1}. {label}: score={score}")
    print("=" * 60)

    sys.stdout.flush()


def main():
    match_stats = {
        f"Agent-{i}": {
            "1st": 0.0, "2nd": 0.0, "3rd": 0.0,
            "4th": 0.0, "5th": 0.0, "6th": 0.0,
            "points": 0.0, "score": 0.0,
            "make_move_crash": 0, "other_crash": 0, "crash": 0,
            "timeout": 0, "invalid": 0,
        }
        for i in range(1, NUM_PLAYERS + 1)
    }

    for i in range(NUM_GAMES):
        play_game(i + 1, match_stats)
        sys.stdout.flush()

    # Aggregate crash stats
    for key in match_stats:
        match_stats[key]["crash"] = match_stats[key]["make_move_crash"] + match_stats[key]["other_crash"]

    # Print structured output for outer layer parsing
    print("=" * 60)
    for i in range(1, NUM_PLAYERS + 1):
        info_var = f"AGENT{i}_INFO"
        print(f"Agent-{i}: {globals().get(info_var, f'agent-{i}')}")

    result_parts = [f"Agent-{i}={match_stats[f'Agent-{i}']['points']:.1f}" for i in range(1, NUM_PLAYERS + 1)]
    print(f"RESULT:{','.join(result_parts)}")

    score_parts = [f"Agent-{i}={match_stats[f'Agent-{i}']['score']:.1f}" for i in range(1, NUM_PLAYERS + 1)]
    print(f"SCORE:{','.join(score_parts)}")

    stats_parts = [f"Agent-{i}={match_stats[f'Agent-{i}']}" for i in range(1, NUM_PLAYERS + 1)]
    print(f"STATS:{','.join(stats_parts)}")

    print("--- MATCH STATISTICS ---")
    # Sort agents by points (descending), then score (descending)
    sorted_agents = sorted(
        match_stats.keys(),
        key=lambda k: (match_stats[k]["points"], match_stats[k]["score"]),
        reverse=True
    )
    for agent_id in sorted_agents:
        s = match_stats[agent_id]
        print(f"{agent_id} make_move_crash: {s['make_move_crash']}")
        print(f"{agent_id} other_crash: {s['other_crash']}")
        print(f"{agent_id} crash (total): {s['crash']}")
        print(f"{agent_id} Timeouts: {s['timeout']}")
        print(f"{agent_id} Invalid: {s['invalid']}")
        print(f"{agent_id} Points: {s['points']:.1f}")
        print(f"{agent_id} Score: {s['score']:.1f}")
        print(f"{agent_id} Placements: 1st={s['1st']:.1f} 2nd={s['2nd']:.1f} 3rd={s['3rd']:.1f} 4th={s['4th']:.1f} 5th={s['5th']:.1f} 6th={s['6th']:.1f}")


if __name__ == "__main__":
    main()
'''


# ============================================================
# Human play mode code
# ============================================================
HUMAN_PLAY_CODE = r'''
class HumanAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, phase, game_state):
        print(f"\n--- {self.name}'s TURN ({phase}) ---")
        if phase == "bid":
            print(f"Round: {game_state['round_number']} ({game_state['cards_this_round']} cards)")
            print(f"Trump: {game_state['trump_suit']}")
            print(f"Hand: {[str(c) for c in game_state['my_hand']]}")
            print(f"Bids so far: {game_state['bids']}")
            while True:
                try:
                    bid = int(input(f"Enter Bid [0-{game_state['cards_this_round']}]: ").strip())
                    if 0 <= bid <= game_state['cards_this_round']:
                        return bid
                    print("Invalid bid range.")
                except ValueError:
                    print("Enter a number.")
        else:
            print(f"Trump: {game_state['trump_suit']}")
            print(f"Trick so far: {[(i+1, str(c)) for i, c in game_state['current_trick']]}")
            print(f"Hand: {[(i, str(c)) for i, c in enumerate(game_state['my_hand'])]}")
            print(f"Bids: {game_state['bids']} | Tricks won: {game_state['tricks_won']}")
            while True:
                try:
                    idx = int(input(f"Select Card Index [0-{len(game_state['my_hand'])-1}]: ").strip())
                    if 0 <= idx < len(game_state['my_hand']):
                        return game_state['my_hand'][idx]
                    print("Invalid index.")
                except ValueError:
                    print("Enter a number.")


class RandomBotAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, phase, game_state):
        if phase == "bid":
            return random.randint(0, game_state['cards_this_round'])
        else:
            return random.choice(game_state['my_hand'])


MODE_TITLES = {
    "humanvsbot": "Human vs Random Bots",
    "humanvshuman": "Human vs Human (Hotseat)",
    "humanvsagent": "Human vs Stored Agent",
}


if __name__ == "__main__":
    mode_title = MODE_TITLES.get(GAME_MODE, GAME_MODE)
    print("=" * 60)
    print(f"WIZARD - {mode_title}")
    print("=" * 60)

    agents = []
    if GAME_MODE == "humanvsbot":
        agents.append(HumanAgent("Human"))
        for i in range(2, NUM_PLAYERS + 1):
            agents.append(RandomBotAgent(f"Bot-{i}"))
        print("You are Agent-1 (Human). Playing against 5 random bots.")
    elif GAME_MODE == "humanvshuman":
        for i in range(1, NUM_PLAYERS + 1):
            agents.append(HumanAgent(f"Player-{i}"))
        print("All 6 seats are human players (hotseat mode).")
    elif GAME_MODE == "humanvsagent":
        agents.append(HumanAgent("Human"))
        try:
            stored_agent = WizardAgent_1(f"StoredAgent")
            agents.append(stored_agent)
        except Exception as e:
            print(f"Failed to load stored agent: {e}")
            agents.append(RandomBotAgent("FallbackBot-2"))
        for i in range(3, NUM_PLAYERS + 1):
            agents.append(RandomBotAgent(f"Bot-{i}"))
        print("You are Agent-1 (Human). Agent-2 is stored agent. Rest are bots.")

    game = WizardGame(NUM_PLAYERS)
    NUM_ROUNDS_LOCAL = 10

    total_scores_display = [0] * NUM_PLAYERS
    for round_num in range(1, NUM_ROUNDS_LOCAL + 1):
        game.start_round(round_num)
        print(f"\n{'='*60}")
        print(f"Round {round_num} ({round_num} cards) - Trump: {game.trump_suit if game.trump_suit else 'None'}")
        print(f"{'='*60}")

        # Show hand to human(s)
        for i, agent in enumerate(agents):
            if isinstance(agent, HumanAgent):
                print(f"\n{agent.name}'s hand: {[str(c) for c in game.hands[i]]}")

        # Bidding
        for i, agent in enumerate(agents):
            game_state = game.get_game_state(i, "bid")
            bid = agent.make_move("bid", game_state)
            if not isinstance(bid, int) or bid < 0 or bid > game.cards_this_round:
                bid = random.randint(0, game.cards_this_round)
            # Hook rule for last bidder
            if i == NUM_PLAYERS - 1:
                current_sum = sum(b for b in game.bids if b is not None)
                forbidden = game.cards_this_round - current_sum
                if 0 <= forbidden <= game.cards_this_round and bid == forbidden:
                    valid = [b for b in range(0, game.cards_this_round + 1) if b != forbidden]
                    bid = random.choice(valid) if valid else 0
                    print(f"(Hook rule applied, bid changed to {bid})")
            game.record_bid(i, bid)
            print(f"{agent.name} bids: {bid}")

        print(f"All bids: {game.bids}")

        # Playing tricks
        for trick_num in range(game.cards_this_round):
            game.start_trick()
            print(f"\n  Trick {trick_num + 1}/{game.cards_this_round}:")
            for _ in range(NUM_PLAYERS):
                cp = game.current_player
                agent = agents[cp]
                game_state = game.get_game_state(cp, "play")
                card = agent.make_move("play", game_state)
                played = game.validate_and_play(cp, card)
                print(f"    {agent.name} plays: {played}")
            winner = game.finish_trick()
            print(f"  -> {agents[winner].name} wins trick!")

        game.score_round()
        print(f"\nRound {round_num} complete.")
        print(f"Tricks won: {game.tricks_won}")
        print(f"Scores: {game.total_scores}")

    print(f"\n{'='*60}")
    print("FINAL SCORES")
    print(f"{'='*60}")
    indexed = [(i, game.total_scores[i]) for i in range(NUM_PLAYERS)]
    indexed.sort(key=lambda x: x[1], reverse=True)
    for rank, (idx, score) in enumerate(indexed, 1):
        print(f"  {rank}. {agents[idx].name}: {score}")
    print("\nThanks for playing!")
'''


# ============================================================
# Outer layer functions
# ============================================================


def find_model_folder(pattern: str) -> str | None:
    """Find agent model folder by exact match or substring fallback."""
    if not AGENTS_DIR.exists():
        logger.error("Agents directory not found: %s", AGENTS_DIR)
        return None

    exact = AGENTS_DIR / pattern
    if exact.is_dir():
        return pattern

    matches = [
        d.name for d in AGENTS_DIR.iterdir()
        if d.is_dir() and pattern.lower() in d.name.lower()
    ]

    if not matches:
        logger.error("No model folder matches pattern '%s'", pattern)
        return None

    if len(matches) > 1:
        return ModelAPI.resolve_model_interactive(pattern, matches, context="folder")

    return matches[0]


def get_available_runs(model_folder: str, game: str) -> list[int]:
    """Get sorted list of available run IDs for a model and game."""
    model_dir = AGENTS_DIR / model_folder
    runs = []
    pattern = re.compile(rf"^{re.escape(game)}_(\d+)\.py$")

    for file in model_dir.glob(f"{game}_*.py"):
        match = pattern.match(file.name)
        if match:
            runs.append(int(match.group(1)))

    return sorted(runs)


def load_stored_agent(
    model_folder: str, game: str, run: int, agent_idx: int
) -> tuple[str, str]:
    """Load agent code from stored file, rename class to WizardAgent_{agent_idx}.

    Returns (renamed_code, imports). Empty strings on failure.
    """
    agent_file = AGENTS_DIR / model_folder / f"{game}_{run}.py"

    if not agent_file.exists():
        logger.error("Agent file not found: %s", agent_file)
        return "", ""

    content = agent_file.read_text()
    lines = content.split("\n")

    # Skip header docstring
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

    imports = []
    class_start_idx = None

    for i, line in enumerate(code_lines):
        stripped = line.strip()
        if stripped.startswith("class WizardAgent"):
            class_start_idx = i
            break
        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:
                imports.append(stripped)

    if class_start_idx is None:
        logger.error("No WizardAgent class found in %s", agent_file)
        return "", ""

    # Extract class body via indentation detection
    class_lines = []
    base_indent = 0

    for i in range(class_start_idx, len(code_lines)):
        line = code_lines[i]
        stripped = line.strip()

        if i == class_start_idx:
            class_lines.append(line)
            base_indent = len(line) - len(line.lstrip())
            continue

        if not stripped or stripped.startswith("#"):
            class_lines.append(line)
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent <= base_indent:
            break

        class_lines.append(line)

    agent_code = "\n".join(class_lines)

    agent_code = re.sub(
        r"\bWizardAgent\b", f"WizardAgent_{agent_idx}", agent_code
    )

    return agent_code.strip(), "\n".join(imports)


def parse_agent_spec(spec: str) -> tuple[str, int]:
    """Parse 'model:run' spec into (model_pattern, run_number)."""
    parts = spec.split(":")
    if len(parts) != 2:
        logger.error("Invalid agent spec '%s'. Expected model:run", spec)
        return "", 0
    try:
        return parts[0], int(parts[1])
    except ValueError:
        logger.error("Invalid run number in spec '%s'", spec)
        return parts[0], 0


def build_game_code(
    agent_codes: list[str],
    extra_imports: str,
    num_games: int,
    move_timeout: float,
    agent_infos: list[str],
) -> str:
    """Assemble the full subprocess script from components."""
    header = (
        "import sys\n"
        "import random\n"
        "import signal\n"
        "\n"
        f"MOVE_TIMEOUT = {move_timeout}\n"
        f"NUM_GAMES = {num_games}\n"
        f"NUM_PLAYERS = {NUM_PLAYERS}\n"
        f"NUM_ROUNDS = {NUM_ROUNDS}\n"
    )

    for i, info in enumerate(agent_infos, 1):
        header += f'AGENT{i}_INFO = "{info}"\n'

    parts = [header, extra_imports]
    parts.extend(agent_codes)
    parts.append(GAME_ENGINE_CODE)
    parts.append(MATCH_RUNNER_CODE)

    return "\n\n".join(parts)


def build_human_game_code(
    mode: str, agent_code: str = "", agent_imports: str = ""
) -> str:
    """Build subprocess script for human play modes."""
    header = (
        "import random\n"
        f'GAME_MODE = "{mode}"\n'
        f"NUM_PLAYERS = {NUM_PLAYERS}\n"
    )
    parts = [header]
    if mode == "humanvsagent" and agent_imports:
        parts.append(agent_imports)
    if mode == "humanvsagent" and agent_code:
        parts.append(agent_code)
    parts.append(GAME_ENGINE_CODE)
    parts.append(HUMAN_PLAY_CODE)
    return "\n\n".join(parts)


def run_match(
    game_code: str, match_id: int, run_ids: list[int], timeout: int = MATCH_TIME_LIMIT
) -> dict:
    """Write temp file, execute subprocess, parse structured output."""
    temp_id = uuid.uuid4().hex[:8]
    temp_file = os.path.join(
        tempfile.gettempdir(), f"wizard_match_{match_id}_{temp_id}.py"
    )

    try:
        with open(temp_file, "w") as f:
            f.write(game_code)

        result = subprocess.run(
            ["python", temp_file], capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            return {
                "match_id": match_id,
                "success": False,
                "error": result.stderr[:500],
                "log": result.stdout,
            }

        stdout = result.stdout

        # Parse RESULT line: Agent-1=<pts>,...,Agent-6=<pts>
        result_match = re.search(
            r"RESULT:((?:Agent-\d+=[\d.]+,?)+)", stdout
        )

        # Parse SCORE line
        score_match = re.search(
            r"SCORE:((?:Agent-\d+=-?[\d.]+,?)+)", stdout
        )

        # Parse STATS lines
        stats_block = ""
        if "--- MATCH STATISTICS ---" in stdout:
            stats_block = stdout.split("--- MATCH STATISTICS ---")[1].strip()

        if result_match:
            agent_points = {}
            for part in result_match.group(1).split(","):
                if "=" in part:
                    name, val = part.split("=")
                    agent_points[name.strip()] = float(val.strip())

            agent_scores = {}
            if score_match:
                for part in score_match.group(1).split(","):
                    if "=" in part:
                        name, val = part.split("=")
                        agent_scores[name.strip()] = float(val.strip())

            # Parse per-agent placement counts from stats block
            agent_placements = {}
            for i in range(1, NUM_PLAYERS + 1):
                key = f"Agent-{i}"
                placements = {}
                for p in ["1st", "2nd", "3rd", "4th", "5th", "6th"]:
                    pm = re.search(rf"Agent-{i} Placements:.*?{p}=([\d.]+)", stats_block)
                    placements[p] = float(pm.group(1)) if pm else 0.0
                agent_placements[key] = placements

            return {
                "match_id": match_id,
                "success": True,
                "agent_points": agent_points,
                "agent_scores": agent_scores,
                "agent_placements": agent_placements,
                "stats_block": stats_block,
                "log": stdout,
                "error": None,
            }

        return {
            "match_id": match_id,
            "success": False,
            "error": "Could not parse results:\n" + stdout[:300],
            "log": stdout,
        }

    except Exception as e:
        return {
            "match_id": match_id,
            "success": False,
            "error": str(e),
            "log": "",
        }
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


async def run_match_async(
    game_code: str, match_id: int, run_ids: list[int]
) -> dict:
    """Run match in executor for async compatibility."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_match, game_code, match_id, run_ids)


async def main_async():
    parser = argparse.ArgumentParser(description="Run Wizard matches between AI agents")
    parser.add_argument(
        "--agent", nargs="+",
        help="Agent specs: model1:run1 model2:run2 ... (exactly 6 for match mode)",
    )
    human_group = parser.add_mutually_exclusive_group()
    human_group.add_argument(
        "--humanvsbot", action="store_true",
        help="Play interactively against 5 random bots",
    )
    human_group.add_argument(
        "--humanvshuman", action="store_true",
        help="All 6 seats are human players (hotseat)",
    )
    human_group.add_argument(
        "--humanvsagent", action="store_true",
        help="Play against a stored agent + 4 random bots (requires --agent with 1 spec)",
    )
    parser.add_argument(
        "--update-scoreboard", action="store_true",
        help="Write results to scoreboard (default: off; enabled by matchmaker)",
    )
    args = parser.parse_args()

    # --- Human modes ---
    human_mode = None
    if args.humanvsbot:
        human_mode = "humanvsbot"
    elif args.humanvshuman:
        human_mode = "humanvshuman"
    elif args.humanvsagent:
        human_mode = "humanvsagent"

    if human_mode:
        if human_mode == "humanvsagent":
            if not args.agent or len(args.agent) != 1:
                print("ERROR: --humanvsagent requires exactly 1 --agent spec.")
                print("Example: --humanvsagent --agent mistral:1")
                sys.exit(1)
            model_pattern, run_num = parse_agent_spec(args.agent[0])
            folder = find_model_folder(model_pattern)
            if not folder:
                sys.exit(1)
            if not run_num:
                runs = get_available_runs(folder, GAME_NAME)
                if not runs:
                    print(f"ERROR: No runs found for {folder}/{GAME_NAME}")
                    sys.exit(1)
                run_num = runs[0]
            agent_code, agent_imports = load_stored_agent(
                folder, GAME_NAME, run_num, 1
            )
            if not agent_code:
                print(f"ERROR: Failed to load agent from {folder}")
                sys.exit(1)
            game_code = build_human_game_code(
                "humanvsagent", agent_code, agent_imports
            )
        elif args.agent:
            print("ERROR: --agent is not used with --humanvsbot or --humanvshuman.")
            sys.exit(1)
        else:
            game_code = build_human_game_code(human_mode)

        temp_file = os.path.join(
            tempfile.gettempdir(),
            f"wizard_{human_mode}_{uuid.uuid4().hex[:8]}.py",
        )
        try:
            with open(temp_file, "w") as f:
                f.write(game_code)
            subprocess.run(
                ["python", temp_file],
                stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
            )
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return

    # --- Agent match mode ---
    if not args.agent or len(args.agent) != NUM_PLAYERS:
        print(f"ERROR: Need exactly {NUM_PLAYERS} agent specifications.")
        print("Example: --agent model1:1 model2:1 model3:1 model4:1 model5:1 model6:1")
        sys.exit(1)

    # Parse and resolve all 6 agent specs
    agent_specs = []
    for spec in args.agent:
        model_pattern, run_num = parse_agent_spec(spec)
        if not model_pattern:
            sys.exit(1)
        folder = find_model_folder(model_pattern)
        if not folder:
            sys.exit(1)
        agent_specs.append((folder, run_num))

    print("\n" + "=" * 60)
    print("WIZARD MATCH - STORED AGENTS")
    print("=" * 60)
    for i, (folder, run) in enumerate(agent_specs, 1):
        print(f"  Agent-{i}: {folder}:{run}")
    print(f"  Games per match: {NUM_GAMES_PER_MATCH}")
    print("=" * 60)

    # Load all 6 agents
    agent_codes = []
    all_imports = set()

    for i, (folder, run) in enumerate(agent_specs, 1):
        code, imports = load_stored_agent(folder, GAME_NAME, run, i)
        if not code:
            print(f"ERROR: Failed to load Agent-{i} from {folder}:{run}")
            sys.exit(1)
        agent_codes.append(code)
        if imports:
            for imp in imports.split("\n"):
                if imp.strip():
                    all_imports.add(imp.strip())

    extra_imports = "\n".join(sorted(all_imports))
    agent_infos = [f"{folder}:{run}" for folder, run in agent_specs]

    game_code = build_game_code(
        agent_codes, extra_imports, NUM_GAMES_PER_MATCH,
        MOVE_TIME_LIMIT, agent_infos,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    run_ids = [run for _, run in agent_specs]
    result = run_match(game_code, 1, run_ids)

    # Build log filename
    agent_suffix = "_vs_".join(f"{f}:{r}" for f, r in agent_specs)
    log_f = RESULTS_DIR / f"{ts}_{agent_suffix}_match.txt"

    if result["success"]:
        agent_points = result["agent_points"]
        agent_scores = result["agent_scores"]
        agent_placements = result["agent_placements"]

        # Prepare list of results for sorting
        results_list = []
        for i, (folder, run) in enumerate(agent_specs, 1):
            key = f"Agent-{i}"
            pts = agent_points.get(key, 0)
            sc = agent_scores.get(key, 0)
            results_list.append({
                "key": key,
                "folder": folder,
                "run": run,
                "pts": pts,
                "sc": sc
            })

        # Sort by points (descending), then by score (descending)
        results_list.sort(key=lambda x: (x["pts"], x["sc"]), reverse=True)

        status = "Result:\n"
        for res in results_list:
            status += f"  {res['key']} ({res['folder']}:{res['run']}): Pts={res['pts']:.1f} Score={res['sc']:.1f}\n"

        game_log = result.get("log", "")
        if game_log:
            status += f"\n{game_log}\n"

        print("\nFINAL RESULTS:")
        for res in results_list:
            print(f"  {res['key']} ({res['folder']}:{res['run']}): Pts={res['pts']:.1f} Score={res['sc']:.1f}")
    else:
        status = f"FAILED: {result.get('error', 'Unknown')}"
        print(f"\nMATCH FAILED: {result.get('error', 'Unknown')}")

    with open(log_f, "w") as f:
        f.write("Match Contenders:\n")
        for i, (folder, run) in enumerate(agent_specs, 1):
            f.write(f"Agent-{i}: {folder}:{run}\n")
        f.write(f"\n{status}\n")
        f.write("-" * 60 + "\n")

    # Scoreboard update
    if result["success"] and args.update_scoreboard:
        for i, (folder, run) in enumerate(agent_specs, 1):
            key = f"Agent-{i}"
            agent_key = f"{folder}:{run}"

            placements = {}
            raw_placements = agent_placements.get(key, {})
            for p in ["1st", "2nd", "3rd", "4th", "5th", "6th"]:
                placements[p] = int(round(raw_placements.get(p, 0)))

            update_scoreboard_6p(
                SCOREBOARD_PATH,
                agent_key,
                games_played=NUM_GAMES_PER_MATCH,
                placements=placements,
                points=int(round(agent_points.get(key, 0))),
                score=agent_scores.get(key, 0.0),
            )

    print(f"\nLog saved to: {log_f}")


if __name__ == "__main__":
    asyncio.run(main_async())
