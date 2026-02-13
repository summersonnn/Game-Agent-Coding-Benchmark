"""
Agent Code: A4-WordFinder
Model: anthropic-claude-sonnet-4.5
Run: 2
Generated: 2026-02-12 09:24:15
"""


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Pre-compute index: letter pairs -> words containing them
        self.pair_index = {}
        for word in self.dictionary:
            chars = set(word)
            for c1 in chars:
                for c2 in chars:
                    if c1 <= c2:
                        key = (c1, c2) if c1 != c2 else (c1,)
                        if key not in self.pair_index:
                            self.pair_index[key] = []
                        if word not in self.pair_index[key]:
                            self.pair_index[key].append(word)
    
    def make_move(self, current_word, word_history):
        req_first = current_word[0].lower()
        req_last = current_word[-1].lower()
        prev_len = len(current_word)
        
        # Get candidate words
        if req_first == req_last:
            key = (req_first,)
        else:
            key = tuple(sorted([req_first, req_last]))
        
        candidates = self.pair_index.get(key, [])
        
        # Filter valid words
        valid = []
        for word in candidates:
            if word in word_history or len(word) == prev_len:
                continue
            if word[0] in [req_first, req_last] or word[-1] in [req_first, req_last]:
                continue
            valid.append(word)
        
        if not valid:
            return self._partial_move(req_first, req_last, prev_len, word_history)
        
        # Score and select best
        best_word = max(valid, key=lambda w: self._score(w, req_first, req_last))
        return best_word
    
    def _score(self, word, req_first, req_last):
        score = len(word)
        
        if '-' in word:
            score /= 2
        
        # Check for consecutive letters (2x bonus)
        for i in range(len(word) - 1):
            pair = word[i:i+2]
            if pair in [req_first + req_last, req_last + req_first]:
                score *= 2
                break
        
        return score
    
    def _partial_move(self, req_first, req_last, prev_len, word_history):
        # Last resort: word with one required letter
        for word in self.dictionary:
            if word in word_history or len(word) == prev_len:
                continue
            if word[0] in [req_first, req_last] or word[-1] in [req_first, req_last]:
                continue
            if req_first in word or req_last in word:
                return word
        
        # Ultimate fallback
        for word in self.dictionary:
            if word not in word_history and len(word) != prev_len:
                return word
        
        return list(self.dictionary)[0]