"""
Agent Code: A4-WordFinder
Model: qwen/qwen3.5-plus-02-15
Run: 2
Generated: 2026-02-16 18:36:51
"""

import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.internal_index = {}
        self._build_index()

    def _build_index(self):
        """
        Pre-compute an index mapping characters to sets of words that contain 
        that character internally (not at start or end).
        """
        for word in self.dictionary:
            if len(word) < 3:
                continue
            
            start_c = word[0]
            end_c = word[-1]
            
            # Identify unique internal characters
            internal_chars = set(word[1:-1])
            for char in internal_chars:
                # The character must not be at the start or end of THIS word
                # to satisfy the position constraint for that required letter.
                if char != start_c and char != end_c:
                    if char not in self.internal_index:
                        self.internal_index[char] = set()
                    self.internal_index[char].add(word)

    def _calculate_score(self, word, req_start, req_end):
        """
        Calculate the potential score for a move based on game rules.
        """
        length = len(word)
        base = length
        
        # Hyphen Penalty
        if '-' in word:
            base = base // 2
            
        # Consecutive Letter Bonus
        pair1 = req_start + req_end
        pair2 = req_end + req_start
        
        if pair1 in word or pair2 in word:
            base *= 2
            
        return base

    def make_move(self, current_word, word_history):
        req_start = current_word[0]
        req_end = current_word[-1]
        current_len = len(current_word)
        
        set_start = self.internal_index.get(req_start, set())
        set_end = self.internal_index.get(req_end, set())
        
        # 1. Try Valid Moves (Both required letters present internally)
        candidates = set_start & set_end
        
        best_word = None
        best_score = -1
        
        for word in candidates:
            if word in word_history:
                continue
            if len(word) == current_len:
                continue
            
            score = self._calculate_score(word, req_start, req_end)
            if score > best_score:
                best_score = score
                best_word = word
            elif score == best_score and best_word is not None:
                # Random tie-breaker for unpredictability
                if random.random() > 0.5:
                    best_word = word
        
        if best_word:
            return best_word
            
        # 2. Try Partial Moves (Only one required letter present internally)
        # This incurs a penalty, so we minimize word length to minimize loss.
        partial_candidates = set_start | set_end
        
        best_partial = None
        min_len = float('inf')
        
        for word in partial_candidates:
            if word in word_history:
                continue
            if len(word) == current_len:
                continue
            
            if len(word) < min_len:
                min_len = len(word)
                best_partial = word
            elif len(word) == min_len and best_partial is not None:
                if random.random() > 0.5:
                    best_partial = word
                    
        if best_partial:
            return best_partial
            
        # 3. Fallback (Avoid Invalid Move penalty if possible)
        # Try to find ANY word not in history to keep the game going.
        for word in self.dictionary:
            if word not in word_history:
                return word
                
        return "a"