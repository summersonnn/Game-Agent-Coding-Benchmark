"""
Agent Code: A4-WordFinder
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:10:12
"""



import random


class WordFinderAgent:
    """
    WordFinder AI agent.
    """

    def __init__(self, name):
        self.name = name
        # load the dictionary (lowercase)
        self.dictionary = load_words()

        # index words by each letter they contain (for fast lookup)
        self.words_by_letter = {chr(i): set() for i in range(ord('a'), ord('z') + 1)}
        for w in self.dictionary:
            # add the word to the sets of all distinct letters it contains
            for ch in set(w):
                self.words_by_letter[ch].add(w)

    # -----------------------------------------------------------------
    # scoring helpers
    # -----------------------------------------------------------------
    def _score_word(self, word, req1, req2):
        """
        Compute the points earned by playing `word` when the previous word
        required letters req1 (first) and req2 (last).
        """
        # base points: full length, or half length if hyphenated
        base = len(word) // 2 if '-' in word else len(word)

        # consecutive bonus: if req1+req2 or req2+req1 appears in the word
        if (req1 + req2) in word or (req2 + req1) in word:
            base *= 2

        return base

    # -----------------------------------------------------------------
    # partial‑move helper (last resort)
    # -----------------------------------------------------------------
    def _find_partial(self, letter, other, prev_word, history):
        """
        Return the shortest word that contains `letter` but NOT `other`,
        does not start or end with `letter`, has a different length from
        prev_word and is not already used.  Returns None if none exists.
        """
        best = None
        best_len = None
        prev_len = len(prev_word)

        for w in self.words_by_letter[letter]:
            if w in history:
                continue
            if len(w) == prev_len:
                continue
            # must not start or end with the required letter
            if w[0] == letter or w[-1] == letter:
                continue
            # must not contain the other required letter at all
            if other in w:
                continue

            # valid partial move – prefer the shortest (smallest penalty)
            if best_len is None or len(w) < best_len:
                best = w
                best_len = len(w)
                if best_len == 1:          # can't get shorter
                    break

        return best

    # -----------------------------------------------------------------
    # main move logic
    # -----------------------------------------------------------------
    def make_move(self, current_word, word_history):
        # ensure lower‑case
        current_word = current_word.lower()
        req1 = current_word[0]
        req2 = current_word[-1]

        # ----- full move: find a word that contains BOTH required letters -----
        # intersect the two sets of words that contain each required letter
        candidates = self.words_by_letter[req1] & self.words_by_letter[req2]

        best_word = None
        best_score = -1
        best_len = -1

        prev_len = len(current_word)

        for w in candidates:
            if w in word_history:
                continue
            if len(w) == prev_len:
                continue
            # required letters must not be the first or last character
            if w[0] == req1 or w[0] == req2:
                continue
            if w[-1] == req1 or w[-1] == req2:
                continue

            score = self._score_word(w, req1, req2)

            # keep the best according to score, then length, then random
            if (score > best_score) or (score == best_score and len(w) > best_len):
                best_score = score
                best_len = len(w)
                best_word = w
            elif score == best_score and len(w) == best_len:
                # tiny random tie‑breaker
                if random.random() < 0.5:
                    best_word = w

        if best_word is not None:
            return best_word

        # ----- no full move possible – try a partial move (last resort) -----
        # try the two possible “single‑letter” options
        partial = self._find_partial(req1, req2, current_word, word_history)
        if partial is not None:
            return partial

        partial = self._find_partial(req2, req1, current_word, word_history)
        if partial is not None:
            return partial

        # ----- extremely rare fallback: pick any unused word of different length -----
        # (this will most likely be penalised, but prevents a crash)
        for w in self.dictionary:
            if w not in word_history and len(w) != prev_len:
                return w

        # ultimate fallback – should never be reached
        return "a"
