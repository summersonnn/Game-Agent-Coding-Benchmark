"""
Agent Code: A3-Wizard
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-03 19:51:13
"""



import random

class Card:
    def __init__(self, card_type, suit=None, rank=None):
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
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return (self.card_type == other.card_type and 
                self.suit == other.suit and 
                self.rank == other.rank)
    
    def __hash__(self):
        return hash((self.card_type, self.suit, self.rank))

class WizardAgent:
    def __init__(self, name):
        self.name = name
    
    def get_led_suit(self, game_state):
        trick = game_state["current_trick"]
        if not trick:
            return None
        first_card = trick[0][1]
        if first_card.card_type == "standard":
            return first_card.suit
        elif first_card.card_type == "jester":
            for _, card in trick:
                if card.card_type == "standard":
                    return card.suit
            return None
        return None
    
    def card_value_simple(self, card, game_state):
        if card.card_type == "wizard":
            return 100
        if card.card_type == "jester":
            return 0
        trump_suit = game_state["trump_suit"]
        led_suit = self.get_led_suit(game_state)
        
        if led_suit is None:
            if trump_suit is not None and card.suit == trump_suit:
                return 50 + card.rank
            return card.rank
        else:
            if trump_suit is not None and card.suit == trump_suit:
                return 50 + card.rank
            elif card.suit == led_suit:
                return card.rank
        return 1
    
    def make_move(self, phase, game_state):
        if phase == "bid":
            N = game_state["cards_this_round"]
            my_hand = game_state["my_hand"]
            
            base_bid = 0
            base_bid += sum(1 for card in my_hand if card.card_type == "wizard")
            
            trump_suit = game_state["trump_suit"]
            if trump_suit is not None:
                high_trumps = [card for card in my_hand 
                              if card.card_type == "standard" 
                              and card.suit == trump_suit 
                              and card.rank >= 11]
                base_bid += len(high_trumps) // 2
            
            if trump_suit is not None:
                non_trump_aces = len([card for card in my_hand 
                                     if card.card_type == "standard" 
                                     and card.suit != trump_suit 
                                     and card.rank == 14])
            else:
                non_trump_aces = len([card for card in my_hand 
                                     if card.card_type == "standard" 
                                     and card.rank == 14])
            base_bid += non_trump_aces // 2
            
            base_bid = max(0, min(N, base_bid))
            
            if game_state["my_position"] == 5:
                bids = game_state["bids"]
                sum_others = sum(b for b in bids[:5] if b is not None)
                if base_bid == N - sum_others:
                    if base_bid > 0:
                        base_bid -= 1
                    else:
                        base_bid = 1 if N > 0 else 0
            return base_bid
        
        elif phase == "play":
            my_hand = game_state["my_hand"]
            my_pos = game_state["my_position"]
            tricks_won = game_state["tricks_won"][my_pos]
            bid = game_state["bids"][my_pos]
            want_win = tricks_won < bid
            
            trick = game_state["current_trick"]
            if not trick:
                legal_cards = my_hand
            else:
                led_card = trick[0][1]
                if led_card.card_type == "wizard":
                    legal_cards = my_hand
                else:
                    led_suit = self.get_led_suit(game_state)
                    if led_suit is None:
                        legal_cards = my_hand
                    else:
                        standard_in_suit = [card for card in my_hand 
                                          if card.card_type == "standard" 
                                          and card.suit == led_suit]
                        if standard_in_suit:
                            legal_cards = standard_in_suit + [
                                card for card in my_hand 
                                if card.card_type in ["wizard", "jester"]
                            ]
                        else:
                            legal_cards = my_hand
            
            if not legal_cards:
                return my_hand[0] if my_hand else None
            
            if want_win:
                legal_cards.sort(key=lambda c: self.card_value_simple(c, game_state), reverse=True)
                return legal_cards[0]
            else:
                legal_cards.sort(key=lambda c: self.card_value_simple(c, game_state))
                return legal_cards[0]
