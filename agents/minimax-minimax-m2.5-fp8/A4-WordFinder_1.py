"""
Agent Code: A4-WordFinder
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-14 18:23:39
"""

from collections import defaultdict

import random
from collections import defaultdict


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Pre-compute data structures for efficient lookup
        # Words grouped by length
        self.words_by_length = defaultdict(set)
        for word in self.dictionary:
            self.words_by_length[len(word)].add(word)
        
        # Words grouped by first-last letter pair
        self.words_by_fl = defaultdict(set)
        for word in self.dictionary:
            if len(word) >= 2:
                fl = (word[0], word[-1])
                self.words_by_fl[fl].add(word)
        
        # Words containing each letter
        self.words_containing = defaultdict(set)
        for word in self.dictionary:
            for letter in set(word):
                self.words_containing[letter].add(word)
        
        # Pre-compute consecutive letter pairs for bonus detection
        self.consecutive_cache = {}
        for word in self.dictionary:
            self.consecutive_cache[word] = set()
            for i in range(len(word) - 1):
                self.consecutive_cache[word].add(word[i:i+2])
    
    def make_move(self, current_word, word_history):
        # Handle starting move
        if not current_word:
            # Pick a random long word to start
            valid_starts = [w for w in self.words_by_length.get(8, set()) 
                           if w not in word_history and len(w) >= 5]
            if valid_starts:
                return random.choice(valid_starts)
            return random.choice(list(self.dictionary))
        
        required_first = current_word[0]
        required_last = current_word[-1]
        current_length = len(current_word)
        
        # Find all valid candidates
        candidates = self._find_valid_candidates(
            required_first, required_last, current_length, word_history
        )
        
        if candidates:
            # Score and rank candidates
            scored = []
            for word in candidates:
                base_score = len(word)
                
                # Check for hyphen penalty
                if '-' in word:
                    base_score //= 2
                
                # Check for consecutive letter bonus
                consecutive_pair = required_first + required_last
                reverse_pair = required_last + required_first
                if consecutive_pair in word or reverse_pair in word:
                    base_score *= 2
                
                # Add randomness to break ties
                scored.append((base_score, len(word), random.random(), word))
            
            # Sort by score (desc), length (desc), random
            scored.sort(key=lambda x: (-x[0], -x[1], -x[2]))
            return scored[0][3]
        
        # Fallback: partial move
        return self._find_partial_move(
            required_first, required_last, current_length, word_history
        )
    
    def _find_valid_candidates(self, required_first, required_last, current_length, word_history):
        """Find all words meeting the constraints"""
        candidates = []
        
        # Get words containing both required letters
        first_set = self.words_containing.get(required_first, set())
        last_set = self.words_containing.get(required_last, set())
        both_letters = first_set & last_set
        
        for word in both_letters:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            
            # Check position constraint: required letters cannot be at start/end
            if word[0] == required_first or word[-1] == required_first:
                continue
            if word[0] == required_last or word[-1] == required_last:
                continue
            
            candidates.append(word)
        
        return candidates
    
    def _find_partial_move(self, required_first, required_last, current_length, word_history):
        """Fallback: find a word with only ONE required letter (not at start/end)"""
        # Try words with first letter
        first_set = self.words_containing.get(required_first, set())
        for word in first_set:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            # Must have first but NOT last
            if required_last in word:
                continue
            # First letter cannot be at start or end
            if word[0] == required_first or word[-1] == required_first:
                continue
            return word
        
        # Try words with last letter
        last_set = self.words_containing.get(required_last, set())
        for word in last_set:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            # Must have last but NOT first
            if required_first in word:
                continue
            # Last letter cannot be at start or end
            if word[0] == required_last or word[-1] == required_last:
                continue
            return word
        
        # Last resort: any valid word not in history
        for length, words in self.words_by_length.items():
            if length == current_length:
                continue
            available = words - word_history
            if available:
                return random.choice(list(available))
        
        return random.choice(list(self.dictionary - word_history))
