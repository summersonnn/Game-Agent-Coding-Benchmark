"""
Agent Code: A3-Wizard
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-04 16:50:03
"""



import random

class WizardAgent:
    def __init__(self, name):
        self.name = name
    
    def make_move(self, phase, game_state):
        if phase == "bid":
            bids = game_state["bids"]
            my_position = game_state["my_position"]
            known_bids = [b for i, b in enumerate(bids) if i != my_position and b is not None]
            sum_known = sum(known_bids)
            is_last = (len(known_bids) == 5)
            n = game_state["cards_this_round"]
            forbidden = n - sum_known if is_last else None
            hand = game_state["my_hand"]
            trump_suit = game_state["trump_suit"]
            wizards = sum(1 for c in hand if c.card_type == 'wizard')
            standard_trump = [c for c in hand if c.card_type == 'standard' and c.suit == trump_suit]
            trump_count = len(standard_trump)
            intended = wizards + (trump_count // 3)
            if standard_trump:
                max_rank = max(c.rank for c in standard_trump)
                if max_rank >= 14:
                    intended += 1
            if trump_suit is None:
                aces = sum(1 for c in hand if c.card_type == 'standard' and c.rank == 14)
                intended += aces // 2
            intended = min(intended, n)
            intended = max(intended, 0)
            if forbidden is not None and intended == forbidden:
                if intended < n:
                    intended += 1
                else:
                    intended -= 1
            intended = max(0, min(intended, n))
            return intended
        
        elif phase == "play":
            my_position = game_state["my_position"]
            my_bid = game_state["bids"][my_position]
            my_tricks = game_state["tricks_won"][my_position]
            total_tricks_won = sum(game_state["tricks_won"])
            remaining = game_state["cards_this_round"] - total_tricks_won
            target = my_bid - my_tricks
            try_win = (target > 0)
            current_trick = game_state["current_trick"]
            led_suit = None
            if current_trick:
                first_card = current_trick[0][1]
                if first_card.card_type == 'wizard':
                    led_suit = None
                elif first_card.card_type == 'standard':
                    led_suit = first_card.suit
                else:  # jester
                    for p, c in current_trick:
                        if c.card_type == 'standard':
                            led_suit = c.suit
                            break
            trump_suit = game_state["trump_suit"]
            my_hand = game_state["my_hand"]
            legal_cards = []
            if led_suit is None:
                legal_cards = list(my_hand)
            else:
                has_led = any(c.card_type == 'standard' and c.suit == led_suit for c in my_hand)
                if has_led:
                    for c in my_hand:
                        if c.card_type == 'wizard' or c.card_type == 'jester' or (c.card_type == 'standard' and c.suit == led_suit):
                            legal_cards.append(c)
                else:
                    legal_cards = list(my_hand)
            def card_key(c):
                if c.card_type == 'wizard':
                    return (4, 15)
                if c.card_type == 'jester':
                    return (0, 0)
                rank = c.rank
                if trump_suit and c.suit == trump_suit:
                    return (3, rank)
                if led_suit and c.suit == led_suit:
                    return (2, rank)
                return (1, rank)
            if not legal_cards:
                return None
            if try_win:
                chosen = max(legal_cards, key=card_key)
            else:
                chosen = min(legal_cards, key=card_key)
            return chosen
