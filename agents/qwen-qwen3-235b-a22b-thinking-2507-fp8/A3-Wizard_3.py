"""
Agent Code: A3-Wizard
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 3
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
        self.bid = None
    
    def make_move(self, phase, game_state):
        if phase == "bid":
            return self._make_bid(game_state)
        elif phase == "play":
            return self._make_play(game_state)
    
    def _make_bid(self, game_state):
        cards_this_round = game_state["cards_this_round"]
        trump_suit = game_state["trump_suit"]
        my_hand = game_state["my_hand"]
        
        n = 0
        n += sum(1 for c in my_hand if c.card_type == "wizard")
        
        if trump_suit is not None:
            n += sum(1 for c in my_hand if c.card_type == "standard" and c.rank == 14)
            suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
            voids = 0
            for suit in suits:
                if suit == trump_suit:
                    continue
                has_suit = any(c.suit == suit for c in my_hand if c.card_type == "standard")
                if not has_suit:
                    voids += 1
            trumps = sum(1 for c in my_hand if c.card_type == "standard" and c.suit == trump_suit)
            n += min(voids, trumps)
        else:
            aces = sum(1 for c in my_hand if c.card_type == "standard" and c.rank == 14)
            n += aces // 2
        
        n = max(0, min(n, cards_this_round))
        
        if game_state["my_position"] == 5:
            total_so_far = sum(b for b in game_state["bids"][:5] if b is not None)
            forbidden = cards_this_round - total_so_far
            if 0 <= forbidden <= cards_this_round:
                if n == forbidden:
                    candidates = [i for i in range(0, cards_this_round + 1) if i != forbidden]
                    if candidates:
                        n = min(candidates, key=lambda x: abs(x - n))
        
        self.bid = n
        return n
    
    def _make_play(self, game_state):
        my_hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        my_pos = game_state["my_position"]
        current_tricks = game_state["tricks_won"][my_pos]
        
        if self.bid is None:
            need_to_win = False
        else:
            need_to_win = (current_tricks < self.bid)
        
        if not current_trick:
            return self._play_lead(my_hand, need_to_win, game_state["trump_suit"])
        
        first_card = current_trick[0][1]
        if first_card.card_type == "wizard":
            return self._play_after_wizard(my_hand, need_to_win)
        elif first_card.card_type == "jester":
            return self._play_after_jester(my_hand, need_to_win, game_state["trump_suit"])
        else:
            led_suit = first_card.suit
            has_led_suit = any(
                c.card_type == "standard" and c.suit == led_suit 
                for c in my_hand
            )
            return self._play_after_standard(
                my_hand, need_to_win, led_suit, has_led_suit, game_state["trump_suit"]
            )
    
    def _play_lead(self, hand, need_to_win, trump_suit):
        jester = [c for c in hand if c.card_type == "jester"]
        if not need_to_win and jester:
            return jester[0]
        
        if need_to_win:
            if trump_suit is not None:
                trumps = [c for c in hand if c.card_type == "standard" and c.suit == trump_suit]
                if trumps:
                    trumps.sort(key=lambda c: c.rank, reverse=True)
                    return trumps[0]
            
            wizards = [c for c in hand if c.card_type == "wizard"]
            if wizards:
                return wizards[0]
            
            aces = [c for c in hand if c.card_type == "standard" and c.rank == 14]
            if aces:
                return aces[0]
            
            standards = [c for c in hand if c.card_type == "standard"]
            if standards:
                standards.sort(key=lambda c: c.rank, reverse=True)
                return standards[0]
        
        non_jesters = [c for c in hand if c.card_type != "jester"]
        if not non_jesters:
            return jester[0]
        
        if trump_suit is not None:
            non_trumps = [c for c in non_jesters 
                          if c.card_type == "standard" and c.suit != trump_suit]
            if non_trumps:
                non_trumps.sort(key=lambda c: c.rank)
                return non_trumps[0]
        
        standards = [c for c in non_jesters if c.card_type == "standard"]
        if standards:
            standards.sort(key=lambda c: c.rank)
            return standards[0]
        
        wizards = [c for c in non_jesters if c.card_type == "wizard"]
        if wizards:
            return wizards[0]
        
        return random.choice(hand)
    
    def _play_after_wizard(self, hand, need_to_win):
        jester = [c for c in hand if c.card_type == "jester"]
        if jester:
            return jester[0]
        
        standards = [c for c in hand if c.card_type == "standard"]
        if standards:
            standards.sort(key=lambda c: c.rank)
            return standards[0]
        
        wizards = [c for c in hand if c.card_type == "wizard"]
        if wizards:
            return wizards[0]
        
        return random.choice(hand)
    
    def _play_after_jester(self, hand, need_to_win, trump_suit):
        jester = [c for c in hand if c.card_type == "jester"]
        if not need_to_win and jester:
            return jester[0]
        
        if need_to_win:
            wizards = [c for c in hand if c.card_type == "wizard"]
            if wizards:
                return wizards[0]
            
            standards = [c for c in hand if c.card_type == "standard"]
            if standards:
                standards.sort(key=lambda c: c.rank, reverse=True)
                return standards[0]
        
        if trump_suit is not None:
            non_trumps = [c for c in hand 
                          if c.card_type == "standard" and c.suit != trump_suit]
            if non_trumps:
                non_trumps.sort(key=lambda c: c.rank)
                return non_trumps[0]
        
        standards = [c for c in hand if c.card_type == "standard"]
        if standards:
            standards.sort(key=lambda c: c.rank)
            return standards[0]
        
        wizards = [c for c in hand if c.card_type == "wizard"]
        if wizards and not need_to_win:
            return wizards[0]
        
        return random.choice(hand)
    
    def _play_after_standard(self, hand, need_to_win, led_suit, has_led_suit, trump_suit):
        jester = [c for c in hand if c.card_type == "jester"]
        if not need_to_win and jester:
            return jester[0]
        
        if has_led_suit:
            led_cards = [c for c in hand 
                         if c.card_type == "standard" and c.suit == led_suit]
            
            if need_to_win:
                wizards = [c for c in hand if c.card_type == "wizard"]
                if wizards:
                    return wizards[0]
                led_cards.sort(key=lambda c: c.rank, reverse=True)
                return led_cards[0]
            else:
                if jester:
                    return jester[0]
                led_cards.sort(key=lambda c: c.rank)
                return led_cards[0]
        
        if need_to_win:
            wizards = [c for c in hand if c.card_type == "wizard"]
            if wizards:
                return wizards[0]
            
            if trump_suit is not None and led_suit != trump_suit:
                trumps = [c for c in hand 
                          if c.card_type == "standard" and c.suit == trump_suit]
                if trumps:
                    trumps.sort(key=lambda c: c.rank, reverse=True)
                    return trumps[0]
        
        if jester:
            return jester[0]
        
        if trump_suit is not None and led_suit != trump_suit:
            non_trumps = [c for c in hand 
                          if c.card_type == "standard" and c.suit != trump_suit]
            if non_trumps:
                non_trumps.sort(key=lambda c: c.rank)
                return non_trumps[0]
        
        standards = [c for c in hand if c.card_type == "standard"]
        if standards:
            standards.sort(key=lambda c: c.rank)
            return standards[0]
        
        wizards = [c for c in hand if c.card_type == "wizard"]
        if wizards and not need_to_win:
            return wizards[0]
        
        return random.choice(hand)
