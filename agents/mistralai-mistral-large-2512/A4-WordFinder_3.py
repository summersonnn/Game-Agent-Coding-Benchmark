"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 3
Generated: 2026-02-05 00:14:02
"""



import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.history = set()

    def make_move(self, current_word, word_history):
        required_first = current_word[0].lower()
        required_last = current_word[-1].lower()
        current_length = len(current_word)
        self.history = word_history.copy()

        # Filter words that meet basic criteria
        candidates = []
        for word in self.dictionary:
            word_lower = word.lower()
            if word_lower in self.history:
                continue
            if len(word_lower) == current_length:
                continue
            if required_first not in word_lower or required_last not in word_lower:
                continue
            if word_lower.startswith(required_first) or word_lower.endswith(required_first):
                continue
            if word_lower.startswith(required_last) or word_lower.endswith(required_last):
                continue

            # Calculate potential score
            length = len(word_lower)
            has_hyphen = '-' in word_lower
            has_bonus = (required_first + required_last in word_lower) or (required_last + required_first in word_lower)

            base_score = length
            if has_hyphen:
                base_score = length / 2
            if has_bonus:
                base_score *= 5

            candidates.append((base_score, word_lower))

        if not candidates:
            return None  # No valid move found

        # Sort by score descending, then by length descending
        candidates.sort(key=lambda x: (-x[0], -len(x[1])))

        # Select the best candidate
        best_word = candidates[0][1]

        # Try to find a word that's harder for opponent (optional strategy)
        # Look for words that end with less common letters
        common_endings = {'e', 's', 'd', 't', 'n', 'y'}
        for score, word in candidates:
            last_char = word[-1].lower()
            if last_char not in common_endings:
                best_word = word
                break

        return best_word
