"""
Agent Code: A4-WordFinder
Model: x-ai/grok-code-fast-1
Run: 2
Generated: 2026-02-12 09:24:15
"""

import collections

import random
import collections

class WordFinderAgent:
    """
    WordFinder agent that precomputes valid words for pairs and singles,
    then selects moves to maximize score or minimize penalty.
    """
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Precompute for pairs: key is frozenset({a, b}), value is list of (word, length, has_hyphen, consecutive_type)
        # consecutive_type: 0=none, 1=ab, 2=ba (where a < b)
        self.pair_to_words = collections.defaultdict(list)
        # Precompute for singles: key is letter, value is list of (word, length, has_hyphen)
        self.single_to_words = collections.defaultdict(list)
        
        for word in self.dictionary:
            if not word:
                continue
            length = len(word)
            has_hyphen = '-' in word
            first = word[0]
            last = word[-1]
            letters = set(word)
            # For pairs
            for a in letters:
                for b in letters:
                    if a != b and a < b:  # to avoid duplicates, assume a < b
                        key = frozenset({a, b})
                        consecutive = 0
                        if a + b in word:
                            consecutive = 1  # ab
                        elif b + a in word:
                            consecutive = 2  # ba
                        # Check if a and b are not at start or end
                        if a != first and a != last and b != first and b != last:
                            self.pair_to_words[key].append((word, length, has_hyphen, consecutive))
            # For singles
            for letter in letters:
                if letter != first and letter != last:
                    self.single_to_words[letter].append((word, length, has_hyphen))

    def make_move(self, current_word, word_history):
        current_word = current_word.lower()
        req1 = current_word[0]
        req2 = current_word[-1]
        curr_len = len(current_word)
        key = frozenset({req1, req2})
        candidates = self.pair_to_words.get(key, [])
        
        best_word = None
        best_score = -float('inf')
        
        for word, length, has_hyphen, consec in candidates:
            if length == curr_len or word in word_history:
                continue
            base = length
            if has_hyphen:
                base /= 2.0
            if consec > 0:
                base *= 2
            if base > best_score:
                best_score = base
                best_word = word
        
        if best_word:
            return best_word
        
        # No full move, try partial
        # For req1
        partial1 = self._find_partial(req1, curr_len, word_history)
        # For req2
        partial2 = self._find_partial(req2, curr_len, word_history)
        
        if partial1 and partial2:
            # Choose the one with smaller penalty (shorter length)
            if partial1[1] <= partial2[1]:
                return partial1[0]
            else:
                return partial2[0]
        elif partial1:
            return partial1[0]
        elif partial2:
            return partial2[0]
        else:
            # Fallback, though unlikely; return a dummy invalid to trigger penalty
            return "invalid"

    def _find_partial(self, req, curr_len, word_history):
        candidates = self.single_to_words.get(req, [])
        best_word = None
        best_len = float('inf')
        for word, length, has_hyphen in candidates:
            if length == curr_len or word in word_history:
                continue
            if length < best_len:
                best_len = length
                best_word = word
        return (best_word, best_len) if best_word else None
