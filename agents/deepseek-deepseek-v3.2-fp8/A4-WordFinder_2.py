"""
Agent Code: A4-WordFinder
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict, deque

import random
from collections import defaultdict, deque

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # Returns a set of lowercase words
        
        # Precompute data structures for fast lookups
        self._build_indexes()
        
    def _build_indexes(self):
        """Build indexes for efficient word lookups"""
        # Index words by letters they contain (excluding first/last positions)
        self.words_by_contained_letters = defaultdict(set)
        
        # Index words by length
        self.words_by_length = defaultdict(set)
        
        # Index words by starting and ending letters (for defensive play)
        self.words_by_start_end = defaultdict(set)
        
        # Cache for consecutive letter pairs
        self.consecutive_pairs_cache = {}
        
        # Store all valid words for quick membership test
        self.all_words_set = self.dictionary
        
        for word in self.dictionary:
            # Skip very short words (they're rarely useful)
            if len(word) < 3:
                continue
                
            # Index by length
            self.words_by_length[len(word)].add(word)
            
            # Index by start-end pair (for defensive strategy)
            start_end = (word[0], word[-1])
            self.words_by_start_end[start_end].add(word)
            
            # Index by letters contained in non-edge positions
            # We track letters that appear NOT at position 0 or -1
            interior_letters = set()
            for i, letter in enumerate(word):
                if i != 0 and i != len(word) - 1:
                    interior_letters.add(letter)
            
            # For each letter in the interior, add this word
            for letter in interior_letters:
                self.words_by_contained_letters[letter].add(word)
            
            # Precompute consecutive letter pairs in this word
            pairs = set()
            for i in range(len(word) - 1):
                pairs.add(word[i:i+2])
                # Also track reverse pairs for bonus checking
                pairs.add(word[i+1] + word[i])
            self.consecutive_pairs_cache[word] = pairs
    
    def _get_candidates(self, letter1, letter2, exclude_length, used_words):
        """Find candidate words containing both letters, not at edges"""
        # Get words containing both letters in interior positions
        words_with_letter1 = self.words_by_contained_letters.get(letter1, set())
        words_with_letter2 = self.words_by_contained_letters.get(letter2, set())
        
        # Intersection contains words with both letters in interior
        candidates = words_with_letter1.intersection(words_with_letter2)
        
        # Filter out words where letters might appear at edges
        valid_candidates = []
        for word in candidates:
            if len(word) == exclude_length:
                continue
            if word in used_words:
                continue
            
            # Double-check that neither letter is at start or end
            if word[0] == letter1 or word[-1] == letter1:
                continue
            if word[0] == letter2 or word[-1] == letter2:
                continue
            
            valid_candidates.append(word)
        
        return valid_candidates
    
    def _score_word(self, word, letter1, letter2):
        """Calculate score for a word given required letters"""
        base_score = len(word)
        
        # Hyphen penalty
        if '-' in word:
            base_score //= 2
        
        # Consecutive letter bonus
        pairs = self.consecutive_pairs_cache.get(word, set())
        if f"{letter1}{letter2}" in pairs or f"{letter2}{letter1}" in pairs:
            base_score *= 2
        
        return base_score
    
    def _get_partial_candidates(self, letter1, letter2, exclude_length, used_words):
        """Find words containing only one of the required letters (for partial moves)"""
        candidates = []
        
        # Try words with letter1 only
        words_with_letter1 = self.words_by_contained_letters.get(letter1, set())
        for word in words_with_letter1:
            if len(word) == exclude_length:
                continue
            if word in used_words:
                continue
            if word[0] == letter1 or word[-1] == letter1:
                continue
            # Must NOT contain letter2 in interior
            if letter2 in word[1:-1]:
                continue
            candidates.append(word)
        
        # Try words with letter2 only
        words_with_letter2 = self.words_by_contained_letters.get(letter2, set())
        for word in words_with_letter2:
            if len(word) == exclude_length:
                continue
            if word in used_words:
                continue
            if word[0] == letter2 or word[-1] == letter2:
                continue
            # Must NOT contain letter1 in interior
            if letter1 in word[1:-1]:
                continue
            candidates.append(word)
        
        return candidates
    
    def _get_defensive_score(self, word, used_words):
        """Evaluate how difficult this word will be for opponent"""
        start_letter = word[0]
        end_letter = word[-1]
        
        # Count how many unused words the opponent could potentially play
        potential_responses = 0
        
        # Get words containing both start and end letters in interior
        candidates = self._get_candidates(start_letter, end_letter, len(word), used_words)
        potential_responses = len(candidates)
        
        # Prefer words with rare start/end letter combinations
        # Rare letters: q, j, x, z, v, k
        rare_letters = {'q', 'j', 'x', 'z', 'v', 'k'}
        rarity_bonus = 0
        if start_letter in rare_letters:
            rarity_bonus += 3
        if end_letter in rare_letters:
            rarity_bonus += 3
        
        # Penalize common vowel endings (easy to find words)
        common_vowels = {'a', 'e', 'i', 'o', 'u'}
        if end_letter in common_vowels:
            potential_responses += 5  # Estimate more responses
        
        return -potential_responses + rarity_bonus
    
    def make_move(self, current_word, word_history):
        """Choose the best word to play"""
        # Extract required letters
        letter1 = current_word[0].lower()
        letter2 = current_word[-1].lower()
        exclude_length = len(current_word)
        
        # Get valid candidates
        candidates = self._get_candidates(letter1, letter2, exclude_length, word_history)
        
        if candidates:
            # Score each candidate
            scored_candidates = []
            for word in candidates:
                # Base score (points we get)
                base_score = self._score_word(word, letter1, letter2)
                
                # Defensive score (how hard for opponent)
                defensive_score = self._get_defensive_score(word, word_history)
                
                # Combine scores with weights
                total_score = base_score * 2 + defensive_score
                
                # Prefer words without hyphens
                if '-' not in word:
                    total_score += 5
                
                # Prefer consecutive bonus
                pairs = self.consecutive_pairs_cache.get(word, set())
                if f"{letter1}{letter2}" in pairs or f"{letter2}{letter1}" in pairs:
                    total_score += 10
                
                scored_candidates.append((total_score, base_score, word))
            
            # Sort by total score
            scored_candidates.sort(reverse=True, key=lambda x: x[0])
            
            # Return the best word
            if scored_candidates:
                return scored_candidates[0][2]
        
        # No valid word found - try partial move
        partial_candidates = self._get_partial_candidates(letter1, letter2, exclude_length, word_history)
        
        if partial_candidates:
            # For partial moves, choose SHORT words to minimize penalty
            partial_candidates.sort(key=len)
            # Prefer words without hyphens (full penalty vs half penalty)
            non_hyphen = [w for w in partial_candidates if '-' not in w]
            if non_hyphen:
                return non_hyphen[0]
            return partial_candidates[0]
        
        # Last resort: return any unused word (will get -10 penalty but continues game)
        # Try to find a word that at least contains one of the letters
        for word in self.dictionary:
            if word not in word_history and len(word) != exclude_length:
                if (letter1 in word[1:-1] or letter2 in word[1:-1]):
                    return word
        
        # Absolute last resort
        for word in self.dictionary:
            if word not in word_history:
                return word
        
        # Should never reach here, but just in case
        return "error"
