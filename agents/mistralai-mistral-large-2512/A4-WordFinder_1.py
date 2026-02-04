"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-05 00:14:02
"""



import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Pre-filter dictionary to exclude hyphenated words for faster searching
        self.non_hyphen_words = {word for word in self.dictionary if '-' not in word}

    def make_move(self, current_word, word_history):
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        required_chars = {first_char, last_char}
        required_pair = first_char + last_char
        required_reverse_pair = last_char + first_char
        current_length = len(current_word)

        # We'll prioritize finding words with the bonus first
        candidates = []

        # First try to find words with consecutive bonus letters (5x multiplier)
        for word in self.non_hyphen_words:
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

            # Check for consecutive bonus
            if required_pair in word or required_reverse_pair in word:
                candidates.append((len(word) * 5, word))  # 5x bonus

        # If we found bonus candidates, pick the longest one
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            return candidates[0][1]

        # If no bonus candidates, look for non-hyphenated words
        for word in self.non_hyphen_words:
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
            candidates.append((len(word), word))

        # If we found non-hyphenated candidates, pick the longest one
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            return candidates[0][1]

        # If no non-hyphenated words found, try hyphenated words (with penalty)
        for word in self.dictionary:
            if '-' in word:  # Only consider hyphenated words now
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
                candidates.append((len(word) // 2, word))  # Half points for hyphenated

        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            return candidates[0][1]

        # If no valid words found, return None (game will end)
        return None
