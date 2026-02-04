"""
Agent Code: A3-Wizard
Model: openai/gpt-5-mini
Run: 3
Generated: 2026-02-04 16:48:42
"""

import math

class WizardAgent:
    """
    A heuristic-based Wizard agent implementing:
      - a probabilistic bidding strategy based on hand strength and trump
      - a rule-compliant play strategy that tries to achieve the agent's bid:
        * when it needs tricks, plays cards likely to win (Wizards, trumps, high cards)
        * when it must avoid tricks, discards low cards or Jesters
    """
    def __init__(self, name):
        self.name = name
        # remember some internal state across calls
        self.last_bid = None
        self.seen_cards = set()  # can be used for light card-tracking heuristics

    # -------------------------
    # Helper utilities
    # -------------------------
    def _card_strength(self, card, trump_suit):
        """Heuristic strength: higher means more likely to win a trick."""
        if card is None:
            return -1.0
        if card.card_type == "wizard":
            return 200.0
        if card.card_type == "jester":
            return 0.0
        # standard card
        # normalized rank 2..14 -> 0..1
        r = (card.rank - 2) / 12.0
        val = 50.0 * r
        if trump_suit is not None and card.suit == trump_suit:
            val += 40.0  # trump premium
        return val

    def _find_follow_suit(self, current_trick):
        """
        Determine which suit must be followed for the current trick (or None).
        - If first card is Wizard -> no suit requirement (None)
        - If there is a standard card in the trick, the first such card defines the suit
        - If only Jesters so far -> no suit requirement (None)
        """
        if not current_trick:
            return None
        first_card = current_trick[0][1]
        if first_card.card_type == "wizard":
            return None
        # find first standard card
        for _, card in current_trick:
            if card.card_type == "standard":
                return card.suit
        # no standard found (only jesters so far)
        return None

    def _legal_cards(self, my_hand, current_trick, trump_suit):
        """Return subset of my_hand that are legal to play given trick rules."""
        if not current_trick:
            return list(my_hand)
        # If first card was a Wizard -> no suit requirement
        first_card = current_trick[0][1]
        if first_card.card_type == "wizard":
            return list(my_hand)
        # determine suit to follow (first standard card)
        suit = self._find_follow_suit(current_trick)
        if suit is None:
            return list(my_hand)
        # do I have any standard cards in that suit?
        has_suit = any(c.card_type == "standard" and c.suit == suit for c in my_hand)
        if has_suit:
            allowed = []
            for c in my_hand:
                if c.card_type == "wizard" or c.card_type == "jester":
                    allowed.append(c)
                elif c.card_type == "standard" and c.suit == suit:
                    allowed.append(c)
            return allowed
        else:
            return list(my_hand)

    def _evaluate_trick_winner_index(self, trick_cards, trump_suit):
        """
        Given a partial/full trick (list of (player_idx, Card) in play order),
        return the index (0-based in the trick_cards list) of the current winner.
        """
        # 1) If any Wizards were played: first Wizard wins
        for i, (_, c) in enumerate(trick_cards):
            if c.card_type == "wizard":
                return i
        # 2) If all Jesters: first Jester wins
        if all(c.card_type == "jester" for _, c in trick_cards):
            return 0
        # 3) Determine first standard card suit (led suit)
        suit_to_follow = None
        for _, c in trick_cards:
            if c.card_type == "standard":
                suit_to_follow = c.suit
                break
        # 4) Highest trump (if any)
        if trump_suit is not None:
            trumps = [(i, c) for i, (_, c) in enumerate(trick_cards)
                      if c.card_type == "standard" and c.suit == trump_suit]
            if trumps:
                # choose highest rank; if tie, earliest wins (but deck has unique cards)
                best = max(trumps, key=lambda ic: (ic[1].rank, -ic[0]))
                return best[0]
        # 5) Highest in led suit
        if suit_to_follow is not None:
            in_suit = [(i, c) for i, (_, c) in enumerate(trick_cards)
                       if c.card_type == "standard" and c.suit == suit_to_follow]
            if in_suit:
                best = max(in_suit, key=lambda ic: (ic[1].rank, -ic[0]))
                return best[0]
        # fallback
        return 0

    # -------------------------
    # Main interface
    # -------------------------
    def make_move(self, phase, game_state):
        if phase == "bid":
            # Bidding strategy: estimate expected tricks using a simple probabilistic model
            cards_this_round = game_state["cards_this_round"]
            trump = game_state["trump_suit"]
            my_hand = game_state["my_hand"]
            my_pos = game_state["my_position"]
            bids = game_state["bids"]

            expected = 0.0
            # Slightly conservative constants to avoid over-bidding
            for c in my_hand:
                if c.card_type == "wizard":
                    expected += 0.95  # almost certain win if played well
                elif c.card_type == "jester":
                    expected += 0.02  # almost never wins
                else:
                    r = (c.rank - 2) / 12.0  # 0..1
                    if trump is None:
                        # No trump this round: high cards matter more
                        expected += 0.20 + 0.60 * r
                    else:
                        if c.suit == trump:
                            # trump cards strong
                            expected += 0.40 + 0.55 * r
                        else:
                            # non-trump: chance depends on rank
                            expected += 0.08 + 0.45 * r

            # Round to nearest integer but be slightly conservative
            bid = int(math.floor(expected + 0.4))
            # clamp to valid range
            bid = max(0, min(cards_this_round, bid))

            # HOOK RULE: if we're the last bidder, avoid making the sum equal total tricks
            # detect if we're last bidder
            none_count = sum(1 for b in bids if b is None)
            am_last = (none_count == 1 and bids[my_pos] is None)
            if am_last:
                sum_other = sum(b for b in bids if b is not None)
                forbidden = cards_this_round - sum_other
                if bid == forbidden:
                    # choose nearest valid alternative
                    candidates = [i for i in range(0, cards_this_round + 1) if i != forbidden]
                    # choose candidate closest to original bid, tie-breaker lower
                    bid = min(candidates, key=lambda x: (abs(x - bid), x))
            self.last_bid = bid
            return bid

        elif phase == "play":
            my_hand = list(game_state["my_hand"])  # list copy
            trump = game_state["trump_suit"]
            my_pos = game_state["my_position"]
            current_trick = list(game_state["current_trick"])  # [(player_idx, Card), ...]
            bids = game_state["bids"]
            tricks_won = game_state["tricks_won"]

            # Update simple seen-cards memory
            for _, c in current_trick:
                try:
                    self.seen_cards.add(c)
                except Exception:
                    pass  # in case Card isn't hashable in a given environment

            if not my_hand:
                return None

            legal = self._legal_cards(my_hand, current_trick, trump)
            if not legal:
                # fallback: return any card from hand
                return random.choice(my_hand)

            # Determine my target: how many more tricks I must take (positive) or must avoid (<=0)
            my_bid = bids[my_pos] if bids and bids[my_pos] is not None else self.last_bid if self.last_bid is not None else 0
            my_taken = tricks_won[my_pos] if tricks_won is not None else 0
            needed = (my_bid - my_taken) if my_bid is not None else 0
            remaining_tricks = len(my_hand)

            # Determine current winning card in trick so far
            current_winner_idx = None
            current_winner_card = None
            if current_trick:
                current_winner_idx = self._evaluate_trick_winner_index(current_trick, trump)
                current_winner_card = current_trick[current_winner_idx][1]

            # Utility: prefer to play a card that would be currently winning (simulation),
            # but avoid wasting Wizards unless necessary.
            def would_currently_win(candidate):
                # simulate appending our play now and see if we'd be the winner among those played
                seq = list(current_trick) + [(-1, candidate)]
                win_idx = self._evaluate_trick_winner_index(seq, trump)
                return win_idx == (len(seq) - 1)

            # If we want to avoid taking tricks: play the weakest legal card possible (prefer Jester)
            if needed <= 0:
                # Prefer Jester if legal
                jesters = [c for c in legal if c.card_type == "jester"]
                if jesters:
                    return jesters[0]
                # Otherwise play the legal card with minimal strength, but avoid playing a Wizard (which often guarantees a win)
                non_wizards = [c for c in legal if c.card_type != "wizard"]
                if non_wizards:
                    # choose min strength
                    choice = min(non_wizards, key=lambda c: (self._card_strength(c, trump), 1 if c.card_type == "standard" else 0))
                    return choice
                # As a last resort, play the weakest (may be a Wizard only option)
                return min(legal, key=lambda c: self._card_strength(c, trump))

            # If we need to win tricks (needed > 0), attempt to play a card that likely wins
            # 1) If we have a Wizard and there is no earlier Wizard in current_trick -> guaranteed win
            #    Prefer to play a Wizard only if it helps (we need a win now).
            earlier_wizard_present = any(c.card_type == "wizard" for _, c in current_trick)
            legal_wizards = [c for c in legal if c.card_type == "wizard"]
            if legal_wizards and not earlier_wizard_present:
                # use a wizard if we need a guaranteed trick now
                return legal_wizards[0]

            # 2) If we can currently move into the lead (simulation) choose the minimal candidate that does so
            winning_now = [c for c in legal if would_currently_win(c)]
            if winning_now:
                # choose the least costly winning card (lowest strength among winners)
                choice = min(winning_now, key=lambda c: self._card_strength(c, trump))
                return choice

            # 3) If we cannot currently become the lead (or it's risky), try to play a strong card that may win later:
            # Prefer high trumps (if legal), then high standard cards in suits we have many in.
            trumps_legal = [c for c in legal if c.card_type == "standard" and trump is not None and c.suit == trump]
            if trumps_legal:
                # choose strongest trump
                choice = max(trumps_legal, key=lambda c: c.rank)
                return choice

            # 4) Else play the strongest legal standard card (highest rank)
            standard_legal = [c for c in legal if c.card_type == "standard"]
            if standard_legal:
                choice = max(standard_legal, key=lambda c: c.rank)
                return choice

            # 5) As a fallback, play any wizard (if somehow legal and we couldn't use above)
            if legal_wizards:
                return legal_wizards[0]

            # 6) Otherwise play the highest Jester possibility (though not useful)
            jesters = [c for c in legal if c.card_type == "jester"]
            if jesters:
                return jesters[0]

            # Fallback last resort
            return random.choice(legal)
