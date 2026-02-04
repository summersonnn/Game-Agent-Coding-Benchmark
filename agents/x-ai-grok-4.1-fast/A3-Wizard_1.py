"""
Agent Code: A3-Wizard
Model: x-ai/grok-4.1-fast
Run: 1
Generated: 2026-02-04 16:54:53
"""



import random

class Card:
    """Represents a single card in the Wizard deck."""
    def __init__(self, card_type, suit=None, rank=None):
        """
        card_type: "wizard", "jester", or "standard"
        suit: "Hearts", "Diamonds", "Clubs", "Spades" (only for standard cards)
        rank: 2-14 where Jack=11, Queen=12, King=13, Ace=14 (only for standard cards)
        """
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
            suit_str = self.suit[0]  # H, D, C, S
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
    
    def get_required_suit(self, current_trick, trick_leader):
        if not current_trick:
            return None
        # Find leader's card
        leader_card = next((c for p, c in current_trick if p == trick_leader), None)
        if not leader_card:
            return None
        if leader_card.card_type == "wizard":
            return None
        if leader_card.card_type == "jester":
            # First standard card determines suit
            for _, c in current_trick:
                if c.card_type == "standard":
                    return c.suit
            return None
        return leader_card.suit
    
    def card_value(self, c, trump):
        if c.card_type == "wizard":
            return 100
        if c.card_type == "jester":
            return 0
        base = 10 + c.rank if c.suit == trump else 5 + c.rank // 2
        return base
    
    def compute_bid_estimate(self, my_hand, trump, cards_this_round):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        hand_count = {s: [] for s in suits}
        num_wiz = 0
        num_jest = 0
        for c in my_hand:
            if c.card_type == "wizard":
                num_wiz += 1
            elif c.card_type == "jester":
                num_jest += 1
            else:
                hand_count[c.suit].append(c.rank)
        # Sort ranks descending
        for s in suits:
            hand_count[s].sort(reverse=True)
        
        # Trump strength
        strong_trump = 0
        if trump:
            trump_ranks = hand_count[trump]
            for i, r in enumerate(trump_ranks):
                if r >= 14 - i:
                    strong_trump += 1
                else:
                    break
        
        # Voids (good for trumping)
        num_voids = sum(1 for ranks in hand_count.values() if len(ranks) == 0)
        
        # Non-trump aces
        num_aces_nontrump = 0
        for s in suits:
            if s != trump and hand_count[s] and hand_count[s][0] == 14:
                num_aces_nontrump += 1
        
        # Estimate
        estimate = num_wiz + strong_trump + (num_aces_nontrump + num_voids) // 2
        
        # Conservative adjustments
        if num_jest >= cards_this_round // 2:
            estimate = 0
        estimate = max(0, min(cards_this_round, int(estimate)))
        
        return estimate
    
    def want_to_win(self, game_state, my_position):
        bid = game_state["bids"][my_position]
        won = game_state["tricks_won"][my_position]
        total_tricks = game_state["cards_this_round"]
        played_tricks = sum(game_state["tricks_won"])
        remaining = total_tricks - played_tricks
        needed = bid - won
        if needed <= 0:
            return False
        if needed >= remaining:
            return True
        return needed / remaining > 0.4  # Slightly conservative threshold
    
    def make_move(self, phase, game_state):
        my_position = game_state["my_position"]
        my_hand = game_state["my_hand"]
        trump = game_state["trump_suit"]
        cards_this_round = game_state["cards_this_round"]
        
        if phase == "bid":
            estimate = self.compute_bid_estimate(my_hand, trump, cards_this_round)
            bid = estimate
            
            # Hook rule check
            bids_list = game_state["bids"]
            sum_so_far = sum(b for b in bids_list if b is not None)
            num_unbid = sum(b is None for b in bids_list)
            if num_unbid == 1:
                if sum_so_far + bid == cards_this_round:
                    possible_bids = [i for i in range(cards_this_round + 1) if sum_so_far + i != cards_this_round]
                    bid = min(possible_bids, key=lambda x: abs(x - estimate))
            
            return max(0, min(cards_this_round, bid))
        
        elif phase == "play":
            current_trick = game_state["current_trick"]
            trick_leader = game_state["trick_leader"]
            required_suit = self.get_required_suit(current_trick, trick_leader)
            
            # Determine candidates
            has_required_suit = any(c.card_type == "standard" and c.suit == required_suit for c in my_hand)
            if required_suit is None or not has_required_suit:
                candidates = my_hand[:]
            else:
                candidates = [c for c in my_hand if c.card_type != "standard" or c.suit == required_suit]
            
            if not candidates:
                return None
            
            # Check current trick state
            current_cards = [c for _, c in current_trick]
            has_wiz_played = any(c.card_type == "wizard" for c in current_cards)
            
            # Decide strategy
            try_win = self.want_to_win(game_state, my_position)
            if has_wiz_played:
                try_win = False
            
            if try_win:
                # Try to win
                wizards = [c for c in candidates if c.card_type == "wizard"]
                if wizards:
                    return random.choice(wizards)
                
                trump_cards = [c for c in candidates if c.card_type == "standard" and c.suit == trump]
                if trump_cards:
                    return max(trump_cards, key=lambda c: c.rank)
                
                suit_cards = [c for c in candidates if c.card_type == "standard" and c.suit == required_suit]
                if suit_cards:
                    return max(suit_cards, key=lambda c: c.rank)
                
                # Fallback highest
                return max(candidates, key=lambda c: self.card_value(c, trump))
            
            else:
                # Try not to win (dump)
                jesters = [c for c in candidates if c.card_type == "jester"]
                if jesters:
                    return random.choice(jesters)
                
                # Lowest non-trump standard first
                standards = [c for c in candidates if c.card_type == "standard"]
                if standards:
                    # Prefer non-trump low, then low rank
                    def low_key(c):
                        trump_penalty = 1 if c.suit == trump else 0
                        return (trump_penalty, c.rank)
                    return min(standards, key=low_key)
                
                # Fallback lowest value
                return min(candidates, key=lambda c: self.card_value(c, trump))
