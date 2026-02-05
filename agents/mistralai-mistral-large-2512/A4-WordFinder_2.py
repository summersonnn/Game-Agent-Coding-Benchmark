"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 2
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
        self.length_index = defaultdict(set)
        self.consecutive_bonus_index = defaultdict(set)

        for word in self.dictionary:
            if len(word) < 3:  # Words must have at least 3 letters to satisfy position constraints
                continue

            # Index by length
            self.length_index[len(word)].add(word)

            # Get all possible letter pairs (excluding first and last letters)
            first_char = word[0]
            last_char = word[-1]

            # Find all unique pairs of letters in the word (excluding first/last positions)
            for i in range(1, len(word)-1):
                for j in range(i+1, len(word)):
                    char1, char2 = sorted((word[i], word[j]))
                    pair = (char1, char2)
                    self.letter_pair_index[pair].add(word)

                    # Check for consecutive letters (bonus)
                    if abs(i - j) == 1:
                        self.consecutive_bonus_index[pair].add(word)

    def make_move(self, current_word, word_history):
        # Update history
        self.history = word_history

        # Get required letters
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        required_pair = tuple(sorted((first_char, last_char)))
        current_length = len(current_word)

        # Try to find a word with both letters (consecutive bonus first)
        candidates = []

        # 1. Check for words with consecutive letters (bonus)
        if required_pair in self.consecutive_bonus_index:
            candidates = self.consecutive_bonus_index[required_pair] - word_history
            # Filter by length and position constraints
            valid_candidates = []
            for word in candidates:
                if len(word) == current_length:
                    continue
                # Check position constraints
                first_pos = word.find(first_char)
                last_pos = word.find(last_char)
                if (first_pos > 0 and first_pos < len(word)-1 and
                    last_pos > 0 and last_pos < len(word)-1):
                    valid_candidates.append(word)
            if valid_candidates:
                # Sort by length (descending) to maximize points
                valid_candidates.sort(key=lambda x: -len(x))
                return valid_candidates[0]

        # 2. Check for words with both letters (non-consecutive)
        if required_pair in self.letter_pair_index:
            candidates = self.letter_pair_index[required_pair] - word_history
            # Filter by length and position constraints
            valid_candidates = []
            for word in candidates:
                if len(word) == current_length:
                    continue
                # Check position constraints
                first_pos = word.find(first_char)
                last_pos = word.find(last_char)
                if (first_pos > 0 and first_pos < len(word)-1 and
                    last_pos > 0 and last_pos < len(word)-1):
                    valid_candidates.append(word)
            if valid_candidates:
                # Sort by length (descending) to maximize points
                valid_candidates.sort(key=lambda x: -len(x))
                return valid_candidates[0]

        # 3. Partial move fallback - try with just one letter
        # Try first_char first
        partial_candidates = []
        for length in sorted(self.length_index.keys(), reverse=True):
            if length == current_length:
                continue
            for word in self.length_index[length]:
                if word in word_history:
                    continue
                pos = word.find(first_char)
                if pos > 0 and pos < len(word)-1:
                    partial_candidates.append(word)
                    break  # Just take one per length

        if partial_candidates:
            # Return the longest possible partial move
            partial_candidates.sort(key=lambda x: -len(x))
            return partial_candidates[0]

        # Try last_char if first_char didn't work
        partial_candidates = []
        for length in sorted(self.length_index.keys(), reverse=True):
            if length == current_length:
                continue
            for word in self.length_index[length]:
                if word in word_history:
                    continue
                pos = word.find(last_char)
                if pos > 0 and pos < len(word)-1:
                    partial_candidates.append(word)
                    break

        if partial_candidates:
            partial_candidates.sort(key=lambda x: -len(x))
            return partial_candidates[0]

        # If absolutely no options, return a random word (will lose)
        # This should theoretically never happen with a proper dictionary
        unused_words = self.dictionary - word_history
        if unused_words:
            return random.choice(list(unused_words))
        return "surrender"  # Last resort
