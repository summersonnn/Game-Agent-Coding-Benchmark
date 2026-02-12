"""
Agent Code: A4-WordFinder
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self._precompute_indexes()
    
    def _precompute_indexes(self):
        """Precompute data structures for fast word lookup during gameplay."""
        self.letter_non_start_end_index = defaultdict(set)
        self.letter_any_index = defaultdict(set)
        self.word_info = {}
        
        for word in self.dictionary:
            if len(word) < 3:
                continue  # Skip words too short to have middle letters
                
            length = len(word)
            non_start_end_letters = set(word[1:-1])
            first = word[0]
            last = word[-1]
            has_hyphen = '-' in word
            
            self.word_info[word] = (length, non_start_end_letters, first, last, has_hyphen)
            
            # Index letters that appear in non-start/end positions
            for letter in non_start_end_letters:
                self.letter_non_start_end_index[letter].add(word)
            
            # Index all letters that appear anywhere in the word
            for letter in set(word):
                self.letter_any_index[letter].add(word)
    
    def make_move(self, current_word, word_history):
        a = current_word[0]
        b = current_word[-1]
        current_len = len(current_word)
        
        # Step 1: Find valid moves (contain both required letters in middle)
        valid_candidates = self._find_valid_candidates(a, b, current_len, word_history)
        if valid_candidates:
            return self._select_best_valid(valid_candidates, a, b)
        
        # Step 2: Find partial moves (contain exactly one required letter in middle)
        partial_candidates = self._find_partial_candidates(a, b, current_len, word_history)
        if partial_candidates:
            return self._select_best_partial(partial_candidates)
        
        # Step 3: Last resort - any valid word (different length, not used)
        return self._last_resort_move(current_len, word_history)
    
    def _find_valid_candidates(self, a, b, current_len, word_history):
        """Find words that contain both a and b in non-start/end positions."""
        if a == b:
            candidates = self.letter_non_start_end_index.get(a, set()).copy()
        else:
            set_a = self.letter_non_start_end_index.get(a, set())
            set_b = self.letter_non_start_end_index.get(b, set())
            candidates = set_a & set_b
        
        filtered = []
        for word in candidates:
            if word in word_history:
                continue
            length, non_set, first, last, _ = self.word_info[word]
            if length == current_len:
                continue
            if a == b:
                if first == a or last == a:
                    continue
            else:
                if first in (a, b) or last in (a, b):
                    continue
            filtered.append(word)
        return filtered
    
    def _find_partial_candidates(self, a, b, current_len, word_history):
        """Find words that contain exactly one required letter in middle."""
        if a == b:
            return []  # Impossible to have exactly one of two identical letters
        
        # Words with a but not b
        partial_a = self.letter_non_start_end_index.get(a, set()) - self.letter_any_index.get(b, set())
        # Words with b but not a
        partial_b = self.letter_non_start_end_index.get(b, set()) - self.letter_any_index.get(a, set())
        candidates = partial_a | partial_b
        
        filtered = []
        for word in candidates:
            if word in word_history:
                continue
            length, _, first, last, _ = self.word_info[word]
            if length == current_len:
                continue
            # Determine which required letter this candidate contains
            if word in partial_a:
                req = a
            else:
                req = b
            if first == req or last == req:
                continue
            filtered.append(word)
        return filtered
    
    def _select_best_valid(self, candidates, a, b):
        """Select valid candidate with highest score (considering length, hyphen, consecutive)."""
        best_word = None
        best_score = -float('inf')
        
        for word in candidates:
            length, _, _, _, has_hyphen = self.word_info[word]
            base = length / 2.0 if has_hyphen else length
            
            # Check consecutive bonus
            consecutive = False
            if a == b:
                if a * 2 in word:
                    consecutive = True
            else:
                if a + b in word or b + a in word:
                    consecutive = True
            
            score = base * (2 if consecutive else 1)
            if score > best_score or (score == best_score and random.random() < 0.5):
                best_score = score
                best_word = word
        
        return best_word
    
    def _select_best_partial(self, candidates):
        """Select partial candidate with smallest penalty (shortest, hyphenated preferred)."""
        best_word = None
        best_penalty = float('inf')
        
        for word in candidates:
            length, _, _, _, has_hyphen = self.word_info[word]
            penalty = length / 2.0 if has_hyphen else length
            if penalty < best_penalty or (penalty == best_penalty and random.random() < 0.5):
                best_penalty = penalty
                best_word = word
        
        return best_word
    
    def _last_resort_move(self, current_len, word_history):
        """Return any unused word with different length as last resort."""
        for word in self.dictionary:
            if word not in word_history and len(word) != current_len:
                return word
        # If nothing found, return any unused word (will be invalid but avoids crash)
        for word in self.dictionary:
            if word not in word_history:
                return word
        return random.choice(list(self.dictionary))
