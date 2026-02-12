"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-coder@preset/fp8
Run: 2
Generated: 2026-02-12 09:31:57
"""



import random


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.precomputed = self._precompute_words()

    def _precompute_words(self):
        # Precompute a mapping from (char_pair, length) -> list of words
        # where char_pair is a frozenset of two characters
        mapping = {}
        for word in self.dictionary:
            if '-' in word:
                continue  # We prefer non-hyphenated words
            if len(word) < 3:
                continue  # Words with length < 3 are not useful
            chars = set(word)
            key = (frozenset(chars), len(word))
            if key not in mapping:
                mapping[key] = []
            mapping[key].append(word)
        return mapping

    def _find_consecutive_words(self, first_char, last_char, current_length, word_history):
        # Try to find words where first_char and last_char appear consecutively
        candidates = []
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            if '-' in word:
                continue
            if first_char not in word or last_char not in word:
                continue
            if word[0] == first_char or word[-1] == first_char:
                continue
            if word[0] == last_char or word[-1] == last_char:
                continue
            # Check for consecutive
            found = False
            for i in range(len(word) - 1):
                if (word[i] == first_char and word[i+1] == last_char) or \
                   (word[i] == last_char and word[i+1] == first_char):
                    found = True
                    break
            if found:
                candidates.append((len(word), word))
        candidates.sort(reverse=True)
        return [word for _, word in candidates]

    def _find_valid_words(self, first_char, last_char, current_length, word_history):
        # Try to find any valid word (not necessarily consecutive)
        candidates = []
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            if first_char not in word or last_char not in word:
                continue
            if word[0] == first_char or word[-1] == first_char:
                continue
            if word[0] == last_char or word[-1] == last_char:
                continue
            # Prefer longer words
            candidates.append((len(word), word))
        candidates.sort(reverse=True)
        return [word for _, word in candidates]

    def _find_partial_words(self, first_char, last_char, current_length, word_history):
        # Find words with at least one of the required letters (partial move)
        candidates = []
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            # Must contain one of the required letters, but not at start or end
            has_first = first_char in word and word[0] != first_char and word[-1] != first_char
            has_last = last_char in word and word[0] != last_char and word[-1] != last_char
            if not (has_first or has_last):
                continue
            # Prefer longer words (even though it's a penalty)
            candidates.append((len(word), word))
        candidates.sort(reverse=True)
        return [word for _, word in candidates]

    def make_move(self, current_word, word_history):
        current_word_lower = current_word.lower()
        first_char = current_word_lower[0]
        last_char = current_word_lower[-1]
        current_length = len(current_word_lower)

        # First try to find a word with consecutive letters
        consecutive_words = self._find_consecutive_words(first_char, last_char, current_length, word_history)
        if consecutive_words:
            return consecutive_words[0]

        # Then try any valid word
        valid_words = self._find_valid_words(first_char, last_char, current_length, word_history)
        if valid_words:
            return valid_words[0]

        # Last resort: partial move
        partial_words = self._find_partial_words(first_char, last_char, current_length, word_history)
        if partial_words:
            return partial_words[0]

        # If we get here, something is very wrong; just return a random word to avoid crash
        return random.choice(list(self.dictionary - word_history)) if self.dictionary - word_history else "example"
