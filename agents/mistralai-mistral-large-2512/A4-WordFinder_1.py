"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 1
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

        # Pre-process all words: index by (first_char, last_char) pairs they contain
        self.pair_index = defaultdict(list)
        self.length_index = defaultdict(set)  # Words by length for quick length filtering

        # Pre-compute all possible (char1, char2) pairs for each word
        for word in self.dictionary:
            if len(word) < 3:  # Words must have at least 3 letters to satisfy position constraints
                continue
            if '-' in word:  # Skip hyphenated words (penalty)
                continue

            # Get all possible (char1, char2) pairs in the word (excluding first/last positions)
            chars = set()
            for i in range(1, len(word)-1):
                for j in range(i+1, len(word)-1):
                    c1, c2 = word[i], word[j]
                    pair = (c1, c2) if c1 <= c2 else (c2, c1)
                    chars.add(pair)

            # Index the word by all its pairs
            for pair in chars:
                self.pair_index[pair].append(word)

            # Index by length
            self.length_index[len(word)].add(word)

        # Convert lists to sets for faster lookups
        for pair in self.pair_index:
            self.pair_index[pair] = set(self.pair_index[pair])

    def make_move(self, current_word, word_history):
        # Extract required letters
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        required_pair = (first_char, last_char) if first_char <= last_char else (last_char, first_char)
        current_length = len(current_word)

        # Get all candidate words that contain the required pair
        candidates = self.pair_index.get(required_pair, set())

        # Filter candidates:
        # 1. Not in history
        # 2. Different length than current word
        # 3. Contains both letters (already guaranteed by pair_index)
        # 4. Letters not at start/end (already guaranteed by pair_index construction)
        valid_words = []
        for word in candidates:
            if (word not in word_history and
                len(word) != current_length and
                word in self.dictionary):
                valid_words.append(word)

        # If we have valid words, choose the best one
        if valid_words:
            # Prioritize words with consecutive letters (bonus) and longer words
            best_word = None
            best_score = -1

            # Check for consecutive bonus first (highest priority)
            for word in valid_words:
                # Check if the required letters appear consecutively in either order
                if (first_char + last_char in word or last_char + first_char in word):
                    # Calculate potential score (length * 2)
                    score = len(word) * 2
                    if score > best_score:
                        best_score = score
                        best_word = word

            # If no consecutive bonus, choose the longest word
            if best_word is None:
                best_word = max(valid_words, key=lambda x: len(x))
            return best_word

        # If no valid words, try partial move (only one required letter)
        # First try with first_char
        partial_candidates = []
        for length in self.length_index:
            if length == current_length:
                continue
            for word in self.length_index[length]:
                if (word not in word_history and
                    first_char in word[1:-1] and
                    last_char not in word):
                    partial_candidates.append(word)

        if partial_candidates:
            return max(partial_candidates, key=lambda x: len(x))

        # Then try with last_char
        partial_candidates = []
        for length in self.length_index:
            if length == current_length:
                continue
            for word in self.length_index[length]:
                if (word not in word_history and
                    last_char in word[1:-1] and
                    first_char not in word):
                    partial_candidates.append(word)

        if partial_candidates:
            return max(partial_candidates, key=lambda x: len(x))

        # If absolutely no options, return a random word (will be invalid and lose)
        # This should theoretically never happen with a proper dictionary
        unused_words = self.dictionary - word_history
        if unused_words:
            return random.choice(list(unused_words))
        return "example"  # Fallback
