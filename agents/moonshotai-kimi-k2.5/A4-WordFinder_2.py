"""
Agent Code: A4-WordFinder
Model: moonshotai/kimi-k2.5
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

import random
from collections import defaultdict


class WordFinderAgent:
    """
    WordFinder agent that pre-computes letter indices for fast move generation.
    Strategy: Maximize score by finding longest words with consecutive letter bonuses,
    falling back to partial moves (shortest word) when necessary.
    """
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Precompute indices for fast lookup
        # Words containing a specific letter in interior positions (not first/last)
        self.by_letter_interior = defaultdict(set)
        # Words containing consecutive letter pairs in interior
        self.consecutive = defaultdict(set)
        
        for word in self.dictionary:
            n = len(word)
            if n < 3:
                continue
                
            interior = word[1:-1]
            
            # Index by unique interior letters
            unique_chars = set(interior)
            for ch in unique_chars:
                self.by_letter_interior[ch].add(word)
            
            # Index consecutive pairs in interior
            for i in range(len(interior) - 1):
                pair = (interior[i], interior[i+1])
                self.consecutive[pair].add(word)
    
    def _is_valid_placement(self, word, fc, lc):
        """Check that fc and lc are not at the boundaries of word."""
        if word[0] in (fc, lc) or word[-1] in (fc, lc):
            return False
        return True
    
    def _calculate_score(self, word, has_consecutive, target_len):
        """Calculate points for a word."""
        if len(word) == target_len:
            return -9999  # Invalid due to length constraint
            
        base = len(word)
        if '-' in word:
            base = base // 2
        
        if has_consecutive:
            base *= 2
            
        return base
    
    def _get_difficulty_bonus(self, word):
        """Tie-breaker: prefer words leaving rare letters for opponent."""
        rarity = {'q': 10, 'z': 9, 'x': 8, 'j': 7, 'k': 6, 
                  'v': 3, 'w': 3, 'y': 2, 'f': 2, 'h': 1}
        return rarity.get(word[0], 0) + rarity.get(word[-1], 0)
    
    def make_move(self, current_word, word_history):
        fc = current_word[0]
        lc = current_word[-1]
        curr_len = len(current_word)
        
        # Get base candidate sets
        set_fc = self.by_letter_interior.get(fc, set())
        set_lc = self.by_letter_interior.get(lc, set())
        
        # Full move candidates: words containing both letters in interior
        candidates_both = set_fc & set_lc
        
        # Consecutive bonus candidates: "fc-lc" or "lc-fc" appearing consecutively
        bonus_candidates = self.consecutive.get((fc, lc), set()) | self.consecutive.get((lc, fc), set())
        
        best_word = None
        best_score = -float('inf')
        best_difficulty = -1
        
        # Evaluate bonus candidates first (higher scoring potential)
        for word in bonus_candidates:
            if word in word_history or len(word) == curr_len:
                continue
            if not self._is_valid_placement(word, fc, lc):
                continue
                
            score = self._calculate_score(word, True, curr_len)
            diff = self._get_difficulty_bonus(word)
            
            if score > best_score or (score == best_score and diff > best_difficulty):
                best_score = score
                best_word = word
                best_difficulty = diff
        
        # Evaluate non-bonus candidates
        regular_candidates = candidates_both - bonus_candidates
        for word in regular_candidates:
            if word in word_history or len(word) == curr_len:
                continue
            if not self._is_valid_placement(word, fc, lc):
                continue
                
            score = self._calculate_score(word, False, curr_len)
            diff = self._get_difficulty_bonus(word)
            
            if score > best_score or (score == best_score and diff > best_difficulty):
                best_score = score
                best_word = word
                best_difficulty = diff
        
        if best_word:
            return best_word
        
        # Partial move fallback: words containing exactly one required letter
        # Use symmetric difference to get words with exactly one of the two letters
        partial_candidates = set_fc.symmetric_difference(set_lc)
        
        best_partial = None
        best_partial_len = float('inf')
        
        for word in partial_candidates:
            if word in word_history or len(word) == curr_len:
                continue
            if not self._is_valid_placement(word, fc, lc):
                continue
                
            # Valid partial move: contains exactly one (verified by symmetric difference)
            # Choose shortest to minimize penalty
            wlen = len(word)
            if wlen < best_partial_len:
                best_partial_len = wlen
                best_partial = word
        
        if best_partial:
            return best_partial
        
        # Desperate fallback: find any usable word not in history with different length
        # This will likely be invalid but avoids a crash
        for word in self.dictionary:
            if word not in word_history and len(word) != curr_len and len(word) >= 3:
                # Verify it doesn't violate boundaries with current required letters
                if word[0] not in (fc, lc) and word[-1] not in (fc, lc):
                    return word
        
        # Ultimate fallback
        return list(self.dictionary)[0] if self.dictionary else "error"
