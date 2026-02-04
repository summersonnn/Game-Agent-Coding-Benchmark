"""
Agent Code: A3-Wizard
Model: google/gemma-3-27b-it@preset/fp8
Run: 2
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
        self.round_number = 0
        self.trump_suit = None

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
        self.round_number = game_state["round_number"]
        self.trump_suit = game_state["trump_suit"]

        if phase == "bid":
            cards_this_round = game_state["cards_this_round"]
            my_hand = game_state["my_hand"]
            bids = game_state["bids"]

            bid = self.bid_strategy(my_hand, cards_this_round, bids)

            return bid

        elif phase == "play":
            my_hand = game_state["my_hand"]
            current_trick = game_state["current_trick"]
            trick_leader = game_state["trick_leader"]

            card_to_play = self.play_strategy(my_hand, current_trick, trick_leader)
            return card_to_play

    def bid_strategy(self, hand, cards_this_round, bids):
        """Estimates the number of tricks the agent can win and returns a bid."""

        wizard_count = sum(1 for card in hand if card.card_type == "wizard")
        jester_count = sum(1 for card in hand if card.card_type == "jester")
        high_card_count = sum(1 for card in hand if card.card_type == "standard" and card.rank >= 10)

        # Base bid on hand strength
        bid = wizard_count + max(0, high_card_count - jester_count)

        # Adjust bid based on round number
        bid = min(cards_this_round, max(0, bid))

        #Hook Rule adjustment
        if bids and all(b is not None for b in bids):
            total_bids = sum(bids)
            if total_bids + bid == cards_this_round:
                bid = max(0, bid-1)

        return bid

    def play_strategy(self, hand, current_trick, trick_leader):
        """Determines which card to play based on the current trick."""

        if not hand:
            return None

        if not current_trick:  # First card played in the trick
            # Play Wizard if available
            for card in hand:
                if card.card_type == "wizard":
                    return card
            # Play highest card otherwise
            highest_card = max(hand, key=lambda card: card.rank if card.card_type == "standard" else -1)
            return highest_card
        else:
            # Follow suit if possible
            led_suit = current_trick[0][1].suit
            playable_cards = []
            for card in hand:
                if card.card_type == "standard" and card.suit == led_suit:
                    playable_cards.append(card)
                elif card.card_type == "wizard" or card.card_type == "jester":
                    playable_cards.append(card)
            
            if playable_cards:
                if led_suit is not None:
                    # Find the highest card of the led suit
                    suit_cards = [card for card in playable_cards if card.card_type == "standard" and card.suit == led_suit]
                    if suit_cards:
                        return max(suit_cards, key=lambda card: card.rank)
                    else:
                        return max(playable_cards, key=lambda card: card.rank if card.card_type == "standard" else -1)
                else:
                    return max(playable_cards, key=lambda card: card.rank if card.card_type == "standard" else -1)
            else:
                # No playable cards, should not happen with the defined rules.
                return random.choice(hand)
