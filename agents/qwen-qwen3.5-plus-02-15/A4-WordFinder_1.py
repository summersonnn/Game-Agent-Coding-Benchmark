"""
Agent Code: A4-WordFinder
Model: qwen/qwen3.5-plus-02-15
Run: 1
Generated: 2026-02-16 18:36:51
"""

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Pre-compute word groupings for faster lookup
        self.words_by_length = defaultdict(list)
        
        # Build lookup structures
        for word in self.dictionary:
            if len(word) < 2:
                continue
            self.words_by_length[len(word)].append(word)
        
        # Sort words by length (descending) within each length group
        for length in self.words_by_length:
            self.words_by_length[length].sort(reverse=True)
        
        # Cache for quick access to sorted lengths
        self.sorted_lengths = sorted(self.words_by_length.keys(), reverse=True)
    
    def make_move(self, current_word, word_history):
        """
        Find the best valid word based on current_word constraints.
        """
        if len(current_word) < 2:
            return self._find_any_valid_word(word_history)
        
        required_first = current_word[0].lower()
        required_last = current_word[-1].lower()
        current_length = len(current_word)
        
        # Strategy priorities:
        # 1. Words with consecutive letter bonus (2x multiplier)
        # 2. Longest words without bonus
        # 3. Avoid hyphens when possible
        
        best_word = None
        best_score = -float('inf')
        best_has_bonus = False
        
        # Search through words, prioritizing longer words
        for length in self.sorted_lengths:
            if length == current_length:
                continue
            
            for word in self.words_by_length[length]:
                if word in word_history:
                    continue
                
                # Check position constraints
                if word[0] in (required_first, required_last):
                    continue
                if word[-1] in (required_first, required_last):
                    continue
                
                # Check if word contains both required letters in middle
                middle = word[1:-1]
                has_first = required_first in middle
                has_last = required_last in middle
                
                if has_first and has_last:
                    has_bonus = self._has_consecutive_bonus(word, required_first, required_last)
                    score = self._calculate_score(word, has_bonus)
                    
                    # Prioritize words with bonus
                    if has_bonus and not best_has_bonus:
                        best_word = word
                        best_score = score
                        best_has_bonus = True
                    elif has_bonus == best_has_bonus and score > best_score:
                        best_word = word
                        best_score = score
                    
                    # If we found a long word with bonus, it's likely optimal
                    if has_bonus and length >= 10:
                        return best_word
        
        if best_word:
            return best_word
        
        # Fallback: partial move (only one required letter)
        return self._find_partial_move(current_word, word_history)
    
    def _calculate_score(self, word, has_bonus):
        """Calculate the score for a word."""
        length = len(word)
        
        # Hyphen penalty
        if '-' in word:
            base_points = length / 2
        else:
            base_points = length
        
        # Consecutive letter bonus
        if has_bonus:
            base_points *= 2
        
        return base_points
    
    def _has_consecutive_bonus(self, word, req_first, req_last):
        """Check if word has consecutive required letters."""
        middle = word[1:-1]
        return (req_first + req_last in middle) or (req_last + req_first in middle)
    
    def _find_partial_move(self, current_word, word_history):
        """Find a word with only one required letter (fallback)."""
        required_first = current_word[0].lower()
        required_last = current_word[-1].lower()
        current_length = len(current_word)
        
        for length in self.sorted_lengths:
            if length == current_length:
                continue
            
            for word in self.words_by_length[length]:
                if word in word_history:
                    continue
                
                if word[0] in (required_first, required_last):
                    continue
                if word[-1] in (required_first, required_last):
                    continue
                
                middle = word[1:-1]
                has_first = required_first in middle
                has_last = required_last in middle
                
                if (has_first and not has_last) or (has_last and not has_first):
                    return word
        
        return self._find_any_valid_word(word_history)
    
    def _find_any_valid_word(self, word_history):
        """Find any word not in history."""
        for word in self.dictionary:
            if word not in word_history and len(word) >= 2:
                return word
        return "the"