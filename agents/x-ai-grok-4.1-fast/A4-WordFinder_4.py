"""
Agent Code: A4-WordFinder
Model: x-ai/grok-4.1-fast
Run: 4
Generated: 2026-02-05 21:09:40
"""

from collections import defaultdict

from collections import defaultdict
import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.pair_to_candidates = defaultdict(list)
        self.single_to_candidates = defaultdict(list)
        for word in self.dictionary:
            if len(word) < 3:
                continue
            first = word[0]
            last = word[-1]
            middle = word[1:-1]
            middle_set = set(middle)
            possible_cs = middle_set - {first, last}
            for c1 in possible_cs:
                for c2 in possible_cs:
                    self.pair_to_candidates[(c1, c2)].append(word)
            for c in possible_cs:
                self.single_to_candidates[c].append(word)
        
        self.pair_sizes = {pair: len(cands) for pair, cands in self.pair_to_candidates.items()}
        
        self.pair_to_scored = {}
        for pair, cands in self.pair_to_candidates.items():
            c1, c2 = pair
            scored = []
            for word in cands:
                wlen = len(word)
                has_hyphen = '-' in word
                base = wlen if not has_hyphen else wlen / 2.0
                bonus = (c1 + c2 in word) or (c2 + c1 in word)
                score = base * (2 if bonus else 1)
                opp_pair = (word[0], word[-1])
                hardness = -self.pair_sizes.get(opp_pair, 0)
                scored.append((score, hardness, wlen, word))
            scored.sort(reverse=True)
            self.pair_to_scored[pair] = scored
        
        self.single_to_scored = {}
        for c, cands in self.single_to_candidates.items():
            scored = []
            for word in cands:
                wlen = len(word)
                opp_pair = (word[0], word[-1])
                hardness = -self.pair_sizes.get(opp_pair, 0)
                scored.append((wlen, -hardness, word))
            scored.sort()
            self.single_to_scored[c] = scored

    def make_move(self, current_word, word_history):
        req1 = current_word[0]
        req2 = current_word[-1]
        prev_len = len(current_word)
        pair = (req1, req2)
        candidates = self.pair_to_scored.get(pair, [])
        for score, hardness, wlen, word in candidates:
            if word in word_history:
                continue
            if wlen == prev_len:
                continue
            return word
        
        # Partial move: try req1 first
        partial_cands1 = self.single_to_scored.get(req1, [])
        for wlen, neg_hardness, word in partial_cands1:
            if word in word_history:
                continue
            if wlen == prev_len:
                continue
            if req2 in word:
                continue
            return word
        
        # Then req2
        partial_cands2 = self.single_to_scored.get(req2, [])
        for wlen, neg_hardness, word in partial_cands2:
            if word in word_history:
                continue
            if wlen == prev_len:
                continue
            if req1 in word:
                continue
            return word
        
        # If no valid move, return a dummy (will lose, but unavoidable)
        return ""
