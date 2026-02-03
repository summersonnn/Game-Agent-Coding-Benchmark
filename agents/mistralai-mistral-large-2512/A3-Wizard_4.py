"""
Agent Code: A3-Wizard
Model: mistralai/mistral-large-2512
Run: 4
Generated: 2026-02-03 19:30:37
"""

from collections import defaultdict

import random
from collections import defaultdict

class WizardAgent:
    def __init__(self, name):
        self.name = name
        self.card_stats = {
            'wizards': 0,
            'jesters': 0,
            'trump_cards': 0,
            'high_trump': 0,
            'aces': 0,
            'void_suits': set(),
            'suit_counts': defaultdict(int)
        }
        self.played_cards = []
        self.player_bids = [None] * 6
        self.player_tricks = [0] * 6
        self.round_history = []

    def analyze_hand(self, hand, trump_suit):
        """Analyze hand strength for bidding purposes"""
        stats = {
            'wizards': 0,
            'jesters': 0,
            'trump_cards': 0,
            'high_trump': 0,
            'aces': 0,
            'void_suits': set(),
            'suit_counts': defaultdict(int)
        }

        suits_present = set()
        for card in hand:
            if card.card_type == "wizard":
                stats['wizards'] += 1
            elif card.card_type == "jester":
                stats['jesters'] += 1
            else:
                suits_present.add(card.suit)
                stats['suit_counts'][card.suit] += 1
                if card.suit == trump_suit:
                    stats['trump_cards'] += 1
                    if card.rank >= 12:  # Q, K, A
                        stats['high_trump'] += 1
                elif card.rank == 14:  # Ace
                    stats['aces'] += 1

        # Determine void suits
        all_suits = {"Hearts", "Diamonds", "Clubs", "Spades"}
        stats['void_suits'] = all_suits - suits_present

        return stats

    def calculate_bid(self, game_state):
        """Calculate bid based on hand analysis and game state"""
        hand = game_state["my_hand"]
        trump_suit = game_state["trump_suit"]
        cards_this_round = game_state["cards_this_round"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]

        stats = self.analyze_hand(hand, trump_suit)
        self.card_stats = stats

        # Base bid calculation
        bid = 0

        # Guaranteed tricks from wizards
        bid += stats['wizards']

        # High trump cards are likely winners
        bid += min(stats['high_trump'], 2)  # Don't overcount

        # Aces in non-trump suits are likely winners if we can lead them
        bid += min(stats['aces'], 2)

        # Consider void suits - can trump in
        if trump_suit and stats['void_suits']:
            bid += min(len(stats['void_suits']), 1)

        # Adjust for round number (early rounds are more predictable)
        if game_state["round_number"] <= 3:
            bid = min(bid, cards_this_round)
        else:
            # Later rounds - be more conservative
            bid = min(bid, max(0, cards_this_round - 2))

        # Adjust for position (last bidder has hook rule)
        if my_position == 5:  # Last bidder
            total_bids = sum(b for b in bids if b is not None)
            remaining_tricks = cards_this_round - total_bids
            if bid == remaining_tricks:
                # Must adjust bid to avoid hook rule
                if bid > 0:
                    bid -= 1
                else:
                    bid += 1

        # Ensure bid is within valid range
        bid = max(0, min(bid, cards_this_round))

        # Special case: if we have no wizards and weak hand, consider bidding 0
        if stats['wizards'] == 0 and bid <= 1 and random.random() < 0.3:
            bid = 0

        return bid

    def make_bid(self, game_state):
        """Make a strategic bid"""
        bid = self.calculate_bid(game_state)

        # Store bid information
        self.player_bids = game_state["bids"].copy()
        self.player_bids[game_state["my_position"]] = bid

        return bid

    def get_legal_plays(self, game_state):
        """Determine all legal plays for current trick"""
        hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        trump_suit = game_state["trump_suit"]

        if not current_trick:  # We're leading
            return hand.copy()

        led_card = current_trick[0][1]
        led_suit = None

        # Determine the suit that must be followed
        if led_card.card_type == "wizard":
            return hand.copy()  # Can play anything
        elif led_card.card_type == "jester":
            # Find first standard card to determine suit
            for _, card in current_trick:
                if card.card_type == "standard":
                    led_suit = card.suit
                    break
            if led_suit is None:
                return hand.copy()  # All jesters so far
        else:
            led_suit = led_card.suit

        # If we have cards in led suit, must play one (or wizard/jester)
        if led_suit:
            has_led_suit = any(
                card.card_type == "standard" and card.suit == led_suit
                for card in hand
            )
            if has_led_suit:
                return [
                    card for card in hand
                    if (card.card_type in ["wizard", "jester"] or
                        (card.card_type == "standard" and card.suit == led_suit))
                ]

        # Can play anything
        return hand.copy()

    def evaluate_card_strength(self, card, trump_suit, played_cards):
        """Evaluate the strength of a card in the current game context"""
        if card.card_type == "wizard":
            return 100  # Always strongest
        elif card.card_type == "jester":
            return 0  # Always weakest

        # Standard card evaluation
        strength = card.rank

        # Trump cards are stronger
        if card.suit == trump_suit:
            strength += 20

        # Adjust for cards already played
        if card.suit == trump_suit:
            higher_trump_played = sum(
                1 for c in played_cards
                if c.card_type == "standard" and c.suit == trump_suit and c.rank > card.rank
            )
            strength -= higher_trump_played * 5

        return strength

    def should_win_trick(self, game_state):
        """Determine if we should try to win the current trick"""
        my_position = game_state["my_position"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        cards_this_round = game_state["cards_this_round"]
        current_trick = game_state["current_trick"]

        my_bid = bids[my_position]
        my_tricks = tricks_won[my_position]
        remaining_tricks = cards_this_round - len(current_trick)

        # If we've already made our bid, try to avoid winning more
        if my_tricks >= my_bid:
            return False

        # If we're close to our bid and can afford to win
        if my_tricks + 1 == my_bid and remaining_tricks > 1:
            return True

        # If we're far from our bid, try to win
        if my_tricks < my_bid:
            return True

        # Default to trying to win if we're not over our bid
        return my_tricks < my_bid

    def make_play(self, game_state):
        """Make a strategic card play"""
        hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        trump_suit = game_state["trump_suit"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]

        legal_plays = self.get_legal_plays(game_state)
        if not legal_plays:
            return hand[0] if hand else None

        # Update played cards history
        self.played_cards.extend([card for _, card in current_trick])

        # Determine if we should try to win this trick
        want_to_win = self.should_win_trick(game_state)

        # Evaluate each legal play
        card_scores = []
        for card in legal_plays:
            strength = self.evaluate_card_strength(card, trump_suit, self.played_cards)

            # Adjust score based on whether we want to win
            if want_to_win:
                score = strength
            else:
                score = -strength

            # Prefer to play jesters when we don't want to win
            if card.card_type == "jester" and not want_to_win:
                score += 50

            # Prefer to save wizards for later if we don't need to win
            if card.card_type == "wizard" and not want_to_win and len(legal_plays) > 1:
                score -= 30

            card_scores.append((score, card))

        # Sort by score (descending for want_to_win, ascending otherwise)
        card_scores.sort(key=lambda x: x[0], reverse=want_to_win)
        best_card = card_scores[0][1]

        return best_card

    def make_move(self, phase, game_state):
        if phase == "bid":
            return self.make_bid(game_state)
        elif phase == "play":
            return self.make_play(game_state)
