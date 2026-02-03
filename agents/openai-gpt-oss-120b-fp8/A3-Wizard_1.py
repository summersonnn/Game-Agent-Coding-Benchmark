"""
Agent Code: A3-Wizard
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-03 19:31:33
"""

from typing import List, Optional

import random
from typing import List, Optional

class WizardAgent:
    """
    A rule‑based Wizard agent with a simple hand‑evaluation for bidding
    and a suit‑aware play strategy that tries to meet its bid.
    """
    def __init__(self, name: str):
        self.name = name
        self.current_bid: Optional[int] = None          # bid for the active round
        self.current_round: Optional[int] = None        # round number of the active round

    # -----------------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------------
    def _reset_round_state(self, round_number: int) -> None:
        """Reset stored round‑specific data when a new round starts."""
        if self.current_round != round_number:
            self.current_bid = None
            self.current_round = round_number

    def _estimate_tricks(self, hand: List["Card"], trump: Optional[str]) -> int:
        """
        Very rough hand strength estimate:
          • each Wizard = 1 trick
          • each trump rank >= Jack (11) = 0.7
          • each trump rank 2‑10 = 0.4
          • each non‑trump Ace = 0.5
          • each non‑trump rank >= King (13) = 0.4
        The sum is rounded to the nearest integer and capped to the number
        of cards in hand.
        """
        score = 0.0
        for c in hand:
            if c.card_type == "wizard":
                score += 1.0
            elif c.card_type == "jester":
                continue
            else:   # standard
                if c.suit == trump:
                    if c.rank >= 11:      # Jack or higher in trump
                        score += 0.7
                    else:
                        score += 0.4
                else:
                    if c.rank == 14:       # Ace
                        score += 0.5
                    elif c.rank >= 13:     # King / Queen
                        score += 0.4
        return max(0, min(len(hand), int(round(score))))

    def _legal_plays(self, hand: List["Card"], current_trick: List[tuple],
                     trump: Optional[str]) -> List["Card"]:
        """
        Return the subset of `hand` that satisfies the suit‑following rule.
        """
        # No cards have been played yet → any card is legal
        if not current_trick:
            return hand[:]

        # Determine led suit (if any)
        led_suit = None
        for _, card in current_trick:
            if card.card_type == "wizard":
                led_suit = None
                break                     # wizard leads – no suit requirement
            if card.card_type == "standard":
                led_suit = card.suit
                break
            # if jester, keep looking for first standard card

        # If no led suit (wizard first or only jesters so far) → any card legal
        if led_suit is None:
            return hand[:]

        # Does the player hold any standard card of the led suit?
        has_led = any(
            c.card_type == "standard" and c.suit == led_suit
            for c in hand
        )

        if has_led:
            # Must follow the suit, unless playing a wizard or jester
            legal = [
                c for c in hand
                if c.card_type in ("wizard", "jester") or
                   (c.card_type == "standard" and c.suit == led_suit)
            ]
        else:
            # No cards in led suit → anything is allowed
            legal = hand[:]

        return legal

    def _choose_card_to_win(self, legal: List["Card"], trump: Optional[str]) -> "Card":
        """
        Choose the strongest card among the legal ones that is most likely to
        capture the trick.
        Preference order:
          1. Wizard (first wizard wins)
          2. Highest trump
          3. Highest card of led suit (if led suit present in legal set)
          4. Highest remaining standard card
        """
        # 1. Wizard
        for c in legal:
            if c.card_type == "wizard":
                return c

        # 2. Highest trump
        trump_cards = [c for c in legal if c.card_type == "standard" and c.suit == trump]
        if trump_cards:
            return max(trump_cards, key=lambda x: x.rank)

        # 3. Highest card of the led suit (if any)
        # The led suit is the suit of the first non‑jester, non‑wizard card
        # in the current trick. We can infer it from the legal set:
        led_suit_cards = [c for c in legal if c.card_type == "standard"]
        if led_suit_cards:
            return max(led_suit_cards, key=lambda x: x.rank)

        # 4. Fallback – highest card overall
        standard_cards = [c for c in legal if c.card_type == "standard"]
        if standard_cards:
            return max(standard_cards, key=lambda x: x.rank)

        # If we somehow have only jesters, return any
        return legal[0]

    def _choose_card_to_lose(self, legal: List["Card"], trump: Optional[str]) -> "Card":
        """
        Choose a low‑value card that is unlikely to win.
        Preference order:
          1. Jester
          2. Lowest non‑trump standard card
          3. Lowest trump (if forced)
          4. Lowest wizard (only if forced)
        """
        # 1. Jester
        for c in legal:
            if c.card_type == "jester":
                return c

        # 2. Lowest non‑trump standard card
        non_trump = [
            c for c in legal
            if c.card_type == "standard" and c.suit != trump
        ]
        if non_trump:
            return min(non_trump, key=lambda x: x.rank)

        # 3. Lowest trump (if we have only trump cards)
        trump_cards = [c for c in legal if c.card_type == "standard" and c.suit == trump]
        if trump_cards:
            return min(trump_cards, key=lambda x: x.rank)

        # 4. Lowest wizard (last resort)
        wizard_cards = [c for c in legal if c.card_type == "wizard"]
        if wizard_cards:
            return wizard_cards[0]

        # Fallback – any card
        return legal[0]

    # -----------------------------------------------------------------------
    # Core interface
    # -----------------------------------------------------------------------
    def make_move(self, phase: str, game_state: dict):
        """
        Implements both bidding and playing phases.
        """
        # Keep round state up‑to‑date
        self._reset_round_state(game_state["round_number"])

        if phase == "bid":
            return self._make_bid(game_state)

        elif phase == "play":
            return self._make_play(game_state)

        else:
            raise ValueError(f"Unknown phase: {phase}")

    # -----------------------------------------------------------------------
    # Bidding
    # -----------------------------------------------------------------------
    def _make_bid(self, gs: dict) -> int:
        hand = gs["my_hand"]
        N = gs["cards_this_round"]
        trump = gs["trump_suit"]
        position = gs["my_position"]
        bids = gs["bids"]                     # list of 6 entries (int or None)

        # Estimate base bid from hand strength
        estimated = self._estimate_tricks(hand, trump)

        # Adjust for the Hook rule if we are the last bidder (dealer)
        # We are last if every other entry in bids is already filled.
        others_filled = all(
            (b is not None) or (i == position)
            for i, b in enumerate(bids)
        )
        if others_filled:
            total_others = sum(b for i, b in enumerate(bids) if i != position and b is not None)
            prohibited = N - total_others
            if 0 <= prohibited <= N and estimated == prohibited:
                # Move away from the prohibited value – pick the nearest alternative
                if estimated < N:
                    estimated += 1
                else:
                    estimated -= 1

        # Clamp to legal range
        bid = max(0, min(N, estimated))

        # Store for later play decisions
        self.current_bid = bid
        return bid

    # -----------------------------------------------------------------------
    # Playing
    # -----------------------------------------------------------------------
    def _make_play(self, gs: dict):
        hand = gs["my_hand"]
        trump = gs["trump_suit"]
        current_trick = gs["current_trick"]          # list of (player_idx, Card)
        tricks_won = gs["tricks_won"][gs["my_position"]]
        total_tricks = gs["cards_this_round"]
        bid = self.current_bid if self.current_bid is not None else 0

        # Remaining tricks we still need to capture
        needed = bid - tricks_won
        remaining_cards = len(hand)

        # Determine whether we should try to win this trick
        # Simple heuristic:
        #   - If we still need to win more tricks than the number of cards left,
        #     we must try to win every remaining trick.
        #   - Otherwise, win only if we still need some and we have a good chance.
        must_win_all = needed == remaining_cards
        try_to_win = needed > 0 and (must_win_all or random.random() < 0.6)

        # Compute legal plays according to the suit‑following rule
        legal = self._legal_plays(hand, current_trick, trump)

        # Choose card based on the goal
        if try_to_win:
            chosen = self._choose_card_to_win(legal, trump)
        else:
            chosen = self._choose_card_to_lose(legal, trump)

        # Remove the chosen card from our hand for internal consistency
        # (the external engine also removes it; this is just to keep our
        #  internal view correct if we ever query the hand again)
        hand.remove(chosen)
        return chosen
