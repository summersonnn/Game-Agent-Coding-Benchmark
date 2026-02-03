"""
Agent Code: A3-Wizard
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-03 19:30:37
"""

from collections import defaultdict

import random
from collections import defaultdict

class WizardAgent:
    def __init__(self, name):
        self.name = name
        self.remaining_cards = set()
        self.played_cards = defaultdict(list)
        self.player_stats = [defaultdict(int) for _ in range(6)]
        self.round_history = []

    def make_move(self, phase, game_state):
        if phase == "bid":
            return self._make_bid(game_state)
        elif phase == "play":
            return self._play_card(game_state)

    def _make_bid(self, game_state):
        cards_this_round = game_state["cards_this_round"]
        my_hand = game_state["my_hand"]
        trump_suit = game_state["trump_suit"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]

        # Count guaranteed wins (Wizards)
        wizards = sum(1 for card in my_hand if card.card_type == "wizard")
        guaranteed_wins = wizards

        # Count potential wins (high trump cards and Aces)
        trump_cards = []
        high_non_trump = []
        for card in my_hand:
            if card.card_type == "standard":
                if card.suit == trump_suit:
                    trump_cards.append(card.rank)
                elif card.rank == 14:  # Ace
                    high_non_trump.append(card)

        # Sort trump cards by rank (highest first)
        trump_cards.sort(reverse=True)

        # Calculate potential wins from trump cards
        potential_wins = 0
        for rank in trump_cards:
            # Estimate chance of winning with this trump card
            # Higher cards have better chance
            if rank >= 12:  # Q, K, A
                potential_wins += 0.8
            elif rank >= 10:  # 10, J
                potential_wins += 0.5
            else:
                potential_wins += 0.2

        # Add potential wins from Aces in non-trump suits
        potential_wins += len(high_non_trump) * 0.6

        # Calculate void suits (can trump in)
        suits_in_hand = set(card.suit for card in my_hand if card.card_type == "standard")
        void_suits = 4 - len(suits_in_hand)
        potential_wins += void_suits * 0.3

        # Base bid is guaranteed wins plus potential wins
        base_bid = guaranteed_wins + int(potential_wins)

        # Adjust for position (later positions have more information)
        if my_position == 5:  # Last bidder (dealer)
            # Apply the hook rule
            current_sum = sum(bid for bid in bids if bid is not None)
            if current_sum == cards_this_round - base_bid:
                # Need to adjust bid to avoid the hook
                if base_bid > 0:
                    base_bid -= 1
                else:
                    base_bid += 1

            # Also consider making a more conservative bid as dealer
            base_bid = max(0, min(base_bid, cards_this_round - current_sum - 1))

        # Apply final bounds
        final_bid = max(0, min(base_bid, cards_this_round))

        # Special case: if we have no Wizards and weak hand, consider bidding 0
        if wizards == 0 and potential_wins < 1 and cards_this_round > 3:
            if random.random() < 0.3:  # 30% chance to bid 0 with weak hand
                final_bid = 0

        return final_bid

    def _play_card(self, game_state):
        my_hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        trump_suit = game_state["trump_suit"]
        trick_leader = game_state["trick_leader"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        cards_this_round = game_state["cards_this_round"]

        # Update played cards tracking
        self._update_played_cards(game_state)

        # Determine if we're leading or following
        if not current_trick:
            return self._lead_card(game_state)
        else:
            return self._follow_card(game_state)

    def _lead_card(self, game_state):
        my_hand = game_state["my_hand"]
        trump_suit = game_state["trump_suit"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        cards_this_round = game_state["cards_this_round"]

        # Count remaining tricks and our bid status
        remaining_tricks = cards_this_round - len(game_state["current_trick"])
        tricks_needed = bids[my_position] - tricks_won[my_position]

        # Group cards by type
        wizards = [c for c in my_hand if c.card_type == "wizard"]
        jesters = [c for c in my_hand if c.card_type == "jester"]
        trump_cards = [c for c in my_hand if c.card_type == "standard" and c.suit == trump_suit]
        non_trump_cards = [c for c in my_hand if c.card_type == "standard" and c.suit != trump_suit]

        # Sort cards by strength
        trump_cards.sort(key=lambda c: c.rank, reverse=True)
        non_trump_cards.sort(key=lambda c: c.rank, reverse=True)

        # Strategy based on our bid status
        if tricks_needed <= 0:
            # We've already made our bid, play safe
            if jesters:
                return jesters[0]
            if non_trump_cards:
                return min(non_trump_cards, key=lambda c: c.rank)
            if trump_cards:
                return min(trump_cards, key=lambda c: c.rank)
            return wizards[0] if wizards else my_hand[0]
        else:
            # We need more tricks
            if wizards:
                return wizards[0]
            if trump_cards:
                return trump_cards[0]
            if non_trump_cards:
                # Lead with our highest non-trump card
                return non_trump_cards[0]
            return jesters[0] if jesters else my_hand[0]

    def _follow_card(self, game_state):
        my_hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        trump_suit = game_state["trump_suit"]
        trick_leader = game_state["trick_leader"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        cards_this_round = game_state["cards_this_round"]

        # Determine the led suit
        led_card = current_trick[0][1]
        led_suit = self._get_led_suit(led_card, current_trick)

        # Count remaining tricks and our bid status
        remaining_tricks = cards_this_round - len(game_state["current_trick"])
        tricks_needed = bids[my_position] - tricks_won[my_position]

        # Group our cards
        wizards = [c for c in my_hand if c.card_type == "wizard"]
        jesters = [c for c in my_hand if c.card_type == "jester"]
        trump_cards = [c for c in my_hand if c.card_type == "standard" and c.suit == trump_suit]
        led_suit_cards = [c for c in my_hand if c.card_type == "standard" and c.suit == led_suit]
        other_cards = [c for c in my_hand if c.card_type == "standard" and c.suit != led_suit and c.suit != trump_suit]

        # Sort cards by strength
        trump_cards.sort(key=lambda c: c.rank, reverse=True)
        led_suit_cards.sort(key=lambda c: c.rank, reverse=True)
        other_cards.sort(key=lambda c: c.rank, reverse=True)

        # Determine if we can win this trick
        current_winner = self._get_current_winner(current_trick, trump_suit)
        can_win = False

        if wizards:
            can_win = True
        elif led_suit and led_suit_cards:
            highest_led = max(c.rank for c in led_suit_cards)
            if current_winner[1].card_type == "standard" and current_winner[1].suit == led_suit:
                if highest_led > current_winner[1].rank:
                    can_win = True
        elif trump_suit and trump_cards:
            if current_winner[1].card_type != "wizard":
                can_win = True

        # Strategy based on our bid status
        if tricks_needed <= 0:
            # We've made our bid, try to avoid winning
            if led_suit and led_suit_cards:
                # Play our lowest card in led suit
                return min(led_suit_cards, key=lambda c: c.rank)
            elif jesters:
                return jesters[0]
            elif other_cards:
                return min(other_cards, key=lambda c: c.rank)
            elif trump_cards:
                return min(trump_cards, key=lambda c: c.rank)
            else:
                return wizards[0] if wizards else my_hand[0]
        else:
            # We need more tricks
            if can_win:
                # Play to win
                if wizards:
                    return wizards[0]
                if led_suit and led_suit_cards:
                    # Play our highest card in led suit
                    return max(led_suit_cards, key=lambda c: c.rank)
                if trump_suit and trump_cards:
                    # Play our lowest trump that can win
                    for card in trump_cards:
                        if current_winner[1].card_type != "wizard":
                            return card
                    return trump_cards[0]
            else:
                # Can't win, play safe
                if led_suit and led_suit_cards:
                    return min(led_suit_cards, key=lambda c: c.rank)
                elif jesters:
                    return jesters[0]
                elif other_cards:
                    return min(other_cards, key=lambda c: c.rank)
                else:
                    return min(trump_cards, key=lambda c: c.rank) if trump_cards else wizards[0]

        # Fallback
        return my_hand[0]

    def _get_led_suit(self, led_card, current_trick):
        if led_card.card_type == "wizard":
            return None
        elif led_card.card_type == "jester":
            # Look for first standard card to determine suit
            for _, card in current_trick:
                if card.card_type == "standard":
                    return card.suit
            return None
        else:
            return led_card.suit

    def _get_current_winner(self, current_trick, trump_suit):
        if not current_trick:
            return None

        # Check for Wizards
        wizards = [(i, c) for i, c in current_trick if c.card_type == "wizard"]
        if wizards:
            return wizards[0]

        # Check for Jesters only
        jesters = [(i, c) for i, c in current_trick if c.card_type == "jester"]
        if len(jesters) == len(current_trick):
            return jesters[0]

        # Determine led suit
        led_card = current_trick[0][1]
        led_suit = self._get_led_suit(led_card, current_trick)

        # Find highest trump card
        trump_cards = [(i, c) for i, c in current_trick if c.card_type == "standard" and c.suit == trump_suit]
        if trump_cards:
            return max(trump_cards, key=lambda x: x[1].rank)

        # Find highest card in led suit
        led_suit_cards = [(i, c) for i, c in current_trick if c.card_type == "standard" and c.suit == led_suit]
        if led_suit_cards:
            return max(led_suit_cards, key=lambda x: x[1].rank)

        # Shouldn't reach here
        return current_trick[0]

    def _update_played_cards(self, game_state):
        current_trick = game_state["current_trick"]
        for player_idx, card in current_trick:
            if card not in self.played_cards[player_idx]:
                self.played_cards[player_idx].append(card)
