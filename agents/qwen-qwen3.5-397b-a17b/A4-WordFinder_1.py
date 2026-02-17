"""
Agent Code: A4-WordFinder
Model: qwen/qwen3.5-397b-a17b
Run: 1
Generated: 2026-02-16 17:46:27
"""

from collections import defaultdict

import random
from collections import defaultdict


class WordFinderAgent:
    """
    WordFinder game agent with optimized word search and scoring strategy.
    """
    def __init__(self, name):
        """
        Initialize agent with pre-computed lookup tables for fast move selection.
        """
        self.name = name
        self.dictionary = load_words()
        
        # Filter to clean words (lowercase, alphabetic or with hyphens)
        self.words = [w for w in self.dictionary if w and len(w) >= 3]
        
        # Index words by length for quick length-based filtering
        self.words_by_length = defaultdict(list)
        
        # Index words by which letters they contain internally (not at start/end)
        # Key: frozenset of internal letters, Value: list of words
        self.words_by_internal_letters = defaultdict(list)
        
        # Index words by individual internal letters for partial move fallback
        # Key: letter, Value: list of words containing that letter internally
        self.words_by_single_internal = defaultdict(list)
        
        # Pre-compute all indices
        self._build_indices()
    
    def _build_indices(self):
        """Build lookup indices for fast word searching."""
        for word in self.words:
            word_lower = word.lower()
            length = len(word_lower)
            
            # Skip very short words
            if length < 3:
                continue
            
            # Index by length
            self.words_by_length[length].append(word_lower)
            
            # Get internal letters (not first or last)
            if length > 2:
                internal = word_lower[1:-1]
                internal_letters = set(internal)
                
                # Index by set of internal letters
                if internal_letters:
                    key = frozenset(internal_letters)
                    self.words_by_internal_letters[key].append(word_lower)
                
                # Index by individual internal letters
                for letter in internal_letters:
                    self.words_by_single_internal[letter].append(word_lower)
    
    def make_move(self, current_word, word_history):
        """
        Find the best valid word based on game rules and scoring optimization.
        """
        current_lower = current_word.lower()
        first_char = current_lower[0]
        last_char = current_lower[-1]
        current_length = len(current_lower)
        
        # Required letters that must appear internally
        required_letters = {first_char, last_char}
        
        # Find all candidate words
        candidates = self._find_valid_candidates(
            first_char, last_char, current_length, word_history
        )
        
        if candidates:
            # Score and select best candidate
            return self._select_best_word(candidates, first_char, last_char)
        
        # Fallback: partial move with one required letter
        partial = self._find_partial_move(
            first_char, last_char, current_length, word_history
        )
        
        if partial:
            return partial
        
        # Last resort: return any valid word not in history
        return self._get_random_valid_word(current_length, word_history)
    
    def _find_valid_candidates(self, first_char, last_char, current_length, word_history):
        """Find words containing both required letters internally."""
        candidates = []
        
        # Get words that contain both letters internally
        # Check all words that have first_char internally
        for word in self.words_by_single_internal.get(first_char, []):
            if len(word) == current_length:
                continue
            if word in word_history:
                continue
            
            # Verify word contains both required letters internally
            internal = word[1:-1]
            if first_char in internal and last_char in internal:
                # Verify neither is at start or end
                if (word[0].lower() != first_char and word[-1].lower() != first_char and
                    word[0].lower() != last_char and word[-1].lower() != last_char):
                    candidates.append(word)
        
        return candidates
    
    def _select_best_word(self, candidates, first_char, last_char):
        """Select the highest scoring word from candidates."""
        scored = []
        
        for word in candidates:
            score = self._calculate_score(word, first_char, last_char)
            scored.append((score, word))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Add some randomness among top candidates to avoid predictability
        top_score = scored[0][0]
        top_candidates = [w for s, w in scored if s >= top_score * 0.9]
        
        if len(top_candidates) > 1:
            return random.choice(top_candidates)
        
        return scored[0][1]
    
    def _calculate_score(self, word, first_char, last_char):
        """Calculate the score for a word based on game rules."""
        length = len(word)
        
        # Hyphen penalty
        if '-' in word:
            length = length / 2
        
        # Consecutive letter bonus (PH or HP)
        internal = word[1:-1]
        if (first_char + last_char in internal or 
            last_char + first_char in internal):
            length *= 2
        
        return length
    
    def _find_partial_move(self, first_char, last_char, current_length, word_history):
        """Find a word with only ONE required letter internally (fallback)."""
        for char in [first_char, last_char]:
            for word in self.words_by_single_internal.get(char, []):
                if len(word) == current_length:
                    continue
                if word in word_history:
                    continue
                
                internal = word[1:-1]
                # Must contain this char internally
                if char not in internal:
                    continue
                
                # Must NOT contain the other required letter internally
                other_char = last_char if char == first_char else first_char
                if other_char in internal:
                    continue
                
                # Verify char is not at start or end
                if word[0].lower() == char or word[-1].lower() == char:
                    continue
                
                return word
        
        return None
    
    def _get_random_valid_word(self, current_length, word_history):
        """Get any valid word not in history as last resort."""
        available = [w for w in self.words if w not in word_history and len(w) != current_length]
        
        if available:
            return random.choice(available)
        
        # Absolute last resort
        return "the"
