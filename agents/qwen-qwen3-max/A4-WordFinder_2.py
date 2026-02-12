"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-max
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    """
    Your agent implementation goes here.
    """
    def __init__(self, name):
        """
        Initialize your agent.
        """
        self.name = name
        self.dictionary = load_words()  # Load the full word dictionary
        
        # Precompute word lists by length to speed up searches
        self.words_by_length = defaultdict(set)
        self.words_without_hyphens = set()
        
        for word in self.dictionary:
            if '-' not in word:
                self.words_without_hyphens.add(word)
                self.words_by_length[len(word)].add(word)
            else:
                self.words_by_length[len(word)].add(word)
        
        # Precompute words containing specific letter pairs for bonus opportunities
        # This is a bit memory intensive but will help with finding consecutive letter bonuses
        self.words_with_consecutive_pairs = defaultdict(set)
        for word in self.words_without_hyphens:
            for i in range(len(word) - 1):
                pair = word[i:i+2]
                self.words_with_consecutive_pairs[pair].add(word)
                # Also add reverse pair since bonus works both ways
                reverse_pair = pair[::-1]
                if reverse_pair != pair:
                    self.words_with_consecutive_pairs[reverse_pair].add(word)

    def make_move(self, current_word, word_history):
        """
        Called when it's your turn.

        Parameters:
        -----------
        current_word : str
            The word played by the opponent (or the starting word).

        word_history : set
            A set of all words that have been used so far in the game (by both players).
            This includes the current_word and all previous words.
            You MUST NOT return a word that is in this set.

        Returns:
        --------
        str
            Your word choice.
        """
        current_word = current_word.lower()
        first_char = current_word[0]
        last_char = current_word[-1]
        current_length = len(current_word)
        
        required_chars = {first_char, last_char}
        
        # Try to find a valid word with bonus first (consecutive letters)
        best_word = None
        best_score = -1
        
        # Check for consecutive pair bonuses
        pair1 = first_char + last_char
        pair2 = last_char + first_char
        
        candidate_words = set()
        if pair1 in self.words_with_consecutive_pairs:
            candidate_words.update(self.words_with_consecutive_pairs[pair1])
        if pair2 in self.words_with_consecutive_pairs:
            candidate_words.update(self.words_with_consecutive_pairs[pair2])
        
        # Filter candidates
        for word in candidate_words:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            if word[0] in required_chars or word[-1] in required_chars:
                continue
            # Verify it actually contains both required chars (should be true due to precomputation, but double-check)
            if not (first_char in word and last_char in word):
                continue
                
            score = len(word) * 2  # Bonus applied
            if score > best_score:
                best_score = score
                best_word = word
        
        # If no bonus word found, look for regular valid words
        if best_word is None:
            # Search through all words of different lengths
            for length, words in self.words_by_length.items():
                if length == current_length:
                    continue
                    
                for word in words:
                    if word in word_history:
                        continue
                    if word[0] in required_chars or word[-1] in required_chars:
                        continue
                    if first_char not in word or last_char not in word:
                        continue
                    
                    # Calculate score
                    if '-' in word:
                        score = len(word) // 2
                    else:
                        score = len(word)
                        
                    if score > best_score:
                        best_score = score
                        best_word = word
        
        # If still no valid word found, try partial move (last resort)
        if best_word is None:
            # Try to find a word with only one of the required characters
            for length, words in self.words_by_length.items():
                if length == current_length:
                    continue
                    
                for word in words:
                    if word in word_history:
                        continue
                    # Check if it contains exactly one of the required chars, and not at start/end
                    has_first = first_char in word
                    has_last = last_char in word
                    
                    if (has_first or has_last) and not (has_first and has_last):
                        # Make sure the required char that is present is not at start or end
                        valid = True
                        if has_first and (word[0] == first_char or word[-1] == first_char):
                            valid = False
                        if has_last and (word[0] == last_char or word[-1] == last_char):
                            valid = False
                            
                        if valid:
                            # Return the first partial move we find (since it's a penalty anyway)
                            return word
            
            # If even partial move isn't possible, return a random word to avoid crash
            # This should rarely happen, but better than crashing
            available_words = [w for w in self.dictionary if w not in word_history and len(w) != current_length]
            if available_words:
                return random.choice(available_words)
            else:
                # Absolute fallback
                return random.choice(list(self.dictionary))
        
        return best_word
