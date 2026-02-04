"""
Agent Code: A3-Wizard
Model: x-ai/grok-4
Run: 4
Generated: 2026-02-04 16:50:03
"""

from collections import defaultdict

import random
from collections import defaultdict

class WizardAgent:
    def __init__(self, name):
        self.name = name

    def get_legal_cards(self, hand, current_trick, trump):
        played = [c for _, c in current_trick]
        if not played:
            return list(hand)
        first_card = played[0]
        if first_card.card_type == 'wizard':
            return list(hand)
        led_suit = None
        for c in played:
            if c.card_type == 'standard':
                led_suit = c.suit
                break
        if led_suit is None:
            return list(hand)
        has_suit = any(c.card_type == 'standard' and c.suit == led_suit for c in hand)
        if not has_suit:
            return list(hand)
        else:
            return [c for c in hand if c.card_type == 'wizard' or c.card_type == 'jester' or (c.card_type == 'standard' and c.suit == led_suit)]

    def get_current_winner(self, played, trump):
        if not played:
            return None, -1
        for i, c in enumerate(played):
            if c.card_type == 'wizard':
                return c, i
        if all(c.card_type == 'jester' for c in played):
            return played[0], 0
        led_suit = None
        for c in played:
            if c.card_type == 'standard':
                led_suit = c.suit
                break
        max_rank = -1
        winner_idx = -1
        for i, c in enumerate(played):
            if c.card_type != 'standard':
                continue
            relevant = False
            if trump and c.suit == trump:
                relevant = True
            elif led_suit and c.suit == led_suit:
                relevant = True
            if relevant:
                if c.rank > max_rank:
                    max_rank = c.rank
                    winner_idx = i
        return (played[winner_idx] if winner_idx != -1 else None), winner_idx

    def get_card_strength(self, card, trump):
        if card.card_type == 'wizard':
            return 100
        if card.card_type == 'jester':
            return 0
        base = card.rank
        if trump and card.suit == trump:
            base += 20
        return base

    def make_move(self, phase, game_state):
        if phase == "bid":
            hand = game_state["my_hand"]
            trump = game_state["trump_suit"]
            n = game_state["cards_this_round"]
            my_pos = game_state["my_position"]
            bids = game_state["bids"]

            wizards = sum(1 for c in hand if c.card_type == 'wizard')
            jesters = sum(1 for c in hand if c.card_type == 'jester')
            standards = [c for c in hand if c.card_type == 'standard']

            bid = wizards

            suit_groups = defaultdict(list)
            for c in standards:
                suit_groups[c.suit].append(c)

            if trump:
                trump_cards = suit_groups.get(trump, [])
                trump_cards.sort(key=lambda c: c.rank, reverse=True)
                high_trump = sum(1 for c in trump_cards if c.rank >= 11)
                bid += high_trump
                mid_trump = sum(1 for c in trump_cards if 8 <= c.rank <= 10)
                bid += mid_trump // 2
                for suit, cards in suit_groups.items():
                    if suit == trump:
                        continue
                    if cards:
                        max_r = max(c.rank for c in cards)
                        if max_r == 14 and len(cards) > n // 5:
                            bid += 1
            else:
                # No trump, count high cards
                bid += sum(1 for c in standards if c.rank >= 13)
                bid += sum(1 for c in standards if c.rank == 12) // 2

            bid = max(0, min(bid, n))

            # Check if last bidder
            none_count = sum(1 for b in bids if b is None)
            if none_count == 1:  # I'm last
                previous_sum = sum(b for b in bids if b is not None)
                if previous_sum + bid == n:
                    if bid > 0:
                        bid -= 1
                    elif bid + 1 <= n:
                        bid += 1

            return bid

        elif phase == "play":
            hand = game_state["my_hand"]
            if not hand:
                return None
            trump = game_state["trump_suit"]
            current_trick = game_state["current_trick"]
            played = [c for _, c in current_trick]
            legal = self.get_legal_cards(hand, current_trick, trump)

            my_pos = game_state["my_position"]
            needed = game_state["bids"][my_pos] - game_state["tricks_won"][my_pos]
            completed = sum(game_state["tricks_won"])
            remaining = game_state["cards_this_round"] - completed
            want_win = needed > (remaining - 1) / 2.0

            candidates = []
            for card in legal:
                temp_played = played + [card]
                _, winner_idx = self.get_current_winner(temp_played, trump)
                is_winning = (winner_idx == len(played))
                candidates.append((card, is_winning))

            if want_win:
                winning_cards = [card for card, is_win in candidates if is_win]
                if winning_cards:
                    winning_cards.sort(key=lambda c: self.get_card_strength(c, trump))
                    return winning_cards[0]  # lowest strength
                else:
                    legal.sort(key=lambda c: self.get_card_strength(c, trump))
                    return legal[0]  # lowest
            else:
                losing_cards = [card for card, is_win in candidates if not is_win]
                if losing_cards:
                    losing_cards.sort(key=lambda c: self.get_card_strength(c, trump), reverse=True)
                    return losing_cards[0]  # highest strength
                else:
                    legal.sort(key=lambda c: self.get_card_strength(c, trump))
                    return legal[0]  # lowest
