"""
Agent Code: A3-Wizard
Model: x-ai/grok-4.1-fast
Run: 4
Generated: 2026-02-04 16:54:53
"""



import random

class WizardAgent:
    def __init__(self, name):
        self.name = name

    def get_led_suit(self, current_trick):
        if not current_trick:
            return None
        _, first_card = current_trick[0]
        if first_card.card_type == "wizard":
            return None
        if first_card.card_type == "jester":
            for _, card in current_trick:
                if card.card_type == "standard":
                    return card.suit
            return None
        return first_card.suit

    def get_legal_cards(self, hand, led_suit):
        if led_suit is None:
            return hand[:]
        has_led = any(c.card_type == "standard" and c.suit == led_suit for c in hand)
        legal = []
        for c in hand:
            if c.card_type != "standard" or c.suit == led_suit or not has_led:
                legal.append(c)
        return legal

    def get_card_power(self, card, trump_suit):
        if card.card_type == "wizard":
            return 1.1
        if card.card_type == "jester":
            return 0.0
        is_trump = trump_suit is not None and card.suit == trump_suit
        r = card.rank
        if is_trump:
            trump_powers = {2:0.08, 3:0.10, 4:0.12, 5:0.15, 6:0.20, 7:0.25, 8:0.30, 9:0.40, 10:0.50, 11:0.60, 12:0.75, 13:0.90, 14:1.0}
            return trump_powers.get(r, 0.0)
        else:
            non_powers = {2:0.02, 3:0.03, 4:0.04, 5:0.05, 6:0.07, 7:0.09, 8:0.11, 9:0.14, 10:0.18, 11:0.22, 12:0.28, 13:0.35, 14:0.45}
            return non_powers.get(r, 0.0)

    def make_move(self, phase, game_state):
        if phase == "bid":
            trump_suit = game_state["trump_suit"]
            hand = game_state["my_hand"]
            n = game_state["cards_this_round"]
            total_power = sum(self.get_card_power(c, trump_suit) for c in hand)
            preferred = max(0, min(n, round(total_power)))
            bids = game_state["bids"]
            sum_so_far = sum(b for b in bids if b is not None)
            num_bids_made = sum(1 for b in bids if b is not None)
            if num_bids_made == 5:
                avoid = n - sum_so_far
                if 0 <= avoid <= n and preferred == avoid:
                    candidates = [i for i in range(n + 1) if i != avoid]
                    preferred = min(candidates, key=lambda x: abs(x - preferred))
            return preferred
        elif phase == "play":
            hand = game_state["my_hand"]
            if not hand:
                return None
            my_pos = game_state["my_position"]
            my_bid = game_state["bids"][my_pos]
            my_won = game_state["tricks_won"][my_pos]
            n_remaining = len(hand)
            needed = my_bid - my_won
            prob_win = max(0.0, min(1.0, needed / max(1, n_remaining)))
            want_to_win = random.random() < prob_win
            trump_suit = game_state["trump_suit"]
            current_trick = game_state["current_trick"]
            led_suit = self.get_led_suit(current_trick)
            legal = self.get_legal_cards(hand, led_suit)
            has_wiz_played = any(c.card_type == "wizard" for _, c in current_trick)
            if has_wiz_played:
                want_to_win = False
            max_follow_rank = 0
            max_trump_played = 0
            for _, c in current_trick:
                if c.card_type == "standard":
                    if led_suit is not None and c.suit == led_suit:
                        max_follow_rank = max(max_follow_rank, c.rank)
                    if trump_suit is not None and c.suit == trump_suit:
                        max_trump_played = max(max_trump_played, c.rank)
            my_wizards = [c for c in legal if c.card_type == "wizard"]
            my_jesters = [c for c in legal if c.card_type == "jester"]
            my_follow_suit = [c for c in legal if c.card_type == "standard" and c.suit == led_suit]
            my_offsuit = [c for c in legal if c.card_type == "standard" and c.suit != led_suit]
            if want_to_win:
                # Try lowest follow suit winner
                follow_winners = [c for c in my_follow_suit if c.rank > max_follow_rank]
                if follow_winners:
                    return min(follow_winners, key=lambda c: c.rank)
                # Try lowest trump winner
                trump_cards_legal = [c for c in legal if c.card_type == "standard" and c.suit == trump_suit]
                trump_winners = [c for c in trump_cards_legal if c.rank > max_trump_played]
                if trump_winners:
                    return min(trump_winners, key=lambda c: c.rank)
                # Wizard
                if my_wizards:
                    return random.choice(my_wizards)
                # Highest possible
                all_standards = my_follow_suit + my_offsuit
                if all_standards:
                    return max(all_standards, key=lambda c: (1 if c.suit == trump_suit else 0, c.rank))
                return random.choice(legal)
            else:
                # Dump
                if my_jesters:
                    return random.choice(my_jesters)
                if my_follow_suit:
                    return min(my_follow_suit, key=lambda c: c.rank)
                # Lowest offsuit non-trump
                non_trump_off = [c for c in my_offsuit if trump_suit is None or c.suit != trump_suit]
                if non_trump_off:
                    return min(non_trump_off, key=lambda c: c.rank)
                if my_offsuit:
                    return min(my_offsuit, key=lambda c: c.rank)
                # If leading and dump, should have been caught above, but fallback
                if led_suit is None:
                    standards = [c for c in legal if c.card_type == "standard"]
                    non_trump_std = [c for c in standards if trump_suit is None or c.suit != trump_suit]
                    if non_trump_std:
                        return min(non_trump_std, key=lambda c: c.rank)
                    if standards:
                        return min(standards, key=lambda c: c.rank)
                return random.choice(legal)
