"""
Agent Code: A3-Wizard
Model: google/gemma-3-27b-it@preset/fp8
Run: 3
Generated: 2026-02-04 16:47:48
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

# -------------------------------------------------------------------------------
class WizardAgent:
    """
    Your agent implementation goes here.
    Implement smart bidding and playing logic to maximize your score.
    """
    def __init__(self, name):
        self.name = name
        # TODO: Initialize your agent's state here
    
    def make_move(self, phase, game_state):
        """
        Called during both bidding and playing phases.
        
        Parameters:
        -----------
        phase : str
            Either "bid" or "play"
        
        game_state : dict
            Complete public game information containing:
            {
                "round_number": int (1-10),
                "cards_this_round": int (same as round_number),
                "trump_suit": str or None ("Hearts", "Diamonds", "Clubs", "Spades", or None),
                "my_hand": [Card, ...] (your current cards),
                "my_position": int (0-5, your seat position),
                "current_trick": [(player_idx, Card), ...] (cards played in current trick),
                "trick_leader": int or None (who led this trick, None if you're first),
                "bids": [int or None, ...] (length 6, bids for all players, None if not yet bid),
                "tricks_won": [int, ...] (length 6, tricks won by each player this round),
                "scores": [int, ...] (length 6, total scores across all rounds),
            }
        
        Returns:
        --------
        If phase == "bid":
            Return an integer from 0 to game_state["cards_this_round"]
        
        If phase == "play":
            Return a Card object from your hand that you want to play
            Must be a valid card following the suit rules described above
        """
        if phase == "bid":
            # TODO: Implement your bidding strategy
            # You must return an integer from 0 to cards_this_round
            cards_this_round = game_state["cards_this_round"]
            my_hand = game_state["my_hand"]
            
            wizard_count = sum(1 for card in my_hand if card.card_type == "wizard")
            jester_count = sum(1 for card in my_hand if card.card_type == "jester")
            
            high_card_count = sum(1 for card in my_hand if card.card_type == "standard" and card.rank >= 10)
            
            bid = 0
            if wizard_count > 0:
                bid += wizard_count
            if high_card_count > 0:
                bid += min(high_card_count, cards_this_round - wizard_count)
            
            bid = min(bid, cards_this_round)
            
            # Adjust bid based on jesters
            if jester_count > 0:
                bid = max(0, bid - 1)
            
            return bid
        
        elif phase == "play":
            # TODO: Implement your card-playing strategy
            # You must return a Card object from your hand
            # Remember to follow suit if required!
            my_hand = game_state["my_hand"]
            current_trick = game_state["current_trick"]
            trick_leader = game_state["trick_leader"]
            trump_suit = game_state["trump_suit"]

            if not my_hand:
                return None

            if not current_trick:  # I am the trick leader
                # Play highest wizard if available
                for card in sorted(my_hand, key=lambda c: c.rank if c.card_type == "standard" else float('inf'), reverse=True):
                    if card.card_type == "wizard":
                        return card
                # Play highest trump if available
                if trump_suit:
                    for card in sorted(my_hand, key=lambda c: c.rank if c.card_type == "standard" and c.suit == trump_suit else float('-inf'), reverse=True):
                        if card.card_type == "standard" and card.suit == trump_suit:
                            return card
                # Play highest card otherwise
                return max(my_hand, key=lambda c: c.rank if c.card_type == "standard" else float('-inf'))
            else:
                # Follow suit if possible
                led_suit = current_trick[0][1].suit
                playable_cards = [card for card in my_hand if card.card_type == "standard" and card.suit == led_suit]
                if playable_cards:
                    return max(playable_cards, key=lambda c: c.rank)
                # Play trump if possible
                if trump_suit:
                    trump_cards = [card for card in my_hand if card.card_type == "standard" and card.suit == trump_suit]
                    if trump_cards:
                        return max(trump_cards, key=lambda c: c.rank)
                # Play a jester if possible
                for card in my_hand:
                    if card.card_type == 'jester':
                        return card
                # Play lowest card otherwise
                return min(my_hand, key=lambda c: c.rank if c.card_type == "standard" else float('inf'))
