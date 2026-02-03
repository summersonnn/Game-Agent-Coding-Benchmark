"""
Agent Code: A3-Wizard
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-03 19:31:33
"""

from typing import List, Optional, Tuple

import random
from typing import List, Optional, Tuple

# -------------------------------------------------------------------------------
class WizardAgent:
    """
    A heuristic‑based Wizard agent.
    • Bids are estimated from hand strength (wizards, high trump, high cards).
    • The “hook” rule is respected when the agent is the dealer (last bidder).
    • During play the agent tracks how many tricks it still needs to meet its bid
      and either tries to win or to lose the current trick accordingly.
    • All suit‑following rules are enforced; illegal plays will be corrected by the
      game engine, so the agent makes sure to return only legal cards.
    """

    def __init__(self, name: str):
        self.name = name
        # these are refreshed each round
        self.my_bid: Optional[int] = None          # the bid we announced this round
        self.tricks_needed: Optional[int] = None   # how many more tricks we must win
        self.trump: Optional[str] = None           # trump suit for the round

    # ---------------------------------------------------------------------------
    # Helper utilities
    # ---------------------------------------------------------------------------
    @staticmethod
    def _card_strength(card, trump: Optional[str], led_suit: Optional[str]) -> Tuple[int, int]:
        """
        Returns a tuple that can be compared to rank cards for winning a trick.
        Higher tuple => stronger card.

        Ordering (from strongest to weakest):
            1. Wizard
            2. Trump (by rank)
            3. Card of led suit (by rank)
            4. Other standard cards (by rank)
            5. Jester
        """
        if card.card_type == "wizard":
            return (5, 0)                     # strongest, rank not needed
        if card.card_type == "jester":
            return (0, 0)                     # weakest

        # standard card
        rank = card.rank
        if trump and card.suit == trump:
            return (4, rank)                  # trump beats everything else
        if led_suit and card.suit == led_suit:
            return (3, rank)                  # follows led suit
        return (2, rank)                      # other suit (low)

    @staticmethod
    def _has_suit(hand: List['Card'], suit: str) -> bool:
        return any(c.card_type == "standard" and c.suit == suit for c in hand)

    def _determine_led_suit(self, current_trick: List[Tuple[int, 'Card']]) -> Optional[str]:
        """
        Implements the “following suit” rule described in the spec.
        Returns the suit that must be followed, or None if there is no requirement.
        """
        if not current_trick:
            return None

        first_card = current_trick[0][1]

        # 1. first card is a wizard → no suit requirement
        if first_card.card_type == "wizard":
            return None

        # 2. first card is a jester → look for the first *standard* card
        if first_card.card_type == "jester":
            for _, c in current_trick[1:]:
                if c.card_type == "standard":
                    return c.suit
            return None   # all jesters so far

        # 3. first card is a standard card → its suit is led
        if first_card.card_type == "standard":
            return first_card.suit

        return None  # fallback (should not happen)

    # ---------------------------------------------------------------------------
    # Bidding
    # ---------------------------------------------------------------------------
    def _estimate_hand_strength(self, hand: List['Card'], trump: Optional[str]) -> int:
        """
        Very simple heuristic:
            • each wizard = 1 guaranteed trick
            • each trump >= Jack (rank >= 11) = 0.75 trick
            • each non‑trump ace = 0.5 trick
            • each non‑trump king = 0.3 trick
        The sum is rounded to the nearest integer and clipped to the round size.
        """
        strength = 0.0
        for c in hand:
            if c.card_type == "wizard":
                strength += 1.0
            elif c.card_type == "standard":
                if trump and c.suit == trump:
                    if c.rank >= 11:          # J, Q, K, A
                        strength += 0.75
                else:
                    if c.rank == 14:          # Ace
                        strength += 0.5
                    elif c.rank == 13:        # King
                        strength += 0.3
        return int(round(strength))

    def _apply_hook_rule(self, desired: int, bids: List[Optional[int]],
                         cards_this_round: int, my_pos: int) -> int:
        """
        If we are the dealer (last to bid) we cannot make the total bids equal
        the number of tricks. Adjust the bid by moving one step up or down.
        """
        # check if we are last to bid
        later_positions = range(my_pos + 1, 6)
        if any(bids[p] is None for p in later_positions):
            # not last
            return desired

        # sum of already‑made bids (excluding our own slot)
        known_sum = sum(b for b in bids if b is not None)
        # our bid would make total = known_sum + desired
        if known_sum + desired == cards_this_round:
            # try to move down first, otherwise up
            if desired > 0:
                return desired - 1
            elif desired < cards_this_round:
                return desired + 1
            else:   # edge case, just return 0
                return 0
        return desired

    def make_move(self, phase: str, game_state: dict):
        # -----------------------------------------------------------------------
        # BIDDING PHASE
        # -----------------------------------------------------------------------
        if phase == "bid":
            hand = game_state["my_hand"]
            cards_this_round = game_state["cards_this_round"]
            trump = game_state["trump_suit"]
            my_pos = game_state["my_position"]
            bids = game_state["bids"]

            # estimate strength and clip to legal range
            est = self._estimate_hand_strength(hand, trump)
            bid = max(0, min(est, cards_this_round))

            # respect the hook rule if we are the dealer (last bidder)
            bid = self._apply_hook_rule(bid, bids, cards_this_round, my_pos)

            # store for later use in the round
            self.my_bid = bid
            self.tricks_needed = bid          # at start we still need all of them
            self.trump = trump

            return bid

        # -----------------------------------------------------------------------
        # PLAYING PHASE
        # -----------------------------------------------------------------------
        elif phase == "play":
            hand: List['Card'] = game_state["my_hand"]
            current_trick: List[Tuple[int, 'Card']] = game_state["current_trick"]
            trump = game_state["trump_suit"]
            cards_this_round = game_state["cards_this_round"]
            tricks_won = game_state["tricks_won"]
            my_pos = game_state["my_position"]

            # update how many tricks we still need to win
            if self.my_bid is not None:
                self.tricks_needed = self.my_bid - tricks_won[my_pos]

            # number of tricks already played in this round
            tricks_played = sum(tricks_won)
            remaining_tricks = cards_this_round - tricks_played

            # decide whether we are trying to win this trick
            need_to_win = (self.tricks_needed is not None) and (self.tricks_needed > 0)

            # determine led suit (if any) according to the rules
            led_suit = self._determine_led_suit(current_trick)

            # -------------------------------------------------------------------
            # Build list of legal cards we may play
            # -------------------------------------------------------------------
            legal_cards = []

            # does the rule force us to follow a suit?
            must_follow = False
            if led_suit:
                if self._has_suit(hand, led_suit):
                    must_follow = True

            for c in hand:
                if must_follow:
                    # we must play a card of the led suit, unless it is a wizard/jester
                    if c.card_type in ("wizard", "jester"):
                        legal_cards.append(c)
                    elif c.card_type == "standard" and c.suit == led_suit:
                        legal_cards.append(c)
                else:
                    # no restriction – any card is legal
                    legal_cards.append(c)

            # sanity fallback (should never happen)
            if not legal_cards:
                legal_cards = hand[:]

            # -------------------------------------------------------------------
            # Choose a card
            # -------------------------------------------------------------------
            # Helper to sort by strength
            def strength_key(card):
                return self._card_strength(card, trump, led_suit)

            if need_to_win:
                # play the strongest legal card
                chosen = max(legal_cards, key=strength_key)
            else:
                # try to lose: play the weakest legal card
                chosen = min(legal_cards, key=strength_key)

            # update internal tracking (if we actually win the trick later the game engine
            # will adjust tricks_won; we only keep the needed count for the next call)
            return chosen

        # -----------------------------------------------------------------------
        # Unexpected phase – should never happen
        # -----------------------------------------------------------------------
        else:
            raise ValueError(f"Unknown phase '{phase}' for WizardAgent")
