"""
Agent Code: A3-Wizard
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 4
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
    
    def make_move(self, phase, game_state):
        if phase == "bid":
            n = game_state["cards_this_round"]
            trump_suit = game_state["trump_suit"]
            my_hand = game_state["my_hand"]
            my_position = game_state["my_position"]
            
            base_bid = 0.0
            num_wizards = len([c for c in my_hand if c.card_type == "wizard"])
            base_bid += num_wizards
            
            if trump_suit is not None:
                for card in my_hand:
                    if card.card_type == "standard" and card.suit == trump_suit:
                        base_bid += (card.rank - 1) / 13.0
                for card in my_hand:
                    if card.card_type == "standard" and card.suit != trump_suit:
                        if card.rank == 14:
                            base_bid += 0.3
                        elif card.rank == 13:
                            base_bid += 0.1
            else:
                for card in my_hand:
                    if card.card_type == "standard" and card.rank == 14:
                        base_bid += 0.8
            
            if my_position == 5:
                current_sum = sum(b for b in game_state["bids"][:5] if b is not None)
                forbidden = n - current_sum
            else:
                forbidden = None
            
            valid_bids = [i for i in range(0, n+1) if forbidden is None or i != forbidden]
            best_bid = None
            min_diff = float('inf')
            for b in valid_bids:
                diff = abs(b - base_bid)
                if diff < min_diff:
                    min_diff = diff
                    best_bid = b
                elif diff == min_diff and b < best_bid:
                    best_bid = b
            return best_bid
        
        elif phase == "play":
            my_hand = game_state["my_hand"]
            current_trick = game_state["current_trick"]
            trump_suit = game_state["trump_suit"]
            my_position = game_state["my_position"]
            
            if not current_trick:
                suit_to_follow = None
            else:
                first_card = current_trick[0][1]
                if first_card.card_type == "wizard":
                    suit_to_follow = None
                elif first_card.card_type == "jester":
                    suit_to_follow = None
                    for _, card in current_trick:
                        if card.card_type == "standard":
                            suit_to_follow = card.suit
                            break
                else:
                    suit_to_follow = first_card.suit
            
            legal_plays = []
            if suit_to_follow is None:
                legal_plays = my_hand.copy()
            else:
                for card in my_hand:
                    if (card.card_type == "standard" and card.suit == suit_to_follow) \
                       or card.card_type == "wizard" \
                       or card.card_type == "jester":
                        legal_plays.append(card)
                if not legal_plays:
                    legal_plays = my_hand.copy()
            
            target = game_state["bids"][my_position]
            current_tricks_won = game_state["tricks_won"][my_position]
            need_win = (target > current_tricks_won)
            
            if need_win:
                if not any(card[1].card_type == "wizard" for card in current_trick):
                    wizards = [c for c in legal_plays if c.card_type == "wizard"]
                    if wizards:
                        return wizards[0]
                
                if trump_suit is not None:
                    current_trump = [card[1] for card in current_trick 
                                    if card[1].card_type == "standard" and card[1].suit == trump_suit]
                    if current_trump:
                        current_high = max(current_trump, key=lambda c: c.rank)
                        candidates = [c for c in legal_plays 
                                     if c.card_type == "standard" and c.suit == trump_suit and c.rank > current_high.rank]
                        if candidates:
                            return min(candidates, key=lambda c: c.rank)
                    else:
                        candidates = [c for c in legal_plays 
                                     if c.card_type == "standard" and c.suit == trump_suit]
                        if candidates:
                            return min(candidates, key=lambda c: c.rank)
                
                if suit_to_follow is not None:
                    current_led = [card[1] for card in current_trick 
                                  if card[1].card_type == "standard" and card[1].suit == suit_to_follow]
                    if current_led:
                        current_high = max(current_led, key=lambda c: c.rank)
                        candidates = [c for c in legal_plays 
                                     if c.card_type == "standard" and c.suit == suit_to_follow and c.rank > current_high.rank]
                        if candidates:
                            return min(candidates, key=lambda c: c.rank)
                    else:
                        candidates = [c for c in legal_plays 
                                     if c.card_type == "standard" and c.suit == suit_to_follow]
                        if candidates:
                            return min(candidates, key=lambda c: c.rank)
                
                standard_cards = [c for c in legal_plays if c.card_type == "standard"]
                if standard_cards:
                    return max(standard_cards, key=lambda c: c.rank)
                
                return legal_plays[0] if legal_plays else None
            
            else:
                jesters = [c for c in legal_plays if c.card_type == "jester"]
                if jesters:
                    return jesters[0]
                
                if suit_to_follow is not None:
                    led_cards = [c for c in legal_plays 
                                if c.card_type == "standard" and c.suit == suit_to_follow]
                    if led_cards:
                        return min(led_cards, key=lambda c: c.rank)
                
                standard_cards = [c for c in legal_plays if c.card_type == "standard"]
                if standard_cards:
                    return min(standard_cards, key=lambda c: c.rank)
                
                wizards = [c for c in legal_plays if c.card_type == "wizard"]
                if wizards:
                    return wizards[0]
                
                return legal_plays[0] if legal_plays else None
