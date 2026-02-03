"""
Agent Code: A3-Wizard
Model: openai/gpt-oss-120b@preset/fp8
Run: 4
Generated: 2026-02-03 19:31:33
"""

from typing import List, Optional, Tuple

import random
from typing import List, Optional, Tuple

class WizardAgent:
    """
    A reasonably strong Wizard agent.
    Implements a hand‑strength based bidding strategy and a
    suit‑aware playing strategy that tries to hit its bid while
    respecting the Hook rule for the last bidder.
    """

    def __init__(self, name: str):
        self.name = name

    # --------------------------------------------------------------------
    # Public entry point -------------------------------------------------
    def make_move(self, phase: str, game_state: dict):
        if phase == "bid":
            return self._make_bid(game_state)
        else:  # phase == "play"
            return self._make_play(game_state)

    # --------------------------------------------------------------------
    # Bidding ------------------------------------------------------------
    def _make_bid(self, gs: dict) -> int:
        cards_this_round = gs["cards_this_round"]
        hand: List[Card] = gs["my_hand"]
        trump: Optional[str] = gs["trump_suit"]

        # ----- estimate hand strength ------------------------------------
        wizards = sum(1 for c in hand if c.card_type == "wizard")
        jokers = sum(1 for c in hand if c.card_type == "jester")

        # high trump cards (Jack or higher)
        high_trumps = 0
        if trump:
            high_trumps = sum(
                1
                for c in hand
                if c.card_type == "standard"
                and c.suit == trump
                and c.rank >= 11
            )
        # high non‑trump cards (King or Ace)
        high_norm = sum(
            1
            for c in hand
            if c.card_type == "standard"
            and (trump is None or c.suit != trump)
            and c.rank >= 13
        )

        # crude expected tricks (weights tuned empirically)
        estimate = (
            wizards * 1.0
            + high_trumps * 0.75
            + high_norm * 0.5
            - jokers * 0.1
        )
        bid = max(0, min(cards_this_round, int(round(estimate))))

        # ----- Hook rule (last bidder) -----------------------------------
        bids = gs["bids"]                     # list length 6, None for not yet bid
        my_pos = gs["my_position"]
        if bids.count(None) == 1 and bids[my_pos] is None:
            # we are the last to bid
            total_without_me = sum(b for b in bids if b is not None)
            if total_without_me + bid == cards_this_round:
                # try to move one step away while staying legal
                if bid > 0:
                    bid -= 1
                elif bid < cards_this_round:
                    bid += 1
                else:
                    # fallback – pick a random legal bid
                    bid = random.randint(0, cards_this_round)

        return bid

    # --------------------------------------------------------------------
    # Playing ------------------------------------------------------------
    def _make_play(self, gs: dict) -> "Card":
        hand: List[Card] = gs["my_hand"]
        trump: Optional[str] = gs["trump_suit"]
        current_trick: List[Tuple[int, "Card"]] = gs["current_trick"]
        my_bid: int = gs["bids"][gs["my_position"]]
        tricks_won: int = gs["tricks_won"][gs["my_position"]]
        total_tricks = gs["cards_this_round"]
        tricks_played = sum(gs["tricks_won"])
        remaining_tricks = total_tricks - tricks_played

        need_to_win = max(0, my_bid - tricks_won)  # how many more tricks we still need

        # ----- determine led suit & suit‑following requirement -------------
        led_suit, must_follow = self._led_suit_and_requirement(current_trick, hand)

        # ----- build list of legal cards -----------------------------------
        legal = self._legal_cards(hand, led_suit, must_follow)

        # ----- if we are leading a new trick --------------------------------
        if not current_trick:
            if need_to_win > 0:
                # try to win the trick – lead with our strongest card
                card = self._strongest_card(legal, trump, led_suit)
            else:
                # try to lose – lead with the weakest card
                card = self._weakest_card(legal, trump, led_suit)
            return card

        # ----- we are following ---------------------------------------------
        # current winning card in the trick so far
        cur_winner = self._current_winner(current_trick, trump, led_suit)

        # cards that would overtake the current winner
        winning_opts = [
            c for c in legal if self._beats(c, cur_winner, trump, led_suit)
        ]

        if need_to_win > 0 and winning_opts:
            # we still need tricks – play the *lowest* winning card
            chosen = min(winning_opts, key=lambda c: self._card_strength(c, trump, led_suit))
        else:
            # avoid winning if possible
            losing_opts = [
                c for c in legal if not self._beats(c, cur_winner, trump, led_suit)
            ]
            if losing_opts:
                chosen = min(losing_opts, key=lambda c: self._card_strength(c, trump, led_suit))
            else:
                # forced to win – use the lowest winning card
                chosen = min(legal, key=lambda c: self._card_strength(c, trump, led_suit))

        return chosen

    # --------------------------------------------------------------------
    # Helper: determine led suit & whether we must follow it -------------
    def _led_suit_and_requirement(
        self, trick: List[Tuple[int, "Card"]], hand: List["Card"]
    ) -> Tuple[Optional[str], bool]:
        if not trick:
            return None, False

        first_card = trick[0][1]

        # 1) first card is a Wizard → no suit requirement
        if first_card.card_type == "wizard":
            return None, False

        # 2) first card is a Jester → look for first standard card
        if first_card.card_type == "jester":
            for _, c in trick:
                if c.card_type == "standard":
                    led = c.suit
                    break
            else:
                # all jokers so far
                return None, False
        else:
            # 3) first card is a standard card → its suit leads
            led = first_card.suit

        # do we have any standard card of that suit?
        must_follow = any(
            c.card_type == "standard" and c.suit == led for c in hand
        )
        return led, must_follow

    # --------------------------------------------------------------------
    # Helper: legal cards according to follow‑suit rule -------------------
    def _legal_cards(
        self, hand: List["Card"], led_suit: Optional[str], must_follow: bool
    ) -> List["Card"]:
        if not led_suit or not must_follow:
            return hand[:]  # any card is legal

        # must follow suit, but Wizards/Jesters are always allowed
        follow = [
            c
            for c in hand
            if (c.card_type == "standard" and c.suit == led_suit)
            or c.card_type in ("wizard", "jester")
        ]
        return follow if follow else hand[:]  # fallback (should not happen)

    # --------------------------------------------------------------------
    # Helper: evaluate who is currently winning the trick -----------------
    def _current_winner(
        self,
        trick: List[Tuple[int, "Card"]],
        trump: Optional[str],
        led_suit: Optional[str],
    ) -> "Card":
        winner_card = trick[0][1]
        for _, c in trick[1:]:
            if self._beats(c, winner_card, trump, led_suit):
                winner_card = c
        return winner_card

    # --------------------------------------------------------------------
    # Helper: does card a beat card b given the round context? ------------
    def _beats(
        self, a: "Card", b: "Card", trump: Optional[str], led_suit: Optional[str]
    ) -> bool:
        # Wizards dominate everything
        if a.card_type == "wizard":
            return b.card_type != "wizard"
        if b.card_type == "wizard":
            return False

        # Jesters lose to everything unless all are Jesters
        if a.card_type == "jester":
            return False
        if b.card_type == "jester":
            return True

        # Both are standard cards now
        # trump beats non‑trump
        a_is_trump = trump is not None and a.suit == trump
        b_is_trump = trump is not None and b.suit == trump
        if a_is_trump and not b_is_trump:
            return True
        if b_is_trump and not a_is_trump:
            return False

        # If both are trump (or both non‑trump) and same suit, compare rank
        if a.suit == b.suit:
            return a.rank > b.rank

        # If neither is trump, the card of the led suit wins
        if led_suit:
            if a.suit == led_suit and b.suit != led_suit:
                return True
            if b.suit == led_suit and a.suit != led_suit:
                return False

        # Different non‑trump suits – earlier card wins, so a does NOT beat b
        return False

    # --------------------------------------------------------------------
    # Helper: numeric strength of a card for ordering purposes ------------
    def _card_strength(self, c: "Card", trump: Optional[str], led_suit: Optional[str]) -> int:
        # lower value = weaker card
        if c.card_type == "jester":
            return 0
        if c.card_type == "wizard":
            return 1000
        # standard cards
        base = c.rank
        if trump and c.suit == trump:
            base += 200          # trump boost
        elif led_suit and c.suit == led_suit:
            base += 100          # led‑suit boost
        else:
            base += 0
        return base

    # --------------------------------------------------------------------
    # Helper: strongest / weakest card from a list ------------------------
    def _strongest_card(self, cards: List["Card"], trump: Optional[str], led_suit: Optional[str]) -> "Card":
        return max(cards, key=lambda c: self._card_strength(c, trump, led_suit))

    def _weakest_card(self, cards: List["Card"], trump: Optional[str], led_suit: Optional[str]) -> "Card":
        return min(cards, key=lambda c: self._card_strength(c, trump, led_suit))
