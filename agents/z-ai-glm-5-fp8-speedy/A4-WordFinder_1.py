"""
Agent Code: A4-WordFinder
Model: z-ai/glm-5@preset/fp8
Run: 1
Generated: 2026-02-12 09:24:15
"""


import random


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Pre-compute indices for fast lookup
        self.words_with_letter = {}  # letter -> set of words containing it
        self.consecutive_pairs = {}  # (letter1, letter2) -> set of words with them consecutively
        
        for word in self.dictionary:
            # Index by unique letters in word
            for letter in set(word):
                if letter not in self.words_with_letter:
                    self.words_with_letter[letter] = set()
                self.words_with_letter[letter].add(word)
            
            # Index by consecutive letter pairs
            for i in range(len(word) - 1):
                pair = (word[i], word[i+1])
                if pair not in self.consecutive_pairs:
                    self.consecutive_pairs[pair] = set()
                self.consecutive_pairs[pair].add(word)
    
    def make_move(self, current_word, word_history):
        current_word = current_word.lower()
        req1, req2 = current_word[0], current_word[-1]
        curr_len = len(current_word)
        
        # Check if both letters exist in dictionary
        if req1 not in self.words_with_letter or req2 not in self.words_with_letter:
            return self._partial_move(req1, req2, word_history, curr_len)
        
        set1 = self.words_with_letter[req1]
        set2 = self.words_with_letter[req2]
        
        # First try bonus words (consecutive letters = 2x multiplier)
        bonus_candidates = (self.consecutive_pairs.get((req1, req2), set()) | 
                           self.consecutive_pairs.get((req2, req1), set()))
        best = self._find_best_word(bonus_candidates, word_history, curr_len, req1, req2, is_bonus=True)
        if best:
            return best
        
        # Then try regular words
        all_candidates = set1 & set2
        regular_candidates = all_candidates - bonus_candidates
        best = self._find_best_word(regular_candidates, word_history, curr_len, req1, req2, is_bonus=False)
        if best:
            return best
        
        # No valid word found - attempt partial move
        return self._partial_move(req1, req2, word_history, curr_len)
    
    def _find_best_word(self, candidates, word_history, curr_len, req1, req2, is_bonus):
        """Find the highest-scoring valid word from candidates."""
        best_word = None
        best_score = -1
        
        for word in candidates:
            if word in word_history:
                continue
            if len(word) == curr_len:
                continue
            if word[0] in (req1, req2) or word[-1] in (req1, req2):
                continue
            
            # Calculate score
            score = len(word)
            if '-' in word:
                score = score // 2  # Hyphen penalty
            if is_bonus:
                score *= 2  # Consecutive letter bonus
            
            if score > best_score:
                best_score = score
                best_word = word
        
        return best_word
    
    def _partial_move(self, req1, req2, word_history, curr_len):
        """Find a word containing at least one required letter (last resort)."""
        best_word = None
        best_len = float('inf')
        
        # Try each required letter
        for letter in [req1, req2]:
            if letter not in self.words_with_letter:
                continue
            for word in self.words_with_letter[letter]:
                if word in word_history:
                    continue
                if len(word) == curr_len:
                    continue
                if word[0] == letter or word[-1] == letter:
                    continue
                # Prefer shortest word to minimize penalty
                if len(word) < best_len:
                    best_len = len(word)
                    best_word = word
        
        if best_word:
            return best_word
        
        # Absolute fallback: any unused word
        for word in self.dictionary:
            if word not in word_history:
                return word
        
        return "a"  # Emergency fallback