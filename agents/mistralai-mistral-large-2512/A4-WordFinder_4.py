"""
Agent Code: A4-WordFinder
Model: mistralai/mistral-large-2512
Run: 4
Generated: 2026-02-05 00:14:02
"""



import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Precompute some useful data structures
        self.word_lengths = {}
        for word in self.dictionary:
            length = len(word)
            if length not in self.word_lengths:
                self.word_lengths[length] = []
            self.word_lengths[length].append(word)

    def make_move(self, current_word, word_history):
        required_first = current_word[0].lower()
        required_last = current_word[-1].lower()
        current_length = len(current_word)
        used_words = set(word.lower() for word in word_history)

        # Find all candidate words that meet the basic requirements
        candidates = []
        for word in self.dictionary:
            # Skip used words
            if word in used_words:
                continue

            # Check length constraint
            if len(word) == current_length:
                continue

            # Check letter constraints
            if required_first not in word or required_last not in word:
                continue

            # Check position constraints
            if word[0] == required_first or word[-1] == required_first:
                continue
            if word[0] == required_last or word[-1] == required_last:
                continue

            # Check if the word contains both letters consecutively (bonus potential)
            has_consecutive = False
            for i in range(len(word) - 1):
                if (word[i] == required_first and word[i+1] == required_last) or \
                   (word[i] == required_last and word[i+1] == required_first):
                    has_consecutive = True
                    break

            # Calculate base score
            if '-' in word:
                base_score = len(word) // 2
            else:
                base_score = len(word)

            # Apply bonus if applicable
            if has_consecutive:
                score = base_score * 5
            else:
                score = base_score

            candidates.append((score, word, has_consecutive))

        # Sort candidates by score (descending) and length (descending for same score)
        candidates.sort(key=lambda x: (-x[0], -len(x[1])))

        # Try to select the best candidate
        for score, word, has_consecutive in candidates:
            # Additional check to ensure the word hasn't been used (in case of case sensitivity)
            if word not in used_words:
                return word

        # If no valid word found, return None (game will end)
        return None
