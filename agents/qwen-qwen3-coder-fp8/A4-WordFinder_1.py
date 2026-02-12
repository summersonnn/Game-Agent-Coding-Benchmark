"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-coder@preset/fp8
Run: 1
Generated: 2026-02-12 09:31:57
"""



import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Precompute a mapping from (first_char, last_char, length) -> list of words
        self.word_map = {}
        for word in self.dictionary:
            if "-" in word:
                continue  # Avoid hyphenated words in precomputation; we can still use them if needed
            fl = word[0]
            ll = word[-1]
            length = len(word)
            key = (fl, ll, length)
            if key not in self.word_map:
                self.word_map[key] = []
            self.word_map[key].append(word)

    def make_move(self, current_word, word_history):
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        current_length = len(current_word)

        # Collect candidate words that satisfy all constraints
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

            # This word satisfies all basic constraints
            consecutive_bonus = 0
            idx_f = word.find(first_char)
            idx_l = word.find(last_char)

            # Check for consecutive occurrence in either order
            for i in range(len(word) - 1):
                if (word[i] == first_char and word[i+1] == last_char) or \
                   (word[i] == last_char and word[i+1] == first_char):
                    consecutive_bonus = 1
                    break

            base_score = len(word)
            if "-" in word:
                base_score //= 2
            if consecutive_bonus:
                base_score *= 2

            candidates.append((base_score, word))

        # Sort candidates by score descending
        candidates.sort(reverse=True)

        # If we have valid candidates, return the best one
        if candidates:
            return candidates[0][1]

        # No valid full move found. Try partial move (fallback).
        # Find words with at least one required letter (not at start/end)
        partial_candidates = []
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            has_first = first_char in word and word[0] != first_char and word[-1] != first_char
            has_last = last_char in word and word[0] != last_char and word[-1] != last_char

            if has_first and not has_last:
                score = -len(word)
                partial_candidates.append((score, word))
            elif has_last and not has_first:
                score = -len(word)
                partial_candidates.append((score, word))

        # Prefer less negative score (i.e., shorter word)
        partial_candidates.sort()

        if partial_candidates:
            return partial_candidates[0][1]

        # Absolute last resort: pick any valid word with one matching letter
        # even if it's slightly invalid in position, just to avoid crash/invalid
        # But according to rules, must not be at start/end.
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            if (first_char in word and word[0] != first_char and word[-1] != first_char) or \
               (last_char in word and word[0] != last_char and word[-1] != last_char):
                return word

        # Final fallback: return any word not in history (should almost never reach here)
        for word in self.dictionary:
            if word not in word_history:
                continue

            length = len(word)
            base_points = length
            if "-" in word:
                base_points = length // 2

            # Check for consecutive bonus
            if first_char + last_char in word or last_char + first_char in word:
                base_points *= 2

            candidates.append((base_points, word))

        # Sort by score descending
        candidates.sort(reverse=True)

        # If we have valid candidates, return the best one
        if candidates:
            return candidates[0][1]

        # If no full valid word found, attempt a partial move
        partial_candidates = []
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == current_length:
                continue
            count = 0
            has_first = first_char in word and word[0] != first_char and word[-1] != first_char
            has_last = last_char in word and word[0] != last_char and word[-1] != last_char
            if has_first:
                count += 1
            if has_last:
                count += 1
            if count == 1:  # Only one required letter
                length = len(word)
                base_points = -length
                partial_candidates.append((base_points, word))

        partial_candidates.sort()  # Negative scores, so sort ascending to get least negative

        if partial_candidates:
            return partial_candidates[0][1]

        # If all else fails, pick any random word that meets length constraint only (will be invalid but avoids crash)
        fallback = [w for w in self.dictionary if len(w) != current_length and w not in word_history]
        if fallback:
            return random.choice(fallback)
        else:
            return "example"  # Last resort fallback
