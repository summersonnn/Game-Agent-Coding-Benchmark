"""
Agent Code: A3-Wizard
Model: x-ai/grok-4.1-fast
Run: 3
Generated: 2026-02-04 16:54:53
"""



import random

class WizardAgent:
    def __init__(self, name):
        self.name = name

    def make_move(self, phase, game_state):
        if phase == "bid":
            hand = game_state["my_hand"]
            trump = game_state["trump_suit"]
            n = game_state["cards_this_round"]
            pos = game_state["my_position"]
            bids_list = game_state["bids"]

            sum_prev = sum(b for b in bids_list if b is not None)
            num_bid = sum(1 for b in bids_list if b is not None)
            is_last_bidder = (num_bid == 5)

            num_wiz = sum(1 for c in hand if c.card_type == "wizard")
            num_jes = sum(1 for c in hand if c.card_type == "jester")
            num_trump = sum(1 for c in hand if trump and c.card_type == "standard" and c.suit == trump)
            high_trump = sum(1 for c in hand if trump and c.card_type == "standard" and c.suit == trump and c.rank >= 12)
            mid_trump = sum(1 for c in hand if trump and c.card_type == "standard" and c.suit == trump and c.rank >= 10)
            high_non = sum(1 for c in hand if c.card_type == "standard" and c.rank >= 13)

            est = num_wiz + high_trump + max(0, (mid_trump - high_trump) * 0.5) + high_non * 0.3
            if num_trump > n // 3:
                est += 0.5
            if num_jes >= 2:
                est -= 0.3

            desired = max(0, min(n, round(est)))

            if is_last_bidder:
                total_would_be = sum_prev + desired
                if total_would_be == n:
                    alt1 = max(0, desired - 1)
                    alt2 = min(n, desired + 1)
                    desired = alt1 if abs(alt1 - est) < abs(alt2 - est) else alt2

            return int(desired)

        elif phase == "play":
            hand = game_state["my_hand"]
            if not hand:
                return None
            my_pos = game_state["my_position"]
            my_bid = game_state["bids"][my_pos]
            my_won = game_state["tricks_won"][my_pos]
            remaining_needed = my_bid - my_won
            remaining_tricks = len(hand)
            trump = game_state["trump_suit"]
            current_trick = game_state["current_trick"]

            # Determine led_suit
            if len(current_trick) == 0:
                led_suit = None
                is_leader = True
            else:
                first_card = current_trick[0][1]
                if first_card.card_type == "wizard":
                    led_suit = None
                elif first_card.card_type == "jester":
                    first_std = next((card for _, card in current_trick if card.card_type == "standard"), None)
                    led_suit = first_std.suit if first_std else None
                else:
                    led_suit = first_card.suit
                is_leader = False

            # Determine legal cards
            has_suit = bool(led_suit and any(c.card_type == "standard" and c.suit == led_suit for c in hand))
            legal_cards = [c for c in hand if not (led_suit and has_suit and c.card_type == "standard" and c.suit != led_suit)]

            # Categorize legal cards
            wizards = [c for c in legal_cards if c.card_type == "wizard"]
            jesters = [c for c in legal_cards if c.card_type == "jester"]
            follows = [c for c in legal_cards if c.card_type == "standard" and c.suit == led_suit]
            off_suits = [c for c in legal_cards if c.card_type == "standard" and c.suit != led_suit]

            # Has wizard already been played?
            wiz_already = any(c.card_type == "wizard" for _, c in current_trick)

            # Decide if we want to win this trick
            if remaining_tricks <= 2:
                want_win = (remaining_needed >= remaining_tricks - 1)
            elif remaining_needed == 0:
                want_win = False
            elif remaining_needed >= remaining_tricks:
                want_win = True
            else:
                want_win = remaining_needed / remaining_tricks > 0.5 or random.random() < 0.2

            if wiz_already:
                want_win = False

            if is_leader:
                # Leading strategy
                if remaining_needed == 0 or not want_win:
                    if jesters:
                        return random.choice(jesters)
                    elif follows or off_suits:
                        stds = follows + off_suits
                        stds.sort(key=lambda c: c.rank)
                        return stds[0]
                # Lead low to draw out high cards or control
                candidates = jesters + follows + off_suits + wizards
                candidates.sort(key=lambda c: 0 if c.card_type == "jester" else c.rank if c.card_type == "standard" else 100)
                return candidates[0]

            else:
                # Non-leader strategy
                if remaining_needed == 0 or not want_win:
                    # Duck: lowest possible
                    if jesters:
                        return random.choice(jesters)
                    if follows:
                        follows.sort(key=lambda c: c.rank)
                        return follows[0]
                    if off_suits:
                        off_suits.sort(key=lambda c: c.rank)
                        return off_suits[0]
                    # Forced to wizard?
                    return random.choice(wizards) if wizards else random.choice(legal_cards)

                # Want to win
                if wizards and not wiz_already:
                    return random.choice(wizards)
                if follows:
                    follows.sort(key=lambda c: c.rank, reverse=True)
                    return follows[0]
                # Trump with off-suit if possible
                my_trumps = [c for c in off_suits if trump and c.suit == trump]
                if my_trumps:
                    my_trumps.sort(key=lambda c: c.rank, reverse=True)
                    return my_trumps[0]
                # Best off-suit or whatever left
                if off_suits:
                    off_suits.sort(key=lambda c: c.rank, reverse=True)
                    return off_suits[0]
                if jesters:
                    return random.choice(jesters)
                return random.choice(wizards) if wizards else random.choice(legal_cards)
