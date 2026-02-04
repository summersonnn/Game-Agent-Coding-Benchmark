"""
Agent Code: A3-Wizard
Model: openai/gpt-5-mini
Run: 4
Generated: 2026-02-04 16:48:42
"""



class WizardAgent:
    """
    A heuristic Wizard agent with simple memory and practical bidding/playing strategies.
    """
    def __init__(self, name):
        self.name = name
        # Memory across a round
        self.played_cards = set()         # seen cards as tuples (type, suit, rank)
        self.prev_current_trick = []      # snapshot of last seen current_trick
        self.round_number = None

    # --- Utility helpers ---
    def _card_key(self, c):
        return (c.card_type, c.suit, c.rank)

    def _is_standard(self, c):
        return c.card_type == "standard"

    def _is_wizard(self, c):
        return c.card_type == "wizard"

    def _is_jester(self, c):
        return c.card_type == "jester"

    def _allowed_cards(self, my_hand, current_trick, trick_leader, trump_suit):
        # Implements the follow-suit and Wizard/Jester rules; returns sublist of my_hand
        if not current_trick:
            return list(my_hand)

        first_card = current_trick[0][1]
        if first_card.card_type == "wizard":
            return list(my_hand)  # no suit requirement
        elif first_card.card_type == "jester":
            # find first standard card played in this trick
            suit = None
            for _, c in current_trick:
                if c.card_type == "standard":
                    suit = c.suit
                    break
            if suit is None:
                return list(my_hand)  # still no suit requirement
            # must follow suit if possible (but wizards and jesters always allowed)
            has_suit = any((self._is_standard(x) and x.suit == suit) for x in my_hand)
            if has_suit:
                return [x for x in my_hand if self._is_wizard(x) or self._is_jester(x) or (self._is_standard(x) and x.suit == suit)]
            else:
                return list(my_hand)
        else:  # first card is standard
            suit = first_card.suit
            has_suit = any((self._is_standard(x) and x.suit == suit) for x in my_hand)
            if has_suit:
                return [x for x in my_hand if self._is_wizard(x) or self._is_jester(x) or (self._is_standard(x) and x.suit == suit)]
            else:
                return list(my_hand)

    def _led_suit(self, current_trick):
        if not current_trick:
            return None
        first = current_trick[0][1]
        if first.card_type == "standard":
            return first.suit
        # if first is Jester or Wizard, find first standard
        for _, c in current_trick:
            if c.card_type == "standard":
                return c.suit
        return None

    def _current_trick_winner_index(self, trick_cards, trump_suit):
        # trick_cards: list of (player_idx, Card) in play order
        if not trick_cards:
            return None
        # 1) First wizard wins
        for i, (_, c) in enumerate(trick_cards):
            if c.card_type == "wizard":
                return i
        # 2) If only jesters: first jester wins
        if all(c.card_type == "jester" for _, c in trick_cards):
            return 0
        # 3) Otherwise: if any trumps played, highest trump (earliest on ties) wins
        led = self._led_suit(trick_cards)
        if trump_suit is not None:
            trumps = [(i, c) for i, (_, c) in enumerate(trick_cards) if c.card_type == "standard" and c.suit == trump_suit]
            if trumps:
                best_i, best_card = None, None
                for i, card in trumps:
                    if best_card is None or card.rank > best_card.rank:
                        best_i, best_card = i, card
                return best_i
        # 4) Highest in led suit wins
        if led is not None:
            candidates = [(i, c) for i, (_, c) in enumerate(trick_cards) if c.card_type == "standard" and c.suit == led]
            if candidates:
                best_i, best_card = None, None
                for i, card in candidates:
                    if best_card is None or card.rank > best_card.rank:
                        best_i, best_card = i, card
                return best_i
        # fallback (shouldn't happen)
        return 0

    def _simulate_wins_if_played(self, current_trick, card_to_play, trump_suit):
        # returns True if adding card_to_play as the next play would make that card the current winner
        new_trick = list(current_trick) + [(-1, card_to_play)]
        winner_index = self._current_trick_winner_index(new_trick, trump_suit)
        return winner_index == (len(new_trick) - 1)

    def _value_for_sort(self, card, trump_suit, led_suit=None):
        # heuristic numeric value: higher means more powerful
        if card.card_type == "wizard":
            return 200
        if card.card_type == "jester":
            return -10
        base = card.rank if card.rank is not None else 0
        if trump_suit is not None and card.card_type == "standard" and card.suit == trump_suit:
            base += 60
        if led_suit and card.card_type == "standard" and card.suit == led_suit:
            base += 10
        return base

    # --- Bidding logic ---
    def make_move(self, phase, game_state):
        if phase == "bid":
            # Reset round memory when bidding for a new round
            cards_this_round = game_state["cards_this_round"]
            if self.round_number != game_state["round_number"]:
                self.round_number = game_state["round_number"]
                self.played_cards.clear()
                self.prev_current_trick = []

            my_hand = game_state.get("my_hand", [])
            trump = game_state.get("trump_suit", None)
            bids = game_state.get("bids", [None]*6)

            # Heuristic expected tricks
            expected = 0.0
            # Wizards are almost guaranteed winners if played smartly
            num_wizards = sum(1 for c in my_hand if c.card_type == "wizard")
            expected += num_wizards

            # Probabilities for standard cards
            # Conservative mappings to reflect 6-player play
            trump_map = {14:0.95, 13:0.8, 12:0.65, 11:0.5, 10:0.35, 9:0.22, 8:0.15, 7:0.09, 6:0.05, 5:0.03, 4:0.02, 3:0.01, 2:0.01}
            non_trump_map = {14:0.7, 13:0.45, 12:0.28, 11:0.15, 10:0.08, 9:0.05, 8:0.03, 7:0.02, 6:0.01, 5:0.01, 4:0.005, 3:0.005, 2:0.005}

            for c in my_hand:
                if c.card_type != "standard":
                    continue
                if trump and c.suit == trump:
                    expected += trump_map.get(c.rank, 0.02)
                else:
                    expected += non_trump_map.get(c.rank, 0.005)

            # Voids + trumps: if we are void in a suit and hold trumps, we can often take led suits
            suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
            for s in suits:
                has_in_suit = any(self._is_standard(c) and c.suit == s for c in my_hand)
                if not has_in_suit and any(self._is_standard(c) and c.suit == trump for c in my_hand) and trump is not None:
                    expected += 0.12

            # Risk aversion: if expected is very small, prefer bidding 0 (safe 20 points)
            if expected < 0.6:
                bid = 0
            else:
                # Round to nearest integer but bias slightly downwards to avoid overshooting
                bid = int(round(expected - 0.2))
                if bid < 0:
                    bid = 0

            # Clamp to allowed range
            bid = max(0, min(cards_this_round, bid))

            # Hook rule (last bidder cannot make sum equal total)
            my_pos = game_state.get("my_position", 0)
            other_bids = [b for b in bids if b is not None]
            n_none = sum(1 for b in bids if b is None)
            if n_none == 1 and bids[my_pos] is None:
                # I'm last to bid
                forbidden = cards_this_round - sum(other_bids)
                if bid == forbidden:
                    # pick nearest alternative (prefer lower to be safer)
                    # try decreasing first
                    alt = None
                    for d in range(0, cards_this_round+1):
                        # check candidates in order of increasing distance, prefer smaller bids
                        cand_low = bid - d
                        cand_high = bid + d
                        chosen = None
                        if cand_low >= 0 and cand_low != forbidden:
                            chosen = cand_low
                        elif cand_high <= cards_this_round and cand_high != forbidden:
                            chosen = cand_high
                        if chosen is not None:
                            alt = chosen
                            break
                    if alt is not None:
                        bid = alt
                    else:
                        # fall back to random valid bid
                        choices = [x for x in range(0, cards_this_round+1) if x != forbidden]
                        bid = random.choice(choices) if choices else 0

            return int(bid)

        elif phase == "play":
            my_hand = list(game_state.get("my_hand", []))
            if not my_hand:
                return None
            current_trick = list(game_state.get("current_trick", []))
            trump = game_state.get("trump_suit", None)
            trick_leader = game_state.get("trick_leader", None)
            my_pos = game_state.get("my_position", 0)
            bids = game_state.get("bids", [None]*6)
            tricks_won = list(game_state.get("tricks_won", [0]*6))
            cards_this_round = game_state.get("cards_this_round", len(my_hand))

            # Update seen-played memory: record any cards we observe in current_trick
            for _, c in current_trick:
                self.played_cards.add(self._card_key(c))

            # Basic info
            my_bid = bids[my_pos] if bids and bids[my_pos] is not None else 0
            my_won = tricks_won[my_pos]
            need = my_bid - my_won
            completed_tricks = sum(tricks_won)
            remaining_tricks = max(0, cards_this_round - completed_tricks)  # includes current trick if in progress

            allowed = self._allowed_cards(my_hand, current_trick, trick_leader, trump)
            # defensive default: if something weird, pick random allowed
            if not allowed:
                return random.choice(my_hand)

            led_suit = self._led_suit(current_trick)

            # Helpers for selecting min/max by heuristic value
            def weakest(cards):
                return min(cards, key=lambda c: (self._value_for_sort(c, trump, led_suit), random.random()))

            def strongest(cards):
                return max(cards, key=lambda c: (self._value_for_sort(c, trump, led_suit), random.random()))

            # Quick checks
            earlier_wizard = any(c.card_type == "wizard" for _, c in current_trick)
            have_wizard_allowed = any(self._is_wizard(c) for c in allowed)
            have_jester_allowed = any(self._is_jester(c) for c in allowed)

            # If we must win all remaining tricks to meet bid, play aggressively
            must_win_all = need > 0 and need >= remaining_tricks

            # If trying to win at least one now
            if need > 0:
                # If a wizard is allowed and no earlier wizard present -> play a wizard (guaranteed win)
                if have_wizard_allowed and not earlier_wizard:
                    # choose one wizard (no preference)
                    for c in allowed:
                        if c.card_type == "wizard":
                            return c

                # If not leading and we can play a card that would currently make us the winner
                # and either we are last or must_win_all or it's a high-probability card, play it.
                # Simulate candidates sorted by ascending power to select smallest card that wins.
                # We prefer minimal winning card.
                winning_candidates = []
                for c in sorted(allowed, key=lambda x: self._value_for_sort(x, trump, led_suit)):
                    if self._simulate_wins_if_played(current_trick, c, trump):
                        winning_candidates.append(c)

                if winning_candidates:
                    # If we are last to play, playing any candidate that wins now guarantees trick.
                    if len(current_trick) == 5 or must_win_all:
                        # pick the weakest winning candidate (conserve strength)
                        return winning_candidates[0]
                    else:
                        # Not last: prefer wizard (handled above), otherwise be cautious:
                        # Only play a winning candidate if it is fairly strong (trump high or top-of-suit ace/king).
                        for c in winning_candidates:
                            if c.card_type == "standard":
                                val = self._value_for_sort(c, trump, led_suit)
                                if val >= 70 or c.rank >= 13:  # strong trump or ace/king
                                    return c
                        # Otherwise prefer to conserve and not play a winner now
                # If leading and must be aggressive, lead strong
                if not current_trick:
                    if must_win_all:
                        # lead with a wizard if any, else strongest card
                        if have_wizard_allowed:
                            for c in allowed:
                                if c.card_type == "wizard":
                                    return c
                        return strongest(allowed)
                    else:
                        # lead with a strong card to try to take a trick but conserve where possible
                        # prefer high trump or high ace
                        trumps = [c for c in allowed if self._is_standard(c) and c.suit == trump] if trump else []
                        if trumps:
                            # pick highest moderate trump if need
                            trumps_sorted = sorted(trumps, key=lambda x: x.rank, reverse=True)
                            return trumps_sorted[0]
                        # else lead highest non-trump standard if any
                        standards = [c for c in allowed if self._is_standard(c)]
                        if standards:
                            return max(standards, key=lambda x: x.rank)
                        # fallback: play wizard if present
                        if have_wizard_allowed:
                            for c in allowed:
                                if c.card_type == "wizard":
                                    return c
                        # or jester
                        if have_jester_allowed:
                            for c in allowed:
                                if c.card_type == "jester":
                                    return c
                        return strongest(allowed)

                # If no path to win now or prefer not to, fall through to safe play
            # If we do NOT want to win (need <= 0) or failed to pick aggressive move:
            # Try to lose: play jester if available; else play weakest legal card.
            if have_jester_allowed:
                # If current trick only jesters and we are first jester, note that first jester wins.
                if current_trick and all(self._is_jester(c) for _, c in current_trick):
                    # Playing jester would not win unless we are the first jester; if we are not first,
                    # we still prefer a jester to avoid high cards.
                    # If we are first (current_trick empty can't be the case here), but handle safely.
                    pass
                # play jester
                for c in allowed:
                    if c.card_type == "jester":
                        return c

            # If we are forced to follow suit and have only high cards in that suit, try to dump a high card that is less likely to win (if over target)
            if led_suit:
                suit_cards = [c for c in allowed if self._is_standard(c) and c.suit == led_suit]
                if suit_cards:
                    # choose the weakest card in suit (lowest rank)
                    return min(suit_cards, key=lambda x: x.rank)

            # Otherwise, play the weakest allowed card
            return weakest(allowed)

        else:
            return None
