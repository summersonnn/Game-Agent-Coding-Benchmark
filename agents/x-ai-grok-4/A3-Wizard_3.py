"""
Agent Code: A3-Wizard
Model: x-ai/grok-4
Run: 3
Generated: 2026-02-04 16:50:03
"""



class WizardAgent:
    def __init__(self, name):
        self.name = name

    def get_hand_info(self, hand, trump):
        wizards = 0
        jesters = 0
        trump_ranks = []
        non_trump = {s: [] for s in ['Hearts', 'Diamonds', 'Clubs', 'Spades']}
        for c in hand:
            if c.card_type == 'wizard':
                wizards += 1
            elif c.card_type == 'jester':
                jesters += 1
            else:
                if c.suit == trump:
                    trump_ranks.append(c.rank)
                else:
                    non_trump[c.suit].append(c.rank)
        trump_ranks.sort(reverse=True)
        for ranks in non_trump.values():
            ranks.sort(reverse=True)
        return wizards, jesters, trump_ranks, non_trump

    def get_led_suit(self, current_trick):
        if not current_trick:
            return None
        first_card = current_trick[0][1]
        if first_card.card_type == 'wizard':
            return None
        if first_card.card_type == 'jester':
            for _, card in current_trick:
                if card.card_type == 'standard':
                    return card.suit
            return None
        return first_card.suit

    def get_legal_cards(self, hand, led_suit):
        if led_suit is None:
            return list(hand)
        has_suit = any(c.card_type == 'standard' and c.suit == led_suit for c in hand)
        legal = []
        for c in hand:
            if c.card_type == 'wizard' or c.card_type == 'jester':
                legal.append(c)
            elif c.card_type == 'standard' and c.suit == led_suit:
                legal.append(c)
        if not has_suit:
            legal = list(hand)
        return legal

    def determine_winner(self, played_cards, trump):
        cards = [c for _, c in played_cards]
        player_idxs = [p for p, c in played_cards]
        wizard_indices = [i for i, c in enumerate(cards) if c.card_type == 'wizard']
        if wizard_indices:
            return player_idxs[wizard_indices[0]]
        if all(c.card_type == 'jester' for c in cards):
            return player_idxs[0]
        led_suit = None
        for c in cards:
            if c.card_type == 'standard':
                led_suit = c.suit
                break
        trumps = [(i, c.rank) for i, c in enumerate(cards) if c.card_type == 'standard' and c.suit == trump]
        if trumps:
            max_i = max(trumps, key=lambda x: x[1])[0]
            return player_idxs[max_i]
        else:
            suit_cards = [(i, c.rank) for i, c in enumerate(cards) if c.card_type == 'standard' and c.suit == led_suit]
            max_i = max(suit_cards, key=lambda x: x[1])[0]
            return player_idxs[max_i]

    def card_strength_key(self, card, trump, led_suit):
        if card.card_type == 'wizard':
            return (3, 15, 0)
        if card.card_type == 'jester':
            return (0, 0, 0)
        rank = card.rank if card.rank else 0
        if trump and card.suit == trump:
            return (2, rank, 0)
        if led_suit and card.suit == led_suit:
            return (1, rank, 0)
        return (0, rank, 0)

    def min_card(self, cards, trump, led_suit):
        if not cards:
            return None
        return min(cards, key=lambda c: self.card_strength_key(c, trump, led_suit))

    def max_card(self, cards, trump, led_suit):
        if not cards:
            return None
        return max(cards, key=lambda c: self.card_strength_key(c, trump, led_suit))

    def make_move(self, phase, game_state):
        if phase == "bid":
            round_num = game_state["cards_this_round"]
            trump = game_state["trump_suit"]
            hand = game_state["my_hand"]
            wizards, jesters, trump_ranks, non_trump = self.get_hand_info(hand, trump)
            expected = float(wizards)
            if trump:
                for i, r in enumerate(trump_ranks):
                    value = (r - 1) / 13.0
                    multiplier = 1 - (i / len(trump_ranks)) if len(trump_ranks) > 0 else 1
                    expected += value * multiplier
            else:
                for suit, ranks in non_trump.items():
                    for i, r in enumerate(ranks):
                        value = (r - 1) / 13.0
                        expected += value * 0.8
            bid = int(round(expected))
            bid = max(0, min(bid, round_num))
            bids = game_state["bids"]
            num_bid = sum(1 for b in bids if b is not None)
            if num_bid == 5:
                current_sum = sum(b for b in bids if b is not None)
                forbidden = round_num - current_sum
                if bid == forbidden:
                    if bid > expected and bid > 0:
                        bid -= 1
                    elif bid + 1 <= round_num:
                        bid += 1
                    else:
                        bid -= 1
                    bid = max(0, min(bid, round_num))
            return bid
        elif phase == "play":
            hand = game_state["my_hand"]
            if not hand:
                return None
            trump = game_state["trump_suit"]
            current_trick = game_state["current_trick"]
            my_pos = game_state["my_position"]
            led_suit = self.get_led_suit(current_trick)
            legal = self.get_legal_cards(hand, led_suit)
            my_bid = game_state["bids"][my_pos]
            current_won = game_state["tricks_won"][my_pos]
            total_tricks = game_state["cards_this_round"]
            tricks_completed = sum(game_state["tricks_won"])
            remaining = total_tricks - tricks_completed
            needed = my_bid - current_won
            should_try_win = (needed > remaining - 1)
            if len(current_trick) == 5:
                winning_cards = []
                losing_cards = []
                for card in legal:
                    played = current_trick + [(my_pos, card)]
                    if self.determine_winner(played, trump) == my_pos:
                        winning_cards.append(card)
                    else:
                        losing_cards.append(card)
                if should_try_win:
                    if winning_cards:
                        return self.min_card(winning_cards, trump, led_suit)
                    else:
                        return self.min_card(legal, trump, led_suit)
                else:
                    if losing_cards:
                        return self.max_card(losing_cards, trump, led_suit)
                    else:
                        return self.min_card(legal, trump, led_suit)
            else:
                has_wizard = any(c.card_type == 'wizard' for _, c in current_trick)
                wizards_in_hand = [c for c in legal if c.card_type == 'wizard']
                jesters_in_hand = [c for c in legal if c.card_type == 'jester']
                if should_try_win:
                    if has_wizard:
                        return self.min_card(legal, trump, led_suit)
                    else:
                        if wizards_in_hand:
                            return wizards_in_hand[0]
                        else:
                            return self.max_card(legal, trump, led_suit)
                else:
                    if has_wizard:
                        return self.max_card(legal, trump, led_suit)
                    else:
                        if jesters_in_hand:
                            return jesters_in_hand[0]
                        else:
                            return self.min_card(legal, trump, led_suit)
