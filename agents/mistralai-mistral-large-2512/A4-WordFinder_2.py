"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 2
Generated: 2026-02-05 00:14:02
"""



import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.cache = {}  # Cache for faster lookups of valid words by first/last letters

    def make_move(self, current_word, word_history):
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        current_length = len(current_word)
        required_chars = {first_char, last_char}
        required_pairs = {first_char + last_char, last_char + first_char}

        # Initialize cache if not already done
        if (first_char, last_char) not in self.cache:
            self.cache[(first_char, last_char)] = self._find_valid_words(first_char, last_char)

        valid_words = self.cache[(first_char, last_char)]

        # Filter words based on game constraints
        candidates = []
        for word in valid_words:
            if (word in word_history or
                len(word) == current_length or
                word[0].lower() in required_chars or
                word[-1].lower() in required_chars):
                continue

            # Check for consecutive bonus
            has_bonus = False
            for pair in required_pairs:
                if pair in word.lower():
                    has_bonus = True
                    break

            # Calculate score potential
            length = len(word)
            if '-' in word:
                score = length / 2
            else:
                score = length

            if has_bonus:
                score *= 5

            candidates.append((score, word, has_bonus))

        if not candidates:
            return None  # No valid move, game ends

        # Sort by score descending, then by length descending (to maximize points)
        candidates.sort(key=lambda x: (-x[0], -len(x[1])))

        # Select the best candidate
        best_word = candidates[0][1]

        return best_word

    def _find_valid_words(self, first_char, last_char):
        """Precompute all valid words containing the required letters not at start/end"""
        valid_words = []
        required_chars = {first_char, last_char}

        for word in self.dictionary:
            word_lower = word.lower()
            # Skip words that don't contain both required letters
            if not (first_char in word_lower and last_char in word_lower):
                continue

            # Skip words where required letters are at start/end
            if (word_lower[0] in required_chars or
                word_lower[-1] in required_chars):
                continue

            valid_words.append(word)

        return valid_words
