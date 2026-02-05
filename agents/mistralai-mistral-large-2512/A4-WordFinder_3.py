"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 3
Generated: 2026-02-05 21:09:40
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.history = set()

        # Pre-process the dictionary for fast lookups
        self.letter_pair_index = defaultdict(set)
        self.letter_index = defaultdict(set)
        self.word_lengths = defaultdict(set)

        for word in self.dictionary:
            if len(word) < 3:
                continue  # Words must have at least 3 letters to satisfy position constraints

            # Index by word length
            self.word_lengths[len(word)].add(word)

            # Index by all possible letter pairs (excluding first/last positions)
            for i in range(1, len(word)-1):
                for j in range(i+1, len(word)):
                    pair = (word[i], word[j])
                    self.letter_pair_index[pair].add(word)
                    # Also index reverse pair
                    self.letter_pair_index[(pair[1], pair[0])].add(word)

            # Index by individual letters (excluding first/last positions)
            for i in range(1, len(word)-1):
                self.letter_index[word[i]].add(word)

    def make_move(self, current_word, word_history):
        # Extract required letters
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        required_pair = (first_char, last_char)
        current_length = len(current_word)

        # Get all words that contain both required letters (not at start/end)
        valid_words = set()
        if required_pair in self.letter_pair_index:
            valid_words = self.letter_pair_index[required_pair].copy()
        elif (last_char, first_char) in self.letter_pair_index:
            valid_words = self.letter_pair_index[(last_char, first_char)].copy()

        # Filter out used words and words of same length
        valid_words -= word_history
        valid_words = {word for word in valid_words if len(word) != current_length}

        # Check for consecutive bonus
        bonus_words = set()
        if valid_words:
            # Look for words with consecutive required letters
            consecutive_patterns = [first_char + last_char, last_char + first_char]
            for word in valid_words:
                word_lower = word.lower()
                for pattern in consecutive_patterns:
                    if pattern in word_lower:
                        bonus_words.add(word)
                        break

        # Prioritize bonus words, then longer words
        if bonus_words:
            # Sort by length descending, then by whether it has hyphen
            sorted_words = sorted(bonus_words, key=lambda x: (-len(x), '-' in x))
            return sorted_words[0]
        elif valid_words:
            # Sort by length descending, then by whether it has hyphen
            sorted_words = sorted(valid_words, key=lambda x: (-len(x), '-' in x))
            return sorted_words[0]

        # If no valid words, try partial move (one required letter)
        partial_words = set()
        for char in [first_char, last_char]:
            if char in self.letter_index:
                partial_words.update(self.letter_index[char])

        partial_words -= word_history
        partial_words = {word for word in partial_words if len(word) != current_length}

        if partial_words:
            # Sort by length descending, then by whether it has hyphen
            sorted_partial = sorted(partial_words, key=lambda x: (-len(x), '-' in x))
            return sorted_partial[0]

        # If absolutely no options, return a random word (will be invalid and lose)
        # This should theoretically never happen with a proper dictionary
        unused_words = self.dictionary - word_history
        if unused_words:
            return random.choice(list(unused_words))
        return "invalid"  # Last resort
