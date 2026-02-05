"""
Agent Code: A4-WordFinder
Model: x-ai/grok-4.1-fast
Run: 3
Generated: 2026-02-05 21:09:40
"""

from collections import defaultdict

from collections import defaultdict
import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.pair_candidates = defaultdict(list)
        self.letter_candidates = defaultdict(list)
        self.length_to_words = defaultdict(list)

        for word in self.dictionary:
            wlen = len(word)
            if wlen < 2:
                continue
            self.length_to_words[wlen].append(word)

            if wlen < 3:
                continue

            contains = set(word)
            start_let = word[0]
            end_let = word[-1]
            has_hyphen = '-' in word

            # For full pairs (A, B)
            for A in contains:
                for B in contains:
                    forbidden = {A, B}
                    if start_let in forbidden or end_let in forbidden:
                        continue
                    ab = A + B
                    ba = B + A
                    has_bonus = ab in word or ba in word
                    multiplier = 2 if has_bonus else 1
                    base = wlen if not has_hyphen else wlen / 2.0
                    score = base * multiplier
                    self.pair_candidates[(A, B)].append((score, wlen, word))

            # For partials (single C)
            for C in contains:
                if start_let == C or end_let == C:
                    continue
                self.letter_candidates[C].append((wlen, word))

        # Sort pair candidates: desc score, desc length
        for pair in list(self.pair_candidates.keys()):
            self.pair_candidates[pair] = sorted(
                self.pair_candidates[pair],
                key=lambda t: (t[0], t[1]),
                reverse=True
            )

        # Sort letter candidates: asc length
        for C in list(self.letter_candidates.keys()):
            self.letter_candidates[C] = sorted(self.letter_candidates[C], key=lambda t: t[0])

    def make_move(self, current_word, word_history):
        A = current_word[0]
        B = current_word[-1]
        prev_len = len(current_word)
        pair = (A, B)

        # Try full valid move
        cands = self.pair_candidates.get(pair, [])
        for score, wlen, word in cands:
            if wlen != prev_len and word not in word_history:
                return word

        # Try partial move
        partial_words = []
        reqs = set([A, B])
        for req in reqs:
            other = B if req == A else A
            cands = self.letter_candidates.get(req, [])
            for wlen, word in cands:
                if wlen != prev_len and word not in word_history and other not in word:
                    partial_words.append(word)
                    break  # shortest for this req

        if partial_words:
            partial_words.sort(key=len)
            return partial_words[0]

        # Ultimate fallback: shortest unused word != prev_len
        for l in range(2, 31):
            if l == prev_len:
                continue
            for word in self.length_to_words[l]:
                if word not in word_history:
                    return word

        # Impossible case
        return ""
