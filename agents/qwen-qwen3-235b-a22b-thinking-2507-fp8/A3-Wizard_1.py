"""
Agent Code: A3-Wizard
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
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
            cards_this_round = game_state["cards_this_round"]
            my_hand = game_state["my_hand"]
            trump_suit = game_state["trump_suit"]
            
            w = sum(1 for card in my_hand if card.card_type == "wizard")
            trump_strength = 0.0
            if trump_suit is not None:
                for card in my_hand:
                    if card.card_type == "standard" and card.suit == trump_suit:
                        normalized_rank = (card.rank - 1) / 13.0
                        if 4 - w > 0:
                            normalized_rank *= 0.9
                        trump_strength += normalized_rank
            
            total_strength = w + trump_strength
            
            bid = round(total_strength)
            bid = max(0, min(bid, cards_this_round))
            
            if game_state["my_position"] == 5:
                total_so_far = 0
                for i in range(5):
                    bid_val = game_state["bids"][i]
                    if bid_val is not None:
                        total_so_far += bid_val
                forbidden = cards_this_round - total_so_far
                if bid == forbidden:
                    candidates = []
                    for d in range(1, cards_this_round + 2):
                        cand1 = bid - d
                        cand2 = bid + d
                        if 0 <= cand1 <= cards_this_round and cand1 != forbidden:
                            candidates.append(cand1)
                        if 0 <= cand2 <= cards_this_round and cand2 != forbidden:
                            candidates.append(cand2)
                        if candidates:
                            break
                    bid = candidates[0] if candidates else 0
            
            return bid
        
        elif phase == "play":
            my_hand = game_state["my_hand"]
            current_trick = game_state["current_trick"]
            bids = game_state["bids"]
            tricks_won = game_state["tricks_won"]
            my_position = game_state["my_position"]
            trump_suit = game_state["trump_suit"]
            
            tricks_needed = bids[my_position] - tricks_won[my_position]
            want_win = tricks_needed > 0
            
            if not current_trick:
                if want_win:
                    wizards = [c for c in my_hand if c.card_type == "wizard"]
                    if wizards:
                        return wizards[0]
                    
                    if trump_suit is not None:
                        trumps = [c for c in my_hand if c.card_type == "standard" and c.suit == trump_suit]
                        if trumps:
                            trumps.sort(key=lambda c: c.rank, reverse=True)
                            return trumps[0]
                    
                    non_trump = [c for c in my_hand if c.card_type == "standard" and (trump_suit is None or c.suit != trump_suit)]
                    if non_trump:
                        non_trump.sort(key=lambda c: c.rank, reverse=True)
                        return non_trump[0]
                    
                    jesters = [c for c in my_hand if c.card_type == "jester"]
                    if jesters:
                        return jesters[0]
                    
                    return random.choice(my_hand)
                else:
                    jesters = [c for c in my_hand if c.card_type == "jester"]
                    if jesters:
                        return jesters[0]
                    
                    suits_count = {}
                    for card in my_hand:
                        if card.card_type == "standard":
                            suits_count[card.suit] = suits_count.get(card.suit, 0) + 1
                    multi_suit = [suit for suit, count in suits_count.items() if count >= 2]
                    
                    if multi_suit:
                        suit = multi_suit[0]
                        cards_in_suit = [c for c in my_hand if c.card_type == "standard" and c.suit == suit]
                        cards_in_suit.sort(key=lambda c: c.rank)
                        return cards_in_suit[0]
                    
                    standard_cards = [c for c in my_hand if c.card_type == "standard"]
                    if standard_cards:
                        standard_cards.sort(key=lambda c: c.rank)
                        return standard_cards[0]
                    
                    return random.choice(my_hand)
            
            first_card = current_trick[0][1]
            led_suit = None
            if first_card.card_type == "wizard":
                led_suit = None
            elif first_card.card_type == "jester":
                for _, card in current_trick:
                    if card.card_type == "standard":
                        led_suit = card.suit
                        break
            else:
                led_suit = first_card.suit
            
            void_in_led = False
            if led_suit is not None:
                has_led = any(
                    card.card_type == "standard" and card.suit == led_suit
                    for card in my_hand
                )
                void_in_led = not has_led
            
            if led_suit is None:
                has_wizard = any(card.card_type == "wizard" for _, card in current_trick)
                if has_wizard:
                    jesters = [c for c in my_hand if c.card_type == "jester"]
                    if jesters:
                        return jesters[0]
                    standards = [c for c in my_hand if c.card_type == "standard"]
                    if standards:
                        standards.sort(key=lambda c: c.rank)
                        return standards[0]
                    return random.choice(my_hand)
                
                if want_win:
                    wizards = [c for c in my_hand if c.card_type == "wizard"]
                    if wizards:
                        return wizards[0]
                    
                    if trump_suit is not None:
                        current_highest = None
                        for _, card in current_trick:
                            if card.card_type == "standard" and card.suit == trump_suit:
                                if current_highest is None or card.rank > current_highest.rank:
                                    current_highest = card
                        
                        trumps = [c for c in my_hand if c.card_type == "standard" and c.suit == trump_suit]
                        if current_highest:
                            candidates = [c for c in trumps if c.rank > current_highest.rank]
                        else:
                            candidates = trumps
                        
                        if candidates:
                            candidates.sort(key=lambda c: c.rank)
                            return candidates[0]
                    
                    jesters = [c for c in my_hand if c.card_type == "jester"]
                    if jesters:
                        return jesters[0]
                    standards = [c for c in my_hand if c.card_type == "standard"]
                    if standards:
                        standards.sort(key=lambda c: c.rank)
                        return standards[0]
                    return random.choice(my_hand)
                else:
                    jesters = [c for c in my_hand if c.card_type == "jester"]
                    if jesters:
                        return jesters[0]
                    standards = [c for c in my_hand if c.card_type == "standard"]
                    if standards:
                        standards.sort(key=lambda c: c.rank)
                        return standards[0]
                    return random.choice(my_hand)
            
            else:
                if not void_in_led:
                    if want_win:
                        wizards = [c for c in my_hand if c.card_type == "wizard"]
                        if wizards:
                            return wizards[0]
                        
                        if trump_suit == led_suit:
                            current_highest = None
                            for _, card in current_trick:
                                if card.card_type == "standard" and card.suit == led_suit:
                                    if current_highest is None or card.rank > current_highest.rank:
                                        current_highest = card
                            
                            cards_in_suit = [c for c in my_hand if c.card_type == "standard" and c.suit == led_suit]
                            if current_highest:
                                candidates = [c for c in cards_in_suit if c.rank > current_highest.rank]
                            else:
                                candidates = cards_in_suit
                            
                            if candidates:
                                candidates.sort(key=lambda c: c.rank)
                                return candidates[0]
                            cards_in_suit.sort(key=lambda c: c.rank)
                            return cards_in_suit[0]
                        
                        cards_in_suit = [c for c in my_hand if c.card_type == "standard" and c.suit == led_suit]
                        cards_in_suit.sort(key=lambda c: c.rank)
                        return cards_in_suit[0]
                    else:
                        jesters = [c for c in my_hand if c.card_type == "jester"]
                        if jesters:
                            return jesters[0]
                        cards_in_suit = [c for c in my_hand if c.card_type == "standard" and c.suit == led_suit]
                        cards_in_suit.sort(key=lambda c: c.rank)
                        return cards_in_suit[0]
                
                else:
                    if want_win:
                        wizards = [c for c in my_hand if c.card_type == "wizard"]
                        if wizards:
                            return wizards[0]
                        
                        if trump_suit is not None:
                            trumps = [c for c in my_hand if c.card_type == "standard" and c.suit == trump_suit]
                            if trumps:
                                trumps.sort(key=lambda c: c.rank, reverse=True)
                                return trumps[0]
                        
                        jesters = [c for c in my_hand if c.card_type == "jester"]
                        if jesters:
                            return jesters[0]
                        standards = [c for c in my_hand if c.card_type == "standard"]
                        if standards:
                            standards.sort(key=lambda c: c.rank)
                            return standards[0]
                        return random.choice(my_hand)
                    else:
                        jesters = [c for c in my_hand if c.card_type == "jester"]
                        if jesters:
                            return jesters[0]
                        
                        if trump_suit is not None:
                            non_trump = [c for c in my_hand if c.card_type == "standard" and c.suit != trump_suit]
                        else:
                            non_trump = [c for c in my_hand if c.card_type == "standard"]
                        
                        if non_trump:
                            non_trump.sort(key=lambda c: c.rank)
                            return non_trump[0]
                        
                        if trump_suit is not None:
                            trumps = [c for c in my_hand if c.card_type == "standard" and c.suit == trump_suit]
                            if trumps:
                                trumps.sort(key=lambda c: c.rank)
                                return trumps[0]
                        
                        return random.choice(my_hand)
