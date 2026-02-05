"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 4
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
        self.length_index = defaultdict(set)
        self.pair_index = defaultdict(set)
        self.single_letter_index = defaultdict(set)

        for word in self.dictionary:
            if len(word) < 3:
                continue  # Words must have at least 3 letters to satisfy position constraints

            # Index by word length
            self.length_index[len(word)].add(word)

            # Index by first and last letters (for opponent moves)
            first_last = (word[0], word[-1])
            self.pair_index[first_last].add(word)

            # Index by all possible letter pairs (for our moves)
            # We'll build this during make_move since it's too large to pre-compute
            # Instead, we'll index by single letters and filter during move
            for c in set(word[1:-1]):  # Exclude first and last letters
                self.single_letter_index[c].add(word)

        # Pre-compute all possible letter pairs for faster lookup
        self.all_letters = set()
        for word in self.dictionary:
            for c in word:
                self.all_letters.add(c)
        self.all_letters = sorted(self.all_letters)

    def make_move(self, current_word, word_history):
        # Update history
        self.history = word_history

        # Get required letters
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        required_pair = (first_char, last_char)
        current_length = len(current_word)

        # Try to find a word with both letters first
        candidates = self._find_valid_words(required_pair, current_length)

        if candidates:
            # Score candidates and pick the best one
            best_word = self._select_best_word(candidates, required_pair)
            return best_word

        # If no word with both letters, try partial move (one letter)
        for letter in required_pair:
            partial_candidates = self._find_partial_words(letter, current_length)
            if partial_candidates:
                # For partial move, just pick the shortest word to minimize penalty
                best_word = min(partial_candidates, key=lambda x: len(x))
                return best_word

        # If absolutely no options, return a random word (will be invalid and lose)
        # This should theoretically never happen with a proper dictionary
        return random.choice(list(self.dictionary))

    def _find_valid_words(self, required_pair, current_length):
        first_char, last_char = required_pair
        candidates = set()

        # Get words that contain both letters (not at start/end)
        # We'll use the single letter index and intersect
        if first_char in self.single_letter_index and last_char in self.single_letter_index:
            first_words = self.single_letter_index[first_char]
            last_words = self.single_letter_index[last_char]
            candidates = first_words & last_words

            # Filter words that have the letters at start/end
            valid_candidates = set()
            for word in candidates:
                if len(word) == current_length:
                    continue
                if word in self.history:
                    continue
                if word[0] == first_char or word[0] == last_char:
                    continue
                if word[-1] == first_char or word[-1] == last_char:
                    continue
                # Check if both letters appear in the middle
                if (first_char in word[1:-1]) and (last_char in word[1:-1]):
                    valid_candidates.add(word)

            return valid_candidates

        return set()

    def _find_partial_words(self, required_letter, current_length):
        candidates = set()

        if required_letter in self.single_letter_index:
            for word in self.single_letter_index[required_letter]:
                if len(word) == current_length:
                    continue
                if word in self.history:
                    continue
                if word[0] == required_letter or word[-1] == required_letter:
                    continue
                if required_letter in word[1:-1]:
                    candidates.add(word)

        return candidates

    def _select_best_word(self, candidates, required_pair):
        first_char, last_char = required_pair
        best_word = None
        best_score = -float('inf')

        for word in candidates:
            # Calculate base score
            if '-' in word:
                base_score = len(word) / 2
            else:
                base_score = len(word)

            # Check for consecutive bonus
            word_lower = word.lower()
            if (first_char + last_char) in word_lower or (last_char + first_char) in word_lower:
                base_score *= 2

            # Simple heuristic: prefer longer words with bonus
            # In a real implementation, we might want to consider opponent's difficulty
            if base_score > best_score:
                best_score = base_score
                best_word = word

        return best_word if best_word else random.choice(list(candidates))
