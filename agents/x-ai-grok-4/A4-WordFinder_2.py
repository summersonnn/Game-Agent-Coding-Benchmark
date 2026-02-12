"""
Agent Code: A4-WordFinder
Model: x-ai-grok-4
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.words_for_pair = defaultdict(list)
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        for req1 in alphabet:
            for req2 in alphabet:
                for w in self.dictionary:
                    if req1 in w and req2 in w:
                        if w[0] not in {req1, req2} and w[-1] not in {req1, req2}:
                            self.words_for_pair[(req1, req2)].append(w)

    def compute_score(self, w, req1, req2):
        base = len(w)
        if '-' in w:
            base //= 2
        consec = (req1 + req2 in w) or (req2 + req1 in w)
        if consec:
            base *= 2
        return base

    def make_move(self, current_word, word_history):
        req1 = current_word[0]
        req2 = current_word[-1]
        len_curr = len(current_word)
        candidates = [w for w in self.words_for_pair[(req1, req2)] if w not in word_history and len(w) != len_curr]
        if candidates:
            candidates.sort(key=lambda w: (-self.compute_score(w, req1, req2), len(self.words_for_pair[(w[0], w[-1])])))
            return candidates[0]
        
        # Partial move
        candidates_partial = []
        for w in self.dictionary:
            if w in word_history:
                continue
            if len(w) == len_curr:
                continue
            contains1 = req1 in w
            contains2 = req2 in w
            if contains1 == contains2:
                continue
            if contains1:
                if w[0] == req1 or w[-1] == req1:
                    continue
            else:
                if w[0] == req2 or w[-1] == req2:
                    continue
            candidates_partial.append(w)
        
        if candidates_partial:
            candidates_partial.sort(key=lambda w: (len(w), len(self.words_for_pair[(w[0], w[-1])])))
            return candidates_partial[0]
        
        # Fallback if nothing
        fallback = [w for w in self.dictionary if w not in word_history and len(w) != len_curr]
        if fallback:
            fallback.sort(key=len)
            return fallback[0]
        
        # Should not reach here
        return "example"