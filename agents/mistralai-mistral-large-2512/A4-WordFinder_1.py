"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Precompute letter pairs for faster lookup
        self.letter_pair_index = defaultdict(list)
        self.letter_index = defaultdict(list)
        self.word_lengths = defaultdict(set)

        for word in self.dictionary:
            if len(word) < 3:  # Words must be at least 3 letters to satisfy position constraints
                continue
            if '-' in word:
                continue  # Skip hyphenated words initially (we'll check them later if needed)
            first_char = word[0]
            last_char = word[-1]
            self.word_lengths[len(word)].add(word)

            # Index words by their first and last character pairs
            pair = (first_char, last_char)
            self.letter_pair_index[pair].append(word)

            # Index words by individual characters (for partial moves)
            for i, char in enumerate(word[1:-1], 1):
                self.letter_index[char].append((word, i))

        # Sort words by length descending for each pair to prioritize longer words
        for pair in self.letter_pair_index:
            self.letter_pair_index[pair].sort(key=lambda x: -len(x))

        # Sort words by length descending for each character
        for char in self.letter_index:
            self.letter_index[char].sort(key=lambda x: -len(x[0]))

    def make_move(self, current_word, word_history):
        current_word = current_word.lower()
        if current_word not in self.dictionary:
            return self._find_random_word(word_history)

        required_first = current_word[0]
        required_last = current_word[-1]
        required_pair = (required_first, required_last)
        current_length = len(current_word)
        used_words = set(word.lower() for word in word_history)

        # First try to find words with both letters (consecutive bonus is best)
        best_word = self._find_best_word_with_pair(required_pair, current_length, used_words)
        if best_word:
            return best_word

        # Then try words with both letters in any order (no bonus)
        best_word = self._find_word_with_both_letters(required_first, required_last, current_length, used_words)
        if best_word:
            return best_word

        # If no words with both letters, try partial moves
        # First try with first letter
        partial_word = self._find_partial_word(required_first, current_length, used_words)
        if partial_word:
            return partial_word

        # Then try with last letter
        partial_word = self._find_partial_word(required_last, current_length, used_words)
        if partial_word:
            return partial_word

        # If all else fails, return a random valid word (should rarely happen)
        return self._find_random_word(used_words)

    def _find_best_word_with_pair(self, required_pair, current_length, used_words):
        """Find words containing the required pair consecutively (for bonus points)"""
        # Check both possible orders of the pair
        for pair in [required_pair, (required_pair[1], required_pair[0])]:
            if pair in self.letter_pair_index:
                for word in self.letter_pair_index[pair]:
                    if (len(word) != current_length and
                        word not in used_words and
                        word[0] != pair[0] and word[0] != pair[1] and
                        word[-1] != pair[0] and word[-1] != pair[1]):
                        # Check if the pair appears consecutively in the word
                        pair_str = pair[0] + pair[1]
                        if pair_str in word:
                            return word
        return None

    def _find_word_with_both_letters(self, first_char, last_char, current_length, used_words):
        """Find words containing both letters but not consecutively (no bonus)"""
        # First try non-hyphenated words
        for word in self.dictionary:
            if (len(word) != current_length and
                word not in used_words and
                '-' not in word and
                first_char in word[1:-1] and
                last_char in word[1:-1] and
                word[0] not in (first_char, last_char) and
                word[-1] not in (first_char, last_char)):
                return word

        # Then try hyphenated words if no other options
        for word in self.dictionary:
            if '-' in word:
                # Check if hyphenated word meets all criteria
                base_word = word.replace('-', '')
                if (len(word) != current_length and
                    word not in used_words and
                    first_char in base_word[1:-1] and
                    last_char in base_word[1:-1] and
                    word[0] not in (first_char, last_char) and
                    word[-1] not in (first_char, last_char)):
                    return word
        return None

    def _find_partial_word(self, required_char, current_length, used_words):
        """Find words containing only one of the required letters (partial move)"""
        if required_char in self.letter_index:
            for word, pos in self.letter_index[required_char]:
                if (len(word) != current_length and
                    word not in used_words and
                    word[0] != required_char and
                    word[-1] != required_char):
                    return word
        return None

    def _find_random_word(self, used_words):
        """Fallback to find any valid word (should rarely be needed)"""
        for word in self.dictionary:
            if (len(word) >= 3 and
                word not in used_words and
                '-' not in word and
                len(word) != len(next(iter(used_words), ""))):
                return word
        return "a"  # Should never reach here if dictionary is valid
