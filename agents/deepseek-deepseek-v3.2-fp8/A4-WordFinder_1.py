"""
Agent Code: A4-WordFinder
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 1
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict, deque

import random
from collections import defaultdict, deque

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Precompute data structures for fast lookups
        self._build_indexes()
    
    def _build_indexes(self):
        """Build efficient indexes for word lookup"""
        # Index 1: Words by their letters (excluding first/last positions)
        self.letter_to_words = defaultdict(set)
        
        # Index 2: Words by length
        self.length_to_words = defaultdict(set)
        
        # Index 3: Words with consecutive letter pairs
        self.consecutive_pairs = defaultdict(set)
        
        # Index 4: First letters that are rare (hard for opponent)
        self.first_letter_freq = defaultdict(int)
        self.last_letter_freq = defaultdict(int)
        
        for word in self.dictionary:
            # Store by length
            self.length_to_words[len(word)].add(word)
            
            # Track letter frequencies for defensive play
            self.first_letter_freq[word[0]] += 1
            self.last_letter_freq[word[-1]] += 1
            
            # Index by letters in middle positions
            middle_letters = set(word[1:-1]) if len(word) > 2 else set()
            for letter in middle_letters:
                self.letter_to_words[letter].add(word)
            
            # Index consecutive letter pairs
            for i in range(len(word) - 1):
                pair = word[i:i+2]
                self.consecutive_pairs[pair].add(word)
                # Also index reverse pair for bonus check
                rev_pair = pair[1] + pair[0]
                self.consecutive_pairs[rev_pair].add(word)
        
        # Precompute rare letters (for defensive strategy)
        self.rare_first_letters = sorted(
            self.first_letter_freq.keys(),
            key=lambda x: self.first_letter_freq[x]
        )[:10]
        
        self.rare_last_letters = sorted(
            self.last_letter_freq.keys(),
            key=lambda x: self.last_letter_freq[x]
        )[:10]
    
    def _calculate_score(self, word, first_letter, last_letter):
        """Calculate potential score for a candidate word"""
        # Base points
        base = len(word)
        
        # Hyphen penalty
        if '-' in word:
            base /= 2
        
        # Consecutive letter bonus
        pair1 = first_letter + last_letter
        pair2 = last_letter + first_letter
        if pair1 in word or pair2 in word:
            base *= 2
        
        return base
    
    def _is_valid_word(self, word, current_word, word_history, first_letter, last_letter):
        """Check if a word satisfies all constraints"""
        if word in word_history:
            return False
        
        if len(word) == len(current_word):
            return False
        
        if word[0] == first_letter or word[-1] == first_letter:
            return False
        
        if word[0] == last_letter or word[-1] == last_letter:
            return False
        
        if first_letter not in word or last_letter not in word:
            return False
        
        return True
    
    def _find_best_word(self, first_letter, last_letter, current_length, word_history):
        """Find the highest-scoring valid word"""
        best_word = None
        best_score = -1
        
        # Strategy 1: Look for words with consecutive bonus first
        consecutive_pair1 = first_letter + last_letter
        consecutive_pair2 = last_letter + first_letter
        
        # Check both orders for consecutive bonus
        for pair in [consecutive_pair1, consecutive_pair2]:
            if pair in self.consecutive_pairs:
                for word in self.consecutive_pairs[pair]:
                    if (self._is_valid_candidate(word, first_letter, last_letter, 
                                                current_length, word_history)):
                        score = self._calculate_score(word, first_letter, last_letter)
                        if score > best_score:
                            best_score = score
                            best_word = word
        
        # Strategy 2: If no consecutive bonus words found, look for long words
        if best_word is None:
            # Start from longest words down to shortest
            for length in sorted(self.length_to_words.keys(), reverse=True):
                if length == current_length:
                    continue
                
                # Filter words of this length that contain both letters
                for word in self.length_to_words[length]:
                    if (first_letter in word and last_letter in word and
                        self._is_valid_candidate(word, first_letter, last_letter,
                                                current_length, word_history)):
                        score = self._calculate_score(word, first_letter, last_letter)
                        if score > best_score:
                            best_score = score
                            best_word = word
                            # Early exit if we find a very long word without hyphen
                            if '-' not in word and length > 12:
                                return best_word
        
        return best_word
    
    def _is_valid_candidate(self, word, first_letter, last_letter, current_length, word_history):
        """Check if a word satisfies all constraints"""
        if word in word_history:
            return False
        if len(word) == current_length:
            return False
        if word[0] == first_letter or word[-1] == first_letter:
            return False
        if word[0] == last_letter or word[-1] == last_letter:
            return False
        if first_letter not in word or last_letter not in word:
            return False
        return True
    
    def _find_partial_move(self, first_letter, last_letter, current_length, word_history):
        """Find a word containing only one required letter (last resort)"""
        # Try to find a short word with one letter to minimize penalty
        for length in sorted(self.length_to_words.keys()):
            if length == current_length:
                continue
            
            for word in self.length_to_words[length]:
                if word in word_history:
                    continue
                
                # Check for words with first_letter but not last_letter
                if (first_letter in word[1:-1] and 
                    last_letter not in word and
                    word[0] != first_letter and 
                    word[-1] != first_letter):
                    return word
                
                # Check for words with last_letter but not first_letter
                if (last_letter in word[1:-1] and 
                    first_letter not in word and
                    word[0] != last_letter and 
                    word[-1] != last_letter):
                    return word
        
        return None
    
    def _calculate_defensive_score(self, word):
        """Calculate how defensive a word is (higher = harder for opponent)"""
        score = 0
        
        # Rare first letters are better
        if word[0] in self.rare_first_letters:
            score += 3
        
        # Rare last letters are better
        if word[-1] in self.rare_last_letters:
            score += 3
        
        # Short words with rare letters are extra hard
        if len(word) < 6 and score > 0:
            score += 2
        
        return score
    
    def make_move(self, current_word, word_history):
        # Convert to lowercase for consistency
        current_word = current_word.lower()
        first_letter = current_word[0]
        last_letter = current_word[-1]
        current_length = len(current_word)
        
        # Try to find the best valid word
        best_word = self._find_best_word(first_letter, last_letter, 
                                        current_length, word_history)
        
        # If found, return it
        if best_word is not None:
            return best_word
        
        # Last resort: partial move
        partial_word = self._find_partial_move(first_letter, last_letter,
                                              current_length, word_history)
        
        if partial_word is not None:
            return partial_word
        
        # Emergency fallback: return any unused word (will get -10 penalty but avoids crash)
        for word in self.dictionary:
            if word not in word_history and len(word) != current_length:
                return word
        
        # Absolute last resort
        return random.choice(list(self.dictionary))
