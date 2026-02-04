"""
Agent Code: A3-Wizard
Model: google/gemma-3-27b-it@preset/fp8
Run: 4
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
        # Initialize agent's state
        self.round_history = []  # Store bid and tricks won for each round
        self.opponent_bids = []

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
            return self.bid(game_state)
        elif phase == "play":
            return self.play(game_state)

    def bid(self, game_state):
        """
        Calculates the bid based on hand analysis.
        """
        cards_this_round = game_state["cards_this_round"]
        my_hand = game_state["my_hand"]
        bids = game_state["bids"]
        
        wizard_count = sum(1 for card in my_hand if card.card_type == "wizard")
        jester_count = sum(1 for card in my_hand if card.card_type == "jester")
        
        # Basic bidding strategy:
        # - Wizards are almost guaranteed wins
        # - Adjust bid based on high cards and trump cards (if known)
        # - Factor in the number of Jesters (reduce bid)
        
        bid = wizard_count  # Start with the number of Wizards
        
        # Add points for high cards (Ace, King, Queen, Jack)
        for card in my_hand:
            if card.card_type == "standard":
                if card.rank >= 11:
                    bid += 1

        # Subtract points for Jesters
        bid -= jester_count

        # Cap the bid at the number of cards
        bid = max(0, min(bid, cards_this_round))

        # Hook rule adjustment
        if game_state["my_position"] == 5:  # Last bidder
            total_bids = sum(b for b in bids if b is not None)
            if bid + total_bids == cards_this_round:
                bid = max(0, min(bid - 1, cards_this_round))  # Reduce bid if it completes the total
        
        return bid

    def play(self, game_state):
        """
        Plays a card based on the current trick and hand.
        """
        my_hand = game_state["my_hand"]
        current_trick = game_state["current_trick"]
        trick_leader = game_state["trick_leader"]
        trump_suit = game_state["trump_suit"]

        if not my_hand:
            return None  # No cards to play

        if not current_trick:  # I am the trick leader
            # Play highest Wizard if available
            for card in sorted(my_hand, key=lambda c: c.rank if c.card_type == "standard" else 100 if c.card_type == "wizard" else 0, reverse=True):
                return card
            
        else:  # Someone else led the trick
            led_card = current_trick[0][1]
            
            if led_card.card_type == "wizard":
                # No suit requirement, play highest card
                for card in sorted(my_hand, key=lambda c: c.rank if c.card_type == "standard" else 100 if c.card_type == "wizard" else 0, reverse=True):
                    return card
            elif led_card.card_type == "jester":
                # First standard card determines the suit
                led_suit = None
                for player_idx, card in current_trick:
                    if card.card_type == "standard":
                        led_suit = card.suit
                        break

                if led_suit:
                    # Try to follow suit
                    for card in my_hand:
                        if card.card_type == "standard" and card.suit == led_suit:
                            return card
                    # If no suit, play highest card
                    for card in sorted(my_hand, key=lambda c: c.rank if c.card_type == "standard" else 100 if c.card_type == "wizard" else 0, reverse=True):
                        return card
                else:
                    # All Jesters, play a Jester if we have one
                    for card in my_hand:
                        if card.card_type == "jester":
                            return card
                    # Otherwise, play highest card
                    for card in sorted(my_hand, key=lambda c: c.rank if c.card_type == "standard" else 100 if c.card_type == "wizard" else 0, reverse=True):
                        return card
            else:  # Led card is standard
                led_suit = led_card.suit
                
                # Try to follow suit
                for card in my_hand:
                    if card.card_type == "standard" and card.suit == led_suit:
                        return card
                
                # If we can't follow suit, play a Wizard if we have one
                for card in my_hand:
                    if card.card_type == "wizard":
                        return card
                
                # Otherwise, play a Jester if we have one
                for card in my_hand:
                    if card.card_type == "jester":
                        return card
                
                # If no other options, play the highest remaining card
                for card in sorted(my_hand, key=lambda c: c.rank if c.card_type == "standard" else 100 if c.card_type == "wizard" else 0, reverse=True):
                    return card

        return random.choice(my_hand)  # Should never reach here, but just in case
