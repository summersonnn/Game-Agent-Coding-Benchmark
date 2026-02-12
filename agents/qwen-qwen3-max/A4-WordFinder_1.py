"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-max
Run: 1
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
        
        # Precompute word lists by length to speed up filtering
        self.words_by_length = defaultdict(set)
        for word in self.dictionary:
            if '-' not in word:  # Avoid hyphenated words unless necessary
                self.words_by_length[len(word)].add(word)
        
        # Also keep a separate set of hyphenated words (for partial moves or last resort)
        self.hyphenated_words = {word for word in self.dictionary if '-' in word}
        
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
        
        # Required letters
        required_letters = {first_char, last_char}
        
        # Find all candidate words that meet the basic constraints
        best_word = None
        best_score = -float('inf')
        
        # Try to find a valid word (containing both required letters)
        for length, words in self.words_by_length.items():
            if length == current_length:
                continue  # Skip same length
                
            for word in words:
                if word in word_history:
                    continue
                    
                # Check if word contains both required letters
                if not (first_char in word and last_char in word):
                    continue
                    
                # Check position constraint: required letters not at start or end
                if word[0] == first_char or word[-1] == first_char:
                    continue
                if word[0] == last_char or word[-1] == last_char:
                    continue
                    
                # Calculate score
                base_points = length
                # Check for consecutive bonus
                word_str = word
                consecutive_bonus = False
                for i in range(len(word_str) - 1):
                    pair = word_str[i:i+2]
                    if (pair == first_char + last_char) or (pair == last_char + first_char):
                        consecutive_bonus = True
                        break
                
                score = base_points * (2 if consecutive_bonus else 1)
                
                if score > best_score:
                    best_score = score
                    best_word = word
        
        # If no valid word found, check hyphenated words (though they give half points)
        if best_word is None:
            for word in self.hyphenated_words:
                if word in word_history:
                    continue
                if len(word) == current_length:
                    continue
                    
                if not (first_char in word and last_char in word):
                    continue
                    
                if word[0] == first_char or word[-1] == first_char:
                    continue
                if word[0] == last_char or word[-1] == last_char:
                    continue
                    
                base_points = len(word) / 2
                consecutive_bonus = False
                word_str = word
                for i in range(len(word_str) - 1):
                    pair = word_str[i:i+2]
                    if (pair == first_char + last_char) or (pair == last_char + first_char):
                        consecutive_bonus = True
                        break
                
                score = base_points * (2 if consecutive_bonus else 1)
                
                if score > best_score:
                    best_score = score
                    best_word = word
        
        # If still no valid word, try partial move (only one required letter)
        if best_word is None:
            # Try non-hyphenated words first for partial move
            for length, words in self.words_by_length.items():
                if length == current_length:
                    continue
                    
                for word in words:
                    if word in word_history:
                        continue
                        
                    # Check if word contains at least one required letter
                    has_first = first_char in word
                    has_last = last_char in word
                    
                    if not (has_first or has_last):
                        continue
                        
                    # Check position constraint for the letter it does contain
                    valid = True
                    if has_first:
                        if word[0] == first_char or word[-1] == first_char:
                            valid = False
                    if has_last:
                        if word[0] == last_char or word[-1] == last_char:
                            valid = False
                            
                    if not valid:
                        continue
                        
                    # Partial move gives negative points, but better than invalid
                    # We'll pick the longest word to minimize penalty (since penalty = -length)
                    score = -length
                    if score > best_score:  # Remember, best_score is negative here
                        best_score = score
                        best_word = word
            
            # If still nothing, try hyphenated for partial move
            if best_word is None:
                for word in self.hyphenated_words:
                    if word in word_history:
                        continue
                    if len(word) == current_length:
                        continue
                        
                    has_first = first_char in word
                    has_last = last_char in word
                    
                    if not (has_first or has_last):
                        continue
                        
                    valid = True
                    if has_first:
                        if word[0] == first_char or word[-1] == first_char:
                            valid = False
                    if has_last:
                        if word[0] == last_char or word[-1] == last_char:
                            valid = False
                            
                    if not valid:
                        continue
                        
                    score = -len(word) / 2  # Hyphenated partial move
                    if score > best_score:
                        best_score = score
                        best_word = word
        
        # If absolutely nothing found, return a random word (should not happen in practice)
        if best_word is None:
            available_words = [w for w in self.dictionary if w not in word_history and len(w) != current_length]
            if available_words:
                best_word = random.choice(available_words)
            else:
                # Fallback to any word not in history
                all_available = [w for w in self.dictionary if w not in word_history]
                if all_available:
                    best_word = random.choice(all_available)
                else:
                    # Last resort: pick any word (will likely be invalid, but we have to return something)
                    best_word = random.choice(list(self.dictionary))
        
        return best_word
