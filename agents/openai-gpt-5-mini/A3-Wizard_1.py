"""
Agent Code: A3-Wizard
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-04 16:48:42
"""



class WizardAgent:
    """
    A reasonably strong Wizard agent with heuristic bidding and play logic.
    """
    def __init__(self, name):
        self.name = name
        # Per-round memory
        self.seen_cards = set()   # Cards observed played this round
        self.last_round = None
        self.my_last_bid = None

    # ----------------- Helper utilities -----------------
    def _reset_for_round(self, round_number):
        self.seen_cards.clear()
        self.last_round = round_number
        self.my_last_bid = None

    def _update_seen(self, current_trick):
        for _, card in current_trick:
            # Card is hashable as provided by the Card class
            self.seen_cards.add(card)

    def _get_legal_cards(self, my_hand, current_trick, trump_suit):
        # If no cards have been played this trick, any card may be led
        if not current_trick:
            return list(my_hand)

        first_card = current_trick[0][1]
        # If first card is a Wizard => no suit requirement
        if first_card.card_type == "wizard":
            return list(my_hand)

        # If first card is a Jester: the first standard card in the trick determines suit
        if first_card.card_type == "jester":
            suit_required = None
            for _, c in current_trick:
                if c.card_type == "standard":
                    suit_required = c.suit
                    break
            # If no standard card yet, no suit requirement
            if suit_required is None:
                return list(my_hand)
        else:
            suit_required = first_card.suit

        # Must follow suit if you have any standard cards in that suit.
        suit_cards = [c for c in my_hand if c.card_type == "standard" and c.suit == suit_required]
        if suit_cards:
            # Wizards and Jesters may always be played
            wilds = [c for c in my_hand if c.card_type in ("wizard", "jester")]
            return suit_cards + wilds
        else:
            return list(my_hand)

    def _trick_winner_index(self, cards_in_order, trump_suit):
        # cards_in_order: list of Card objects in play order
        # 1) If any Wizards: first Wizard wins
        for idx, c in enumerate(cards_in_order):
            if c.card_type == "wizard":
                return idx
        # 2) If all Jesters: first Jester wins
        if all(c.card_type == "jester" for c in cards_in_order):
            return 0
        # 3) Otherwise, determine the led suit (first standard card)
        first_standard_idx = next(i for i, c in enumerate(cards_in_order) if c.card_type == "standard")
        led_suit = cards_in_order[first_standard_idx].suit
        # 4) If any trump cards were played, highest trump wins
        if trump_suit is not None:
            trump_indices = [i for i, c in enumerate(cards_in_order) if c.card_type == "standard" and c.suit == trump_suit]
            if trump_indices:
                # choose the highest rank among trumps
                best = trump_indices[0]
                for i in trump_indices[1:]:
                    if cards_in_order[i].rank > cards_in_order[best].rank:
                        best = i
                return best
        # 5) Otherwise highest card in led suit wins
        candidates = [i for i, c in enumerate(cards_in_order) if c.card_type == "standard" and c.suit == led_suit]
        best = candidates[0]
        for i in candidates[1:]:
            if cards_in_order[i].rank > cards_in_order[best].rank:
                best = i
        return best

    def _would_win_if_played(self, current_trick, candidate_card, trump_suit):
        simulate = [c for _, c in current_trick] + [candidate_card]
        winner_idx = self._trick_winner_index(simulate, trump_suit)
        return winner_idx == (len(simulate) - 1)

    def _card_value(self, card, trump_suit):
        # Numeric value used for sorting/choosing cards.
        if card.card_type == "wizard":
            return 2000
        if card.card_type == "jester":
            return 0
        # standard card: prefer higher rank and trumps
        base = card.rank  # 2..14
        if trump_suit is not None and card.suit == trump_suit:
            base += 50
        return base

    def _lead_strength(self, card, trump_suit):
        # Strength when leading (higher => more likely to win the trick)
        if card.card_type == "wizard":
            return 3000
        if card.card_type == "jester":
            return 0
        s = card.rank
        if trump_suit is not None and card.suit == trump_suit:
            s += 100
        return s

    # ----------------- Bidding -----------------
    def _bid_estimate(self, game_state):
        my_hand = game_state["my_hand"]
        cards_this_round = game_state["cards_this_round"]
        trump = game_state["trump_suit"]

        # quick counts
        wizards = sum(1 for c in my_hand if c.card_type == "wizard")
        jesters = sum(1 for c in my_hand if c.card_type == "jester")
        standard_cards = [c for c in my_hand if c.card_type == "standard"]
        suits = {"Hearts": 0, "Diamonds": 0, "Clubs": 0, "Spades": 0}
        for c in standard_cards:
            suits[c.suit] += 1
        voids = sum(1 for v in suits.values() if v == 0)

        # weight cards to estimate number of tricks we can win
        weight = 0.0
        for c in my_hand:
            if c.card_type == "wizard":
                weight += 1.15
            elif c.card_type == "jester":
                weight += 0.0
            else:
                # standard
                r_norm = (c.rank - 2) / 12.0  # 0..1
                if trump is not None and c.suit == trump:
                    # trumps are significantly more valuable
                    weight += 0.9 * r_norm + 0.2
                else:
                    # non-trumps contribute less
                    weight += 0.5 * r_norm

        # voids give opportunities to trump when others lead those suits
        weight += 0.12 * voids

        # small-hand adjustment: single-card and two-card hands are more reliable,
        # so round more aggressively for small hands
        if cards_this_round <= 2:
            estimate = int(round(weight))
        else:
            estimate = int(round(weight))

        # floor to 0 and cap to cards_this_round
        estimate = max(0, min(cards_this_round, estimate))

        # if we have no likely winners (very low weight), prefer bidding 0 (safe)
        if weight < 0.25:
            estimate = 0

        return estimate

    def make_move(self, phase, game_state):
        phase = phase.lower()
        if game_state["round_number"] != self.last_round:
            # new round, reset per-round memory
            self._reset_for_round(game_state["round_number"])

        if phase == "bid":
            cards_this_round = game_state["cards_this_round"]
            # basic estimate
            estimate = self._bid_estimate(game_state)

            # handle hook rule for last bidder (player index 5)
            my_pos = game_state["my_position"]
            bids = list(game_state["bids"])  # copy
            if my_pos == 5:
                # sum of other bids
                other_sum = sum(b for i, b in enumerate(bids) if i != 5 and b is not None)
                banned = cards_this_round - other_sum
                # If our estimate equals banned, choose nearest valid bid
                if estimate == banned:
                    valid = [i for i in range(cards_this_round + 1) if i != banned]
                    # choose the valid bid closest to estimate (tie-break to smaller)
                    estimate = min(valid, key=lambda x: (abs(x - estimate), x))
            # ensure valid integer and within range
            estimate = int(max(0, min(cards_this_round, estimate)))
            self.my_last_bid = estimate
            return estimate

        elif phase == "play":
            my_hand = list(game_state["my_hand"])
            if not my_hand:
                return None

            # update seen cards with current trick cards
            current_trick = game_state["current_trick"]
            self._update_seen(current_trick)

            trump = game_state["trump_suit"]
            my_pos = game_state["my_position"]
            my_bid = game_state["bids"][my_pos]
            # If the game_state doesn't contain our bid for some reason, use stored
            if my_bid is None:
                my_bid = self.my_last_bid if self.my_last_bid is not None else 0
            tricks_won = game_state["tricks_won"][my_pos]
            need = my_bid - tricks_won  # how many more tricks we want to win this round
            remaining_tricks = game_state["cards_this_round"] - sum(game_state["tricks_won"])

            legal_cards = self._get_legal_cards(my_hand, current_trick, trump)

            # If only one legal card, must play it
            if len(legal_cards) == 1:
                chosen = legal_cards[0]
                # remember we've seen it (we played it)
                self.seen_cards.add(chosen)
                return chosen

            # If there is an active trick (not leading), check which legal plays would win
            if current_trick:
                winners = []
                losers = []
                for c in legal_cards:
                    if self._would_win_if_played(current_trick, c, trump):
                        winners.append(c)
                    else:
                        losers.append(c)

                # If we still need tricks, try to win this trick cheaply
                if need > 0:
                    if winners:
                        # pick cheapest winning card (lowest value) to conserve power
                        min_val = min(self._card_value(c, trump) for c in winners)
                        candidates = [c for c in winners if self._card_value(c, trump) == min_val]
                        chosen = random.choice(candidates)
                        self.seen_cards.add(chosen)
                        return chosen
                    else:
                        # cannot win this trick: throw away the least valuable card (prefer Jesters)
                        jesters = [c for c in legal_cards if c.card_type == "jester"]
                        if jesters:
                            chosen = random.choice(jesters)
                        else:
                            min_val = min(self._card_value(c, trump) for c in legal_cards)
                            cands = [c for c in legal_cards if self._card_value(c, trump) == min_val]
                            chosen = random.choice(cands)
                        self.seen_cards.add(chosen)
                        return chosen
                else:
                    # need <= 0: avoid winning. Play a losing card if possible (prefer Jesters)
                    if losers:
                        jesters = [c for c in losers if c.card_type == "jester"]
                        if jesters:
                            chosen = random.choice(jesters)
                        else:
                            # discard the most "dangerous" losing card (highest value) to reduce future wins
                            max_val = max(self._card_value(c, trump) for c in losers)
                            cands = [c for c in losers if self._card_value(c, trump) == max_val]
                            chosen = random.choice(cands)
                        self.seen_cards.add(chosen)
                        return chosen
                    else:
                        # all legal cards would win — pick the cheapest winner to minimize overtrick damage
                        min_val = min(self._card_value(c, trump) for c in winners)
                        cands = [c for c in winners if self._card_value(c, trump) == min_val]
                        chosen = random.choice(cands)
                        self.seen_cards.add(chosen)
                        return chosen

            else:
                # We are leading the trick: no cards played yet
                if need > 0:
                    # attempt to lead something likely to win
                    # choose the card with maximum lead_strength, but prefer to avoid spending a Wizard if a strong trump/non-wizard will suffice
                    best = max(legal_cards, key=lambda c: self._lead_strength(c, trump))
                    if best.card_type == "wizard":
                        # check if a non-wizard is almost as strong; if so, play that to save the wizard
                        non_wizards = [c for c in legal_cards if c.card_type != "wizard"]
                        if non_wizards:
                            alt = max(non_wizards, key=lambda c: self._lead_strength(c, trump))
                            # if alt has at least 80% of strength, prefer alt
                            if self._lead_strength(alt, trump) >= 0.8 * self._lead_strength(best, trump):
                                chosen = alt
                            else:
                                chosen = best
                        else:
                            chosen = best
                    else:
                        chosen = best
                    self.seen_cards.add(chosen)
                    return chosen
                else:
                    # need <= 0: lead a throwaway (prefer Jester), otherwise lowest strength
                    jesters = [c for c in legal_cards if c.card_type == "jester"]
                    if jesters:
                        chosen = random.choice(jesters)
                    else:
                        min_strength = min(self._lead_strength(c, trump) for c in legal_cards)
                        cands = [c for c in legal_cards if self._lead_strength(c, trump) == min_strength]
                        chosen = random.choice(cands)
                    self.seen_cards.add(chosen)
                    return chosen

        else:
            # Unknown phase: fallback
            return None
