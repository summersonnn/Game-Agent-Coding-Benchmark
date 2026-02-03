"""
Agent Code: A3-Wizard
Model: openai/gpt-oss-120b@preset/fp8
Run: 3
Generated: 2026-02-03 19:31:33
"""

from typing import List, Tuple, Optional

import random
from typing import List, Tuple, Optional


class WizardAgent:
    """
    A heuristic based Wizard agent.
    - Bids are estimated from hand strength (wizards, high trump, void suits, high cards).
    - The “hook” rule is respected when the agent is the last bidder.
    - During play the agent tries to meet its bid:
        * If it still needs tricks, it plays the lowest card that can win the current trick.
        * Otherwise it discards the lowest legal card (preferring Jesters, then low cards).
    """

    def __init__(self, name: str):
        self.name = name
        # cache for quick rank ordering
        self.rank_order = {r: i for i, r in enumerate(range(2, 15), start=2)}  # 2‑14

    # ------------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------------
    def make_move(self, phase: str, game_state: dict):
        if phase == "bid":
            return self._make_bid(game_state)
        else:  # "play"
            return self._make_play(game_state)

    # ------------------------------------------------------------------------
    # Bidding logic
    # ------------------------------------------------------------------------
    def _make_bid(self, gs: dict) -> int:
        hand: List[Card] = gs["my_hand"]
        n = gs["cards_this_round"]
        trump = gs["trump_suit"]

        # basic strength evaluation
        strength = 0

        # Wizards are guaranteed tricks
        wizards = [c for c in hand if c.card_type == "wizard"]
        strength += len(wizards) * 2  # weight a bit higher

        # Count high trump cards (rank >= 11)
        trump_cards = [c for c in hand
                       if c.card_type == "standard" and c.suit == trump and c.rank >= 11]
        strength += len(trump_cards)

        # Count high cards in other suits (rank >= 12)
        high_others = [c for c in hand
                       if c.card_type == "standard" and c.suit != trump and c.rank >= 12]
        strength += len(high_others) * 0.5

        # Void suits (no cards of a suit) give chance to trump later
        suits = {"Hearts", "Diamonds", "Clubs", "Spades"}
        voids = sum(1 for s in suits if not any(c.suit == s for c in hand
                                                if c.card_type == "standard"))
        strength += voids * 0.3

        # Convert strength to a plausible bid (0‑n)
        bid = min(n, max(0, int(round(strength))))

        # Hook rule handling – are we the last bidder?
        bids = gs["bids"]                     # list of 6 entries, None if not yet bid
        if bids.count(None) == 1:             # only our slot is None → we are last
            current_sum = sum(b for b in bids if b is not None)
            if current_sum + bid == n:        # would violate the hook rule
                # pick the nearest alternative that does NOT make the sum equal n
                alternatives = [b for b in range(0, n + 1)
                                if b != bid and current_sum + b != n]
                if alternatives:
                    bid = random.choice(alternatives)
                else:
                    # fallback – any value that is not the forbidden one
                    bid = (bid + 1) % (n + 1)

        return bid

    # ------------------------------------------------------------------------
    # Playing logic
    # ------------------------------------------------------------------------
    def _make_play(self, gs: dict):
        hand: List[Card] = gs["my_hand"]
        trick: List[Tuple[int, Card]] = gs["current_trick"]
        trump = gs["trump_suit"]
        my_pos = gs["my_position"]
        bids = gs["bids"]
        tricks_won = gs["tricks_won"]
        target_bid = bids[my_pos] if bids[my_pos] is not None else 0
        won_sofar = tricks_won[my_pos]

        # --------------------------------------------------------------------
        # Determine how many more tricks we need
        # --------------------------------------------------------------------
        need_to_win = target_bid - won_sofar
        total_tricks = gs["cards_this_round"]
        completed_tricks = sum(tricks_won)
        remaining_tricks = total_tricks - completed_tricks

        # --------------------------------------------------------------------
        # Determine led suit (if any) and legal cards we may play
        # --------------------------------------------------------------------
        led_suit = self._determine_led_suit(trick)
        legal = self._legal_cards(hand, trick, led_suit)

        # --------------------------------------------------------------------
        # Simple decision: try to win only if we still need tricks
        # --------------------------------------------------------------------
        if need_to_win > 0 and remaining_tricks > 0:
            winning_cards = [c for c in legal if self._would_win(c, trick, trump, led_suit)]
            if winning_cards:
                # play the *lowest* winning card to conserve power
                return self._lowest_winning_card(winning_cards, trump, led_suit)
        # Otherwise (or if we cannot win) discard the lowest legal card
        return self._lowest_card(legal, trump, led_suit)

    # ------------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------------
    def _determine_led_suit(self, trick: List[Tuple[int, Card]]) -> Optional[str]:
        """Return the suit that must be followed, or None if no suit requirement."""
        if not trick:
            return None
        first = trick[0][1]
        if first.card_type == "standard":
            return first.suit
        if first.card_type == "wizard":
            return None
        # first is a Jester – find first standard card in the trick
        for _, c in trick:
            if c.card_type == "standard":
                return c.suit
        return None  # all Jesters

    def _legal_cards(self, hand: List[Card],
                     trick: List[Tuple[int, Card]],
                     led_suit: Optional[str]) -> List[Card]:
        """Return the subset of hand that obeys the follow‑suit rule."""
        if not trick:  # we lead – any card is fine
            return hand[:]

        # Wizards and Jesters are always legal
        legal = [c for c in hand if c.card_type in ("wizard", "jester")]
        # If there is a led suit, we must follow it if we have any standard card of that suit
        if led_suit:
            suit_cards = [c for c in hand
                          if c.card_type == "standard" and c.suit == led_suit]
            if suit_cards:
                legal.extend(suit_cards)
            else:
                # no cards of led suit → any card is allowed (including other standards)
                legal.extend([c for c in hand if c.card_type == "standard"])
        else:
            # No suit requirement (first card was wizard or all jokers)
            legal.extend([c for c in hand if c.card_type == "standard"])
        return legal

    def _current_winner(self, trick: List[Tuple[int, Card]],
                        trump: Optional[str],
                        led_suit: Optional[str]) -> Optional[Card]:
        """Determine the winning card of the already‑played part of the trick."""
        if not trick:
            return None
        # 1. wizard?
        for _, c in trick:
            if c.card_type == "wizard":
                return c
        # 2. trump cards?
        trump_cards = [(i, c) for i, (_, c) in enumerate(trick)
                       if c.card_type == "standard" and c.suit == trump]
        if trump_cards:
            # highest rank trump wins
            _, win = max(trump_cards, key=lambda pair: pair[1].rank)
            return win
        # 3. led suit cards
        led_cards = [(i, c) for i, (_, c) in enumerate(trick)
                     if c.card_type == "standard" and c.suit == led_suit]
        if led_cards:
            _, win = max(led_cards, key=lambda pair: pair[1].rank)
            return win
        # fallback – should not happen, but return first card
        return trick[0][1]

    def _would_win(self, card: Card,
                   trick: List[Tuple[int, Card]],
                   trump: Optional[str],
                   led_suit: Optional[str]) -> bool:
        """Assume we play `card` as the last card of the trick – would we win?"""
        # If a wizard already in trick, first wizard wins → we cannot win
        if any(c.card_type == "wizard" for _, c in trick):
            return False
        # If we play a wizard we win (no earlier wizard)
        if card.card_type == "wizard":
            return True

        # Determine current winner without our card
        winner = self._current_winner(trick, trump, led_suit)

        # If winner is a wizard (handled above) – not possible here
        # Compare our card to winner
        # 1. If we are trump and winner is not trump → we win
        if card.card_type == "standard" and card.suit == trump:
            if winner.card_type != "standard" or winner.suit != trump:
                return True
            # both trump → higher rank wins
            return card.rank > winner.rank

        # 2. Both are non‑trump
        # If we follow led suit and winner does not, we win
        if led_suit and card.card_type == "standard" and card.suit == led_suit:
            if winner.card_type != "standard" or winner.suit != led_suit:
                return True
            # both led suit → higher rank wins
            return card.rank > winner.rank

        # 3. Otherwise we cannot beat the current winner
        return False

    def _card_strength(self, card: Card, trump: Optional[str],
                       led_suit: Optional[str]) -> Tuple[int, int]:
        """
        Helper for sorting cards.
        Lower tuple -> weaker card.
        Order: Jester < low non‑trump < low trump < high trump < high led < Wizard
        """
        if card.card_type == "jester":
            return (0, 0)
        if card.card_type == "wizard":
            return (5, 0)
        # standard card
        is_trump = (card.suit == trump)
        is_led = (card.suit == led_suit)
        base = 1
        if is_trump:
            base = 3
        elif is_led:
            base = 2
        # rank as secondary key (lower rank = weaker)
        return (base, card.rank)

    def _lowest_card(self, cards: List[Card],
                     trump: Optional[str],
                     led_suit: Optional[str]) -> Card:
        """Return the weakest legal card."""
        return min(cards, key=lambda c: self._card_strength(c, trump, led_suit))

    def _lowest_winning_card(self, cards: List[Card],
                             trump: Optional[str],
                             led_suit: Optional[str]) -> Card:
        """Return the weakest card among those that can win."""
        # For winning cards we still want the smallest strength that still wins
        return min(cards, key=lambda c: self._card_strength(c, trump, led_suit))
