"""
Agent Code: A3-Wizard
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-04 16:50:03
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

    def make_move(self, phase, game_state):
        if phase == "bid":
            return self.bid(game_state)
        elif phase == "play":
            return self.play(game_state)

    def bid(self, game_state):
        hand = game_state["my_hand"]
        trump = game_state["trump_suit"]
        n = game_state["cards_this_round"]
        wizards = sum(1 for c in hand if c.card_type == "wizard")
        jesters = sum(1 for c in hand if c.card_type == "jester")
        standards = [c for c in hand if c.card_type == "standard"]
        trump_high = 0
        non_trump_aces = 0
        if trump:
            for c in standards:
                if c.suit == trump and c.rank >= 12:
                    trump_high += 1
                elif c.rank == 14:
                    non_trump_aces += 1
        else:
            for c in standards:
                if c.rank >= 13:
                    trump_high += 1
        est = wizards + trump_high + (non_trump_aces // 2)
        est = min(est, n - jesters)
        est = max(est, 0)
        if est < 1 and wizards == 0:
            est = 0
        bid = est
        bids = game_state["bids"]
        num_bid = sum(1 for b in bids if b is not None)
        if num_bid == 5:  # I am last
            sum_prev = sum(b for b in bids if b is not None)
            forbidden = n - sum_prev
            if bid == forbidden:
                if bid + 1 <= n:
                    bid += 1
                elif bid - 1 >= 0:
                    bid -= 1
                else:
                    bid = 0
        return bid

    def play(self, game_state):
        hand = game_state["my_hand"]
        if not hand:
            return None
        trump = game_state["trump_suit"]
        current_trick = game_state["current_trick"]
        my_pos = game_state["my_position"]
        my_bid = game_state["bids"][my_pos]
        tricks_won = game_state["tricks_won"][my_pos]
        remaining = len(hand)
        needed = my_bid - tricks_won
        if needed <= 0:
            want_win = False
        elif needed >= remaining:
            want_win = True
        else:
            ratio = needed / remaining
            want_win = ratio > 0.5 or (remaining == 1 and needed == 1)
        legal = self.get_legal_cards(hand, current_trick, trump)
        if not legal:
            return random.choice(hand)
        if not current_trick:
            sorted_legal = sorted(legal, key=lambda c: self.card_value(c, trump))
            if want_win:
                return sorted_legal[-1]  # highest
            else:
                return sorted_legal[0]  # lowest
        current_played = [c for _, c in current_trick]
        candidates = []
        for c in legal:
            sim_played = current_played + [c]
            if self.determine_winner(sim_played, trump) == len(current_played):
                candidates.append(("win", c))
            else:
                candidates.append(("lose", c))
        if want_win:
            winning = [c for status, c in candidates if status == "win"]
            if winning:
                return min(winning, key=lambda c: self.card_value(c, trump))
            else:
                return min(legal, key=lambda c: self.card_value(c, trump))
        else:
            losing = [c for status, c in candidates if status == "lose"]
            if losing:
                return max(losing, key=lambda c: self.card_value(c, trump))
            else:
                return min(legal, key=lambda c: self.card_value(c, trump))

    def get_legal_cards(self, hand, current_trick, trump):
        if not current_trick:
            return list(hand)
        led_card = current_trick[0][1]
        if led_card.card_type == "wizard":
            return list(hand)
        effective_led_suit = None
        for _, c in current_trick:
            if c.card_type == "standard":
                effective_led_suit = c.suit
                break
        if effective_led_suit is None:
            return list(hand)
        have_suit = any(c.card_type == "standard" and c.suit == effective_led_suit for c in hand)
        if not have_suit:
            return list(hand)
        legal = []
        for c in hand:
            if c.card_type in ("wizard", "jester") or (c.card_type == "standard" and c.suit == effective_led_suit):
                legal.append(c)
        return legal

    def card_value(self, card, trump):
        if card.card_type == "wizard":
            return 100
        if card.card_type == "jester":
            return 0
        base = card.rank
        if trump and card.suit == trump:
            base += 20
        return base

    def determine_winner(self, played_cards, trump):
        if not played_cards:
            raise ValueError("No cards played")
        for i in range(len(played_cards)):
            if played_cards[i].card_type == "wizard":
                return i
        if all(c.card_type == "jester" for c in played_cards):
            return 0
        led_suit = None
        for c in played_cards:
            if c.card_type == "standard":
                led_suit = c.suit
                break
        if led_suit is None:
            return 0
        has_trump = False
        if trump is not None:
            has_trump = any(c.card_type == "standard" and c.suit == trump for c in played_cards)
        if has_trump:
            max_rank = -1
            winner = -1
            for i, c in enumerate(played_cards):
                if c.card_type == "standard" and c.suit == trump and c.rank > max_rank:
                    max_rank = c.rank
                    winner = i
            if winner == -1:
                raise ValueError("Has trump but no trump found")
            return winner
        else:
            max_rank = -1
            winner = -1
            for i, c in enumerate(played_cards):
                if c.card_type == "standard" and c.suit == led_suit and c.rank > max_rank:
                    max_rank = c.rank
                    winner = i
            if winner == -1:
                raise ValueError("No led suit card found")
            return winner
