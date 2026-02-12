"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()

        # Precompute letter pair to words mapping for faster lookup
        self.letter_pair_map = defaultdict(list)
        self.single_letter_map = defaultdict(list)

        for word in self.dictionary:
            if len(word) < 3:  # Words must be at least 3 letters to satisfy position constraints
                continue
            if '-' in word:
                continue  # Skip hyphenated words initially (we'll handle them separately)

            # Map first and last letters to words
            first_char = word[0]
            last_char = word[-1]
            pair = (first_char, last_char)

            # Store words that contain both letters (not at start/end)
            if first_char in word[1:-1] and last_char in word[1:-1]:
                self.letter_pair_map[pair].append(word)
                # Also store reverse pair
                self.letter_pair_map[(last_char, first_char)].append(word)

            # Store words that contain single letters (for partial moves)
            for char in set(word[1:-1]):
                self.single_letter_map[char].append(word)

        # Precompute hyphenated words separately
        self.hyphenated_words = [word for word in self.dictionary if '-' in word]

    def make_move(self, current_word, word_history):
        # Get required letters
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        required_pair = (first_char, last_char)
        current_length = len(current_word)

        # Convert word_history to lowercase set for case-insensitive comparison
        used_words = {word.lower() for word in word_history}

        # First try to find words with both letters (full move)
        candidate_words = []

        # Check both possible orderings of the pair
        for pair in [required_pair, (last_char, first_char)]:
            if pair in self.letter_pair_map:
                for word in self.letter_pair_map[pair]:
                    word_lower = word.lower()
                    if (word_lower not in used_words and
                        len(word) != current_length and
                        first_char in word[1:-1] and
                        last_char in word[1:-1]):

                        # Check if letters appear consecutively for bonus
                        has_consecutive = False
                        if pair[0] + pair[1] in word or pair[1] + pair[0] in word:
                            has_consecutive = True

                        candidate_words.append((word, len(word), has_consecutive, False))

        # Sort candidates by score potential (longest first, then bonus)
        candidate_words.sort(key=lambda x: (-x[1], -x[2]))

        # Try to find the best valid word
        for word, length, has_bonus, is_hyphen in candidate_words:
            if word.lower() not in used_words:
                return word

        # If no full move found, try hyphenated words
        for word in self.hyphenated_words:
            word_lower = word.lower()
            if (word_lower not in used_words and
                len(word) != current_length and
                first_char in word[1:-1] and
                last_char in word[1:-1]):

                # Check if letters appear consecutively
                has_consecutive = False
                if first_char + last_char in word or last_char + first_char in word:
                    has_consecutive = True

                return word

        # If still no full move, try partial moves (one required letter)
        # First try with first_char
        if first_char in self.single_letter_map:
            for word in self.single_letter_map[first_char]:
                word_lower = word.lower()
                if (word_lower not in used_words and
                    len(word) != current_length and
                    first_char in word[1:-1] and
                    last_char not in word):  # Must not contain the other letter

                    return word

        # Then try with last_char
        if last_char in self.single_letter_map:
            for word in self.single_letter_map[last_char]:
                word_lower = word.lower()
                if (word_lower not in used_words and
                    len(word) != current_length and
                    last_char in word[1:-1] and
                    first_char not in word):  # Must not contain the other letter

                    return word

        # If absolutely no valid move found, return a random word that at least follows some rules
        # This should rarely happen with a good dictionary
        fallback_words = [word for word in self.dictionary
                         if len(word) != current_length and
                         word.lower() not in used_words and
                         len(word) > 2]

        if fallback_words:
            return random.choice(fallback_words)

        # Final fallback - return a word that might get us some points
        return "example"
