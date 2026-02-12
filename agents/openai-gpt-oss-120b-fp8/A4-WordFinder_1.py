"""
Agent Code: A4-WordFinder
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-12 10:20:03
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    """
    WordFinder agent that selects the longest valid word,
    preferring those that give the consecutive‑letter bonus.
    """
    def __init__(self, name):
        self.name = name
        # full dictionary supplied by the game environment
        self.dictionary = load_words()                     # set of lowercase words

        # ------------------------------------------------------------------
        # Pre‑computed information for fast move generation
        # ------------------------------------------------------------------
        # word -> (first, last, length, has_hyphen, internal_set, internal_str)
        self.info = {}

        # (letter1,letter2) unordered pair  -> list of words that contain BOTH
        # letters somewhere **inside** the word (not at the ends)
        self.pair_to_words = defaultdict(list)

        # single letter -> list of words that contain this letter inside
        self.letter_to_words = defaultdict(list)

        for w in self.dictionary:
            # words shorter than 3 can never satisfy the “inside” rule
            if len(w) < 3:
                continue

            first, last = w[0], w[-1]
            internal = w[1:-1]
            internal_set = set(internal)
            has_hyphen = '-' in w
            self.info[w] = (first, last, len(w), has_hyphen, internal_set, internal)

            # store for every unordered pair of internal letters
            letters = list(internal_set)
            for i in range(len(letters)):
                for j in range(i, len(letters)):
                    a, b = letters[i], letters[j]
                    key = tuple(sorted((a, b)))          # unordered pair
                    self.pair_to_words[key].append(w)

            # store for each single internal letter
            for ch in internal_set:
                self.letter_to_words[ch].append(w)

        # sort candidate lists once – longest words first (higher base points)
        for lst in self.pair_to_words.values():
            lst.sort(key=lambda x: self.info[x][2], reverse=True)
        for lst in self.letter_to_words.values():
            lst.sort(key=lambda x: self.info[x][2], reverse=True)

    # ----------------------------------------------------------------------
    # Helper utilities
    # ----------------------------------------------------------------------
    @staticmethod
    def _consecutive_inside(word: str, a: str, b: str) -> bool:
        """
        Return True if 'ab' or 'ba' occurs completely inside the word
        (i.e. the first character of the pair is not at position 0
        and the second character is not at the last position).
        """
        # need at least 4 letters to have an internal pair
        if len(word) < 4:
            return False
        for i in range(1, len(word) - 2):          # i … i+1 are both internal
            if (word[i] == a and word[i + 1] == b) or \
               (word[i] == b and word[i + 1] == a):
                return True
        return False

    # ----------------------------------------------------------------------
    # Core move logic
    # ----------------------------------------------------------------------
    def make_move(self, current_word, word_history):
        """
        Choose the best legal word according to the current game state.
        """
        a, b = current_word[0], current_word[-1]          # required letters
        key = tuple(sorted((a, b)))                       # unordered pair

        best_word = None
        best_score = -1.0

        # --------------------------------------------------------------
        # 1) Try to find a full‑match word (contains BOTH required letters)
        # --------------------------------------------------------------
        candidates = self.pair_to_words.get(key, [])
        for w in candidates:
            if w in word_history:
                continue
            first, last, length, has_hyphen, internal_set, _ = self.info[w]

            # length must differ from previous word
            if length == len(current_word):
                continue

            # required letters may NOT be at the start or end of the new word
            if first == a or first == b or last == a or last == b:
                continue

            # (the pair‑to‑words map already guarantees both letters are internal)

            # compute points
            score = float(length)
            if has_hyphen:
                score /= 2.0
            if self._consecutive_inside(w, a, b):
                score *= 2.0

            if score > best_score:
                best_score = score
                best_word = w

            # because lists are sorted by length, we can break early
            # once we have found a word with the maximum possible base length.
            # However we keep scanning to catch a possible consecutive‑pair bonus
            # on a slightly shorter word.
        if best_word:
            return best_word

        # --------------------------------------------------------------
        # 2) No full match – fall back to a partial move (one required letter)
        # --------------------------------------------------------------
        # try each required letter separately, longest possible word first
        for req in (a, b):
            for w in self.letter_to_words.get(req, []):
                if w in word_history:
                    continue
                first, last, length, has_hyphen, internal_set, _ = self.info[w]

                if length == len(current_word):
                    continue
                if first == a or first == b or last == a or last == b:
                    continue
                # word must contain at least one of the required letters internally;
                # it may also (by accident) contain the other – that's fine.
                # This is a partial move because we already know no word contains both.
                return w

        # --------------------------------------------------------------
        # 3) If even a partial move cannot be found, return an empty string.
        #    The game engine will treat it as an invalid move (penalty),
        #    but this situation should be extremely rare.
        # --------------------------------------------------------------
        return ""
