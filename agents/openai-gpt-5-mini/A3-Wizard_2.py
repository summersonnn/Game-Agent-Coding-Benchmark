"""
Agent Code: A3-Wizard
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-04 16:48:42
"""

import math

class WizardAgent:
    """
    A reasonably strong heuristic-based Wizard agent.
    Bidding strategy estimates trick-winning probability per card (wizards, trumps, high cards).
    Playing strategy tries to:
      - win minimal necessary tricks when still short of bid (play smallest card that currently wins,
        otherwise play a strong candidate),
      - avoid winning once bid is satisfied (play low-power card or a Jester if legal),
      - always obey the follow-suit / wizard/jester rules.
    The agent keeps a small memory of seen cards within a round to slightly improve bidding behavior.
    """
    def __init__(self, name):
        self.name = name
        self._current_round = None
        self._seen_cards = set()   # set of Card objects seen played this round
        self._last_bid = None

    # -------------------------
    # Helper utilities
    # -------------------------
    def _reset_for_round(self, round_number):
        self._current_round = round_number
        self._seen_cards.clear()
        self._last_bid = None

    def _card_power(self, card, trump_suit):
        """Numerical heuristic power of a card (higher => stronger)."""
        if card.card_type == "wizard":
            return 100
        if card.card_type == "jester":
            return 0
        # standard card
        base = card.rank  # 2..14
        if trump_suit is not None and card.suit == trump_suit:
            return 50 + base  # trump boosted
        return base

    def _led_suit_from_trick(self, current_trick):
        """Determine the suit that must be followed (or None if no suit requirement)."""
        if not current_trick:
            return None
        first_card = current_trick[0][1]
        if first_card.card_type == "wizard":
            return None
        if first_card.card_type == "jester":
            # first standard card determines suit
            for (_, c) in current_trick:
                if c.card_type == "standard":
                    return c.suit
            return None
        # first card is standard
        return first_card.suit

    def _determine_trick_winner(self, trick, trump_suit):
        """
        Given a partial/full trick (list of (player_idx, Card) in play order),
        returns the winning player_idx for the current trick state.
        """
        # 1) Any wizard? first wizard wins
        for (player_idx, card) in trick:
            if card.card_type == "wizard":
                return player_idx

        # 2) All jesters?
        if all(card.card_type == "jester" for (_, card) in trick):
            return trick[0][0]

        # 3) Otherwise: look for trump cards among standard cards
        first_standard = None
        for (_, card) in trick:
            if card.card_type == "standard":
                first_standard = card
                break
        if first_standard is None:
            # shouldn't happen (we handled all-jesters and wizards above), default to first
            return trick[0][0]

        led_suit = first_standard.suit
        # trump cards
        if trump_suit is not None:
            trump_cards = [(p, c) for (p, c) in trick if c.card_type == "standard" and c.suit == trump_suit]
            if trump_cards:
                # highest rank trump wins
                best = max(trump_cards, key=lambda pc: pc[1].rank)
                return best[0]

        # otherwise highest card in led suit
        led_cards = [(p, c) for (p, c) in trick if c.card_type == "standard" and c.suit == led_suit]
        if led_cards:
            best = max(led_cards, key=lambda pc: pc[1].rank)
            return best[0]
        # fallback
        return trick[0][0]

    def _valid_plays(self, my_hand, current_trick, trump_suit):
        """
        Return list of cards from my_hand that are legal to play given current_trick.
        Implements the MUST FOLLOW SUIT rule and the Wizard/Jester exceptions.
        """
        if not current_trick:
            return list(my_hand)  # leading: any card allowed

        led_suit = self._led_suit_from_trick(current_trick)

        if led_suit is None:
            # no suit requirement (wizard led or only jesters so far)
            return list(my_hand)

        # If led_suit is determined (a standard card was played earlier),
        # and we have standard cards of that suit, we must play one of them OR wizard/jester
        suit_cards = [c for c in my_hand if c.card_type == "standard" and c.suit == led_suit]
        wizards_jesters = [c for c in my_hand if c.card_type in ("wizard", "jester")]
        if suit_cards:
            return suit_cards + wizards_jesters
        # no cards in led suit: can play any card
        return list(my_hand)

    # -------------------------
    # Bidding logic
    # -------------------------
    def _estimate_tricks_from_hand(self, my_hand, trump_suit, cards_this_round):
        """
        Heuristic estimate (float) of expected number of tricks the hand can win.
        Uses weighted contributions from wizards, trumps, and high non-trump cards.
        """
        wizards = [c for c in my_hand if c.card_type == "wizard"]
        jesters = [c for c in my_hand if c.card_type == "jester"]
        standard = [c for c in my_hand if c.card_type == "standard"]
        trumps = [c for c in standard if trump_suit is not None and c.suit == trump_suit]
        nontrumps = [c for c in standard if not (trump_suit is not None and c.suit == trump_suit)]

        est = 0.0
        # Wizards are very strong winners, but small discount for multiple wizards (later ones might be redundant)
        for i, w in enumerate(wizards):
            est += 0.9 * (0.95 if i == 0 else 0.85)  # first wizard especially reliable

        # Trumps: stronger ranks add more
        for t in sorted(trumps, key=lambda c: c.rank, reverse=True):
            r = t.rank
            if r >= 14:
                p = 0.9
            elif r >= 13:
                p = 0.75
            elif r >= 11:
                p = 0.6
            elif r >= 9:
                p = 0.45
            else:
                p = 0.25
            # Slight boost if multiple trumps (good for taking multiple tricks)
            p *= (1.0 + 0.04 * (len(trumps) - 1))
            est += p

        # Non-trump high cards (aces and kings are valuable)
        for c in nontrumps:
            r = c.rank
            if r >= 14:
                p = 0.75
            elif r >= 13:
                p = 0.55
            elif r >= 12:
                p = 0.4
            elif r >= 11:
                p = 0.25
            else:
                p = 0.12
            est += p

        # Slight adjustment for number of cards: longer hands are more volatile -> be conservative
        if cards_this_round <= 3:
            factor = 1.0
        elif cards_this_round <= 6:
            factor = 0.92
        elif cards_this_round <= 8:
            factor = 0.82
        else:
            factor = 0.72
        est *= factor

        # Bound estimate between 0 and number of cards
        est = max(0.0, min(est, cards_this_round))
        return est

    # -------------------------
    # Main interface
    # -------------------------
    def make_move(self, phase, game_state):
        if phase == "bid":
            cards_this_round = game_state["cards_this_round"]
            round_number = game_state["round_number"]
            trump_suit = game_state["trump_suit"]
            my_hand = game_state["my_hand"]
            bids = game_state["bids"]
            my_pos = game_state["my_position"]

            # Reset per-round memory if new round
            if round_number != self._current_round:
                self._reset_for_round(round_number)

            # Estimate expected tricks
            est = self._estimate_tricks_from_hand(my_hand, trump_suit, cards_this_round)

            # Convert estimate to integer bid with slight rounding toward safer (lower) for marginal values
            bid = int(math.floor(est + 0.5))

            # Conservative tweak: if estimate small (<0.4) prefer 0
            if est < 0.45:
                bid = 0

            # Ensure within legal bounds
            bid = max(0, min(bid, cards_this_round))

            # Enforce the Hook Rule if we're the last bidder (only one None left and it's us)
            none_count = sum(1 for b in bids if b is None)
            if none_count == 1 and bids[my_pos] is None:
                sum_so_far = sum(b for b in bids if b is not None)
                if sum_so_far + bid == cards_this_round:
                    # pick nearest alternative bid that does not make sum equal total
                    # try small adjustments by distance
                    for delta in [1, -1, 2, -2, 3, -3, 4, -4]:
                        candidate = bid + delta
                        if 0 <= candidate <= cards_this_round and (sum_so_far + candidate) != cards_this_round:
                            bid = candidate
                            break
                    else:
                        # fallback: brute force pick first valid
                        for candidate in range(0, cards_this_round + 1):
                            if (sum_so_far + candidate) != cards_this_round:
                                bid = candidate
                                break

            # store last bid
            self._last_bid = bid
            return bid

        elif phase == "play":
            # Update per-round memory with any newly seen cards in current_trick
            current_trick = game_state["current_trick"]
            for (_, c) in current_trick:
                # Card implements __hash__, safe to add
                try:
                    self._seen_cards.add(c)
                except Exception:
                    pass  # defensive

            my_hand = list(game_state["my_hand"])
            trump_suit = game_state["trump_suit"]
            my_pos = game_state["my_position"]
            bids = game_state["bids"]
            tricks_won = game_state["tricks_won"]
            my_bid = bids[my_pos] if bids is not None else None
            my_tricks = tricks_won[my_pos]
            cards_this_round = game_state["cards_this_round"]

            # Safety fallback
            if not my_hand:
                return None

            # Determine legal plays
            valid = self._valid_plays(my_hand, current_trick, trump_suit)
            if not valid:
                # shouldn't happen, but pick random card from hand
                return random.choice(my_hand)

            # Convenience: simulate whether playing a card would currently make us the trick winner
            def would_be_current_winner(card):
                hypothetical = list(current_trick) + [(my_pos, card)]
                winner = self._determine_trick_winner(hypothetical, trump_suit)
                return winner == my_pos

            # Determine needs
            remaining_tricks_total = cards_this_round - sum(tricks_won)
            need = 0
            if my_bid is not None:
                need = my_bid - my_tricks

            # Sorting helpers
            valid_sorted_by_power_asc = sorted(valid, key=lambda c: (self._card_power(c, trump_suit), c.card_type))
            valid_sorted_by_power_desc = list(reversed(valid_sorted_by_power_asc))

            # If we still need to win tricks -> attempt to win (but try to use minimal winning card)
            if need > 0:
                # If there's an immediate play that makes us the current trick winner, play the weakest such card
                for card in valid_sorted_by_power_asc:
                    if would_be_current_winner(card):
                        # Avoid wasting a Wizard if not necessary: prefer non-wizard minimal winner if available
                        if card.card_type == "wizard":
                            # check if a non-wizard can also win; if yes prefer it
                            nonwizard_winner = None
                            for c2 in valid_sorted_by_power_asc:
                                if c2.card_type != "wizard" and would_be_current_winner(c2):
                                    nonwizard_winner = c2
                                    break
                            if nonwizard_winner:
                                return nonwizard_winner
                        return card

                # No immediate winning play: if leading, play a strong card to try to win
                if not current_trick:
                    # prefer a high trump, then high non-trump
                    for c in valid_sorted_by_power_desc:
                        if c.card_type != "jester":
                            # avoid playing a wizard immediately if we have alternatives, unless we really need to secure wins
                            if c.card_type == "wizard":
                                # if we have multiple wizards and need many tricks, use wizard; otherwise try next best
                                wizards = [x for x in my_hand if x.card_type == "wizard"]
                                if len(wizards) > 1 or need >= len(wizards):
                                    return c
                                # otherwise skip wizard for now
                                continue
                            return c
                    # fallback
                    return valid_sorted_by_power_desc[0]

                # Not leading and cannot currently secure trick: play a reasonable strong card (highest-power) to try to outlast others
                return valid_sorted_by_power_desc[0]

            else:
                # We do NOT want to win any more tricks (either bid is satisfied or we had no bid)
                # Try to play the weakest legal card that will NOT make us the current winner.
                for card in valid_sorted_by_power_asc:
                    if not would_be_current_winner(card):
                        return card
                # If every legal card would currently make us the winner (rare), dump the weakest card
                return valid_sorted_by_power_asc[0]

        else:
            # Unknown phase - fallback
            return None
