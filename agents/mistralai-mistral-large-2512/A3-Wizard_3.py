"""
Agent Code: A3-Wizard
Model: mistralai/mistral-large-2512
Run: 3
Generated: 2026-02-03 19:30:37
"""

from collections import defaultdict

import random
from collections import defaultdict

class WizardAgent:
    def __init__(self, name):
        self.name = name
        self.card_stats = defaultdict(int)
        self.played_cards = set()
        self.trump_strength = 0
        self.non_trump_strength = defaultdict(int)
        self.void_suits = set()
        self.remaining_wizards = 4
        self.remaining_jesters = 4
        self.round_history = []

    def make_move(self, phase, game_state):
        self._update_game_state(game_state)

        if phase == "bid":
            return self._make_bid(game_state)
        elif phase == "play":
            return self._play_card(game_state)

    def _update_game_state(self, game_state):
        # Track played cards
        for _, card in game_state["current_trick"]:
            if card not in self.played_cards:
                self.played_cards.add(card)
                if card.card_type == "wizard":
                    self.remaining_wizards -= 1
                elif card.card_type == "jester":
                    self.remaining_jesters -= 1

        # Update card statistics
        self._analyze_hand(game_state["my_hand"], game_state["trump_suit"])

    def _analyze_hand(self, hand, trump_suit):
        self.trump_strength = 0
        self.non_trump_strength = defaultdict(int)
        self.void_suits = set(["Hearts", "Diamonds", "Clubs", "Spades"])

        for card in hand:
            if card.card_type == "wizard":
                self.trump_strength += 2  # Wizards are very strong
            elif card.card_type == "jester":
                continue  # Jesters are weak
            else:
                if card.suit == trump_suit:
                    # Trump cards are strong, especially high ones
                    self.trump_strength += 1 + (card.rank / 14)
                else:
                    # Non-trump cards - track strength by suit
                    self.non_trump_strength[card.suit] += 1 + (card.rank / 14)
                    if card.suit in self.void_suits:
                        self.void_suits.remove(card.suit)

    def _make_bid(self, game_state):
        cards_this_round = game_state["cards_this_round"]
        trump_suit = game_state["trump_suit"]
        my_hand = game_state["my_hand"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]

        # Base bid calculation
        base_bid = self._calculate_base_bid(game_state)

        # Adjust for position (last bidder has hook rule)
        if my_position == 5:  # Last bidder (Player-6)
            total_bids = sum(b for b in bids if b is not None)
            remaining_bids = cards_this_round - total_bids

            if remaining_bids == 1:  # Hook rule applies
                # Need to avoid making the total equal to tricks available
                if base_bid == 1:
                    # Choose between 0 or 2
                    return 0 if random.random() < 0.5 else 2
                elif base_bid == 0:
                    return 2
                else:
                    return max(0, base_bid - 1)

        return max(0, min(cards_this_round, base_bid))

    def _calculate_base_bid(self, game_state):
        cards_this_round = game_state["cards_this_round"]
        trump_suit = game_state["trump_suit"]
        my_hand = game_state["my_hand"]

        # Count guaranteed winners (Wizards)
        guaranteed_wins = sum(1 for card in my_hand if card.card_type == "wizard")

        # Count potential winners (high trump cards and Aces in other suits)
        potential_wins = 0
        for card in my_hand:
            if card.card_type == "standard":
                if card.suit == trump_suit:
                    # Trump cards are strong, especially high ones
                    if card.rank >= 12:  # Q, K, A
                        potential_wins += 0.8
                    elif card.rank >= 10:  # 10, J
                        potential_wins += 0.5
                else:
                    # Non-trump Aces are strong
                    if card.rank == 14:  # Ace
                        potential_wins += 0.7

        # Consider void suits (can trump in)
        void_bonus = len(self.void_suits) * 0.3

        # Consider round number (early rounds are more predictable)
        round_factor = game_state["round_number"] / 10

        # Calculate base bid
        base_bid = guaranteed_wins + potential_wins + void_bonus

        # Adjust for round length
        if cards_this_round <= 3:
            # Early rounds - be more conservative
            base_bid *= 0.8
        elif cards_this_round >= 7:
            # Late rounds - be more aggressive
            base_bid *= 1.2

        # Consider other players' bids if available
        bids = game_state["bids"]
        if bids.count(None) == 1:  # Only we haven't bid
            total_bids = sum(b for b in bids if b is not None)
            if total_bids >= cards_this_round * 0.7:  # Others are bidding high
                base_bid *= 0.9  # Be slightly more conservative

        return int(round(base_bid))

    def _play_card(self, game_state):
        my_hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        trump_suit = game_state["trump_suit"]
        trick_leader = game_state["trick_leader"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        my_position = game_state["my_position"]
        cards_this_round = game_state["cards_this_round"]

        # If we're leading the trick
        if not current_trick:
            return self._lead_card(game_state)

        # If following a trick
        led_card = current_trick[0][1]
        led_suit = self._get_led_suit(led_card, current_trick)

        # Determine if we need to win this trick
        need_to_win = self._should_win_trick(game_state)

        # Get legal plays
        legal_plays = self._get_legal_plays(my_hand, led_suit, led_card)

        if need_to_win:
            return self._play_to_win(legal_plays, trump_suit, led_suit)
        else:
            return self._play_to_avoid_winning(legal_plays, trump_suit, led_suit)

    def _get_led_suit(self, led_card, current_trick):
        if led_card.card_type == "wizard":
            return None
        elif led_card.card_type == "jester":
            # Find first standard card to determine suit
            for _, card in current_trick[1:]:
                if card.card_type == "standard":
                    return card.suit
            return None
        else:
            return led_card.suit

    def _should_win_trick(self, game_state):
        my_position = game_state["my_position"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        cards_this_round = game_state["cards_this_round"]
        current_trick = game_state["current_trick"]

        my_bid = bids[my_position]
        my_tricks = tricks_won[my_position]
        tricks_remaining = cards_this_round - len(game_state["current_trick"])

        # If we've already met our bid, try to avoid winning more tricks
        if my_tricks >= my_bid:
            return False

        # If this is the last trick and we need it to make our bid
        if len(current_trick) == 5 and my_tricks == my_bid - 1:
            return True

        # If we're close to our bid and this trick is important
        if my_tricks == my_bid - 1 and tricks_remaining <= 2:
            return True

        # Default: try to win if we still need tricks
        return my_tricks < my_bid

    def _get_legal_plays(self, hand, led_suit, led_card):
        legal_plays = []

        if led_suit is None:  # Wizard led or all Jesters
            return hand.copy()

        # Check if we have cards in the led suit
        has_led_suit = any(
            card.card_type == "standard" and card.suit == led_suit
            for card in hand
        )

        for card in hand:
            if card.card_type in ["wizard", "jester"]:
                legal_plays.append(card)
            elif card.card_type == "standard":
                if card.suit == led_suit:
                    legal_plays.append(card)
                elif not has_led_suit:
                    legal_plays.append(card)

        return legal_plays

    def _play_to_win(self, legal_plays, trump_suit, led_suit):
        # Sort plays by strength (Wizards > high trump > high led suit > others)
        def card_strength(card):
            if card.card_type == "wizard":
                return 4
            elif card.card_type == "jester":
                return 0
            elif card.suit == trump_suit:
                return 3 + (card.rank / 14)
            elif card.suit == led_suit:
                return 2 + (card.rank / 14)
            else:
                return 1 + (card.rank / 14)

        # Play the strongest legal card
        return max(legal_plays, key=card_strength)

    def _play_to_avoid_winning(self, legal_plays, trump_suit, led_suit):
        # Sort plays by weakness (Jesters > low non-trump > low trump > others)
        def card_weakness(card):
            if card.card_type == "jester":
                return 4
            elif card.card_type == "wizard":
                return 0
            elif card.suit == trump_suit:
                return 1 + (14 - card.rank) / 14
            elif card.suit == led_suit:
                return 2 + (14 - card.rank) / 14
            else:
                return 3 + (14 - card.rank) / 14

        # Play the weakest legal card
        return max(legal_plays, key=card_weakness)

    def _lead_card(self, game_state):
        my_hand = game_state["my_hand"]
        trump_suit = game_state["trump_suit"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        my_position = game_state["my_position"]
        my_bid = bids[my_position]
        my_tricks = tricks_won[my_position]

        # If we've already met our bid, lead a weak card
        if my_tricks >= my_bid:
            return self._lead_weak_card(my_hand, trump_suit)

        # Otherwise, lead a strong card
        return self._lead_strong_card(my_hand, trump_suit)

    def _lead_strong_card(self, hand, trump_suit):
        # Prioritize Wizards > high trump > high non-trump Aces
        def card_strength(card):
            if card.card_type == "wizard":
                return 4
            elif card.card_type == "jester":
                return 0
            elif card.suit == trump_suit:
                return 3 + (card.rank / 14)
            else:
                return 2 if card.rank == 14 else 1 + (card.rank / 14)

        return max(hand, key=card_strength)

    def _lead_weak_card(self, hand, trump_suit):
        # Prioritize Jesters > low non-trump > low trump
        def card_weakness(card):
            if card.card_type == "jester":
                return 4
            elif card.card_type == "wizard":
                return 0
            elif card.suit == trump_suit:
                return 1 + (14 - card.rank) / 14
            else:
                return 2 + (14 - card.rank) / 14

        return max(hand, key=card_weakness)
