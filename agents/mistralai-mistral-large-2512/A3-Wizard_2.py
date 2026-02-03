"""
Agent Code: A3-Wizard
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-03 19:30:37
"""

from collections import defaultdict

import random
from collections import defaultdict

class WizardAgent:
    def __init__(self, name):
        self.name = name
        self.card_strength = {
            'wizard': 100,
            'jester': 0,
            'standard': {
                14: 14,  # Ace
                13: 13,  # King
                12: 12,  # Queen
                11: 11,  # Jack
                10: 10,
                9: 9,
                8: 8,
                7: 7,
                6: 6,
                5: 5,
                4: 4,
                3: 3,
                2: 2
            }
        }
        self.suit_counts = defaultdict(int)
        self.played_cards = []
        self.opponent_bids = []
        self.opponent_tricks = []

    def make_move(self, phase, game_state):
        if phase == "bid":
            return self.make_bid(game_state)
        elif phase == "play":
            return self.play_card(game_state)

    def make_bid(self, game_state):
        cards = game_state["my_hand"]
        trump_suit = game_state["trump_suit"]
        cards_this_round = game_state["cards_this_round"]
        my_position = game_state["my_position"]
        bids = game_state["bids"]

        # Count Wizards and Jesters
        wizards = sum(1 for card in cards if card.card_type == "wizard")
        jesters = sum(1 for card in cards if card.card_type == "jester")

        # Count trump cards and high cards
        trump_cards = []
        high_cards = []
        for card in cards:
            if card.card_type == "standard":
                if card.suit == trump_suit:
                    trump_cards.append(card)
                elif card.rank >= 12:  # Jack or higher
                    high_cards.append(card)

        # Calculate base bid
        base_bid = wizards  # Each wizard is a guaranteed trick

        # Add trump cards that are likely to win
        trump_strength = sum(1 for card in trump_cards if card.rank >= 10)  # 10 or higher
        base_bid += min(trump_strength, len(trump_cards))

        # Add high cards in non-trump suits
        high_card_strength = sum(1 for card in high_cards if card.rank >= 13)  # King or Ace
        base_bid += high_card_strength // 2  # Conservative estimate

        # Adjust for position (later positions can be more aggressive)
        if my_position == 5:  # Last bidder (dealer)
            # Apply hook rule
            current_sum = sum(bid for bid in bids if bid is not None)
            forbidden_bid = cards_this_round - current_sum
            possible_bids = [b for b in range(cards_this_round + 1) if b != forbidden_bid]

            # Choose bid closest to base_bid that's valid
            valid_bid = min(possible_bids, key=lambda x: abs(x - base_bid))
            return valid_bid
        else:
            # Early positions should be more conservative
            return min(base_bid, cards_this_round)

    def play_card(self, game_state):
        my_hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        trump_suit = game_state["trump_suit"]
        trick_leader = game_state["trick_leader"]
        bids = game_state["bids"]
        tricks_won = game_state["tricks_won"]
        my_position = game_state["my_position"]
        cards_this_round = game_state["cards_this_round"]

        # Update played cards history
        self.played_cards.extend(card for _, card in current_trick)

        # If first to play
        if not current_trick:
            return self.play_first_card(my_hand, trump_suit, bids, tricks_won, my_position, cards_this_round)

        # Determine led suit
        led_suit = self.get_led_suit(current_trick, trump_suit)

        # Get current trick status
        current_winner, winning_card = self.get_current_winner(current_trick, trump_suit, led_suit)
        i_am_winning = current_winner == my_position

        # Get my remaining tricks needed
        my_bid = bids[my_position]
        my_tricks = tricks_won[my_position]
        tricks_needed = my_bid - my_tricks
        tricks_remaining = cards_this_round - len(current_trick)

        # Strategy based on whether I need to win this trick
        if tricks_needed > 0:
            # I need more tricks - try to win this one
            return self.play_to_win(my_hand, led_suit, trump_suit, current_trick)
        else:
            # I don't need more tricks - try to avoid winning
            return self.play_to_avoid(my_hand, led_suit, trump_suit, current_trick)

    def play_first_card(self, hand, trump_suit, bids, tricks_won, my_position, cards_this_round):
        # Count remaining tricks needed
        my_bid = bids[my_position]
        my_tricks = tricks_won[my_position]
        tricks_needed = my_bid - my_tricks

        # If I don't need more tricks, play a low card
        if tricks_needed <= 0:
            return self.get_lowest_card(hand, trump_suit)

        # If I need tricks, play a strong card
        wizards = [c for c in hand if c.card_type == "wizard"]
        if wizards:
            return wizards[0]

        trump_cards = [c for c in hand if c.card_type == "standard" and c.suit == trump_suit]
        if trump_cards:
            return max(trump_cards, key=lambda c: c.rank)

        # Play highest card in strongest suit
        suit_strength = self.get_suit_strength(hand, trump_suit)
        strongest_suit = max(suit_strength.keys(), key=lambda s: suit_strength[s])
        suit_cards = [c for c in hand if c.card_type == "standard" and c.suit == strongest_suit]
        return max(suit_cards, key=lambda c: c.rank) if suit_cards else hand[0]

    def play_to_win(self, hand, led_suit, trump_suit, current_trick):
        # Try to play a winning card
        wizards = [c for c in hand if c.card_type == "wizard"]
        if wizards:
            return wizards[0]

        # Check if we can play a trump card to win
        if led_suit != trump_suit:
            trump_cards = [c for c in hand if c.card_type == "standard" and c.suit == trump_suit]
            if trump_cards:
                return max(trump_cards, key=lambda c: c.rank)

        # Play highest card in led suit
        if led_suit:
            led_cards = [c for c in hand if c.card_type == "standard" and c.suit == led_suit]
            if led_cards:
                return max(led_cards, key=lambda c: c.rank)

        # If we can't follow suit, play highest remaining card
        return max(hand, key=lambda c: self.get_card_strength(c, trump_suit))

    def play_to_avoid(self, hand, led_suit, trump_suit, current_trick):
        # Try to play a card that won't win
        jesters = [c for c in hand if c.card_type == "jester"]
        if jesters:
            return jesters[0]

        # If we must follow suit, play lowest card in led suit
        if led_suit:
            led_cards = [c for c in hand if c.card_type == "standard" and c.suit == led_suit]
            if led_cards:
                return min(led_cards, key=lambda c: c.rank)

        # If we can't follow suit, play lowest card
        return self.get_lowest_card(hand, trump_suit)

    def get_led_suit(self, current_trick, trump_suit):
        if not current_trick:
            return None

        first_card = current_trick[0][1]
        if first_card.card_type == "wizard":
            return None
        elif first_card.card_type == "jester":
            # Find first standard card to determine suit
            for _, card in current_trick:
                if card.card_type == "standard":
                    return card.suit
            return None
        else:
            return first_card.suit

    def get_current_winner(self, current_trick, trump_suit, led_suit):
        if not current_trick:
            return None, None

        winning_idx = 0
        winning_card = current_trick[0][1]

        for i, (_, card) in enumerate(current_trick[1:], 1):
            if self.card_beats(winning_card, card, trump_suit, led_suit):
                continue
            else:
                winning_idx = i
                winning_card = card

        return current_trick[winning_idx][0], winning_card

    def card_beats(self, card1, card2, trump_suit, led_suit):
        # Returns True if card1 beats card2
        if card1.card_type == "wizard":
            return True
        if card2.card_type == "wizard":
            return False
        if card1.card_type == "jester":
            return False
        if card2.card_type == "jester":
            return True

        # Both are standard cards
        card1_trump = card1.suit == trump_suit
        card2_trump = card2.suit == trump_suit

        if card1_trump and not card2_trump:
            return True
        if not card1_trump and card2_trump:
            return False
        if card1.suit == card2.suit:
            return card1.rank > card2.rank
        if card1.suit == led_suit:
            return True
        if card2.suit == led_suit:
            return False
        return True  # Neither follows suit, first card wins

    def get_card_strength(self, card, trump_suit):
        if card.card_type == "wizard":
            return 100
        if card.card_type == "jester":
            return 0
        if card.suit == trump_suit:
            return 50 + card.rank
        return card.rank

    def get_lowest_card(self, hand, trump_suit):
        # Get the lowest card that's not a trump
        non_trump_cards = [c for c in hand if not (c.card_type == "standard" and c.suit == trump_suit)]
        if non_trump_cards:
            return min(non_trump_cards, key=lambda c: self.get_card_strength(c, trump_suit))
        return min(hand, key=lambda c: self.get_card_strength(c, trump_suit))

    def get_suit_strength(self, hand, trump_suit):
        suit_strength = defaultdict(int)
        for card in hand:
            if card.card_type == "standard":
                if card.suit == trump_suit:
                    suit_strength[card.suit] += card.rank * 2  # Trump cards are stronger
                else:
                    suit_strength[card.suit] += card.rank
        return suit_strength
