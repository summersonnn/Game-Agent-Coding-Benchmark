"""
Agent Code: A4-WordFinder
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-12 09:30:10
"""

import math

import math


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # provided by environment

        self.words = list(self.dictionary)
        self.n = len(self.words)

        self._a_ord = ord("a")
        self._z_ord = ord("z")
        self._alpha = "abcdefghijklmnopqrstuvwxyz"
        self._idx = {c: i for i, c in enumerate(self._alpha)}

        # Per-word cached features
        self._mask = [0] * self.n  # 26-bit mask of letters allowed as "required" (present, and NOT at word ends)
        self._first = [""] * self.n
        self._last = [""] * self.n
        self._len = [0] * self.n
        self._base = [0.0] * self.n  # length with hyphen penalty applied (len or len/2)
        self._def_bonus = [0.0] * self.n  # defensive bonus based on (first,last) difficulty

        # For each letter, list of word-ids where that letter can be used as a required letter
        self._by_letter = [[] for _ in range(26)]

        for wid, w in enumerate(self.words):
            if not w:
                continue
            self._first[wid] = w[0]
            self._last[wid] = w[-1]
            L = len(w)
            self._len[wid] = L
            self._base[wid] = (L * 0.5) if ("-" in w) else float(L)

            banned0 = w[0]
            banned1 = w[-1]

            m = 0
            # A letter is usable as a required letter iff it appears in the word and
            # is NOT equal to the word's first or last character (rule 2).
            for ch in w:
                o = ord(ch)
                if self._a_ord <= o <= self._z_ord and ch != banned0 and ch != banned1:
                    m |= 1 << (o - self._a_ord)

            self._mask[wid] = m
            if m:
                # Populate per-letter index
                mm = m
                while mm:
                    lsb = mm & -mm
                    i = (lsb.bit_length() - 1)
                    self._by_letter[i].append(wid)
                    mm ^= lsb

        # Precompute pair counts for defensive heuristic: how many words exist for each (req_first, req_last)
        self._pair_count = [[0] * 26 for _ in range(26)]
        for wid in range(self.n):
            m = self._mask[wid]
            if not m:
                continue
            letters = []
            mm = m
            while mm:
                lsb = mm & -mm
                letters.append(lsb.bit_length() - 1)
                mm ^= lsb
            for i in letters:
                row = self._pair_count[i]
                for j in letters:
                    row[j] += 1

        # Defensive bonus per word depends on opponent's required pair = (our first, our last)
        # Smaller pair_count => harder for opponent => bigger bonus.
        self._DEF_SCALE = 18.0
        for wid in range(self.n):
            f = self._first[wid]
            l = self._last[wid]
            if f in self._idx and l in self._idx:
                c = self._pair_count[self._idx[f]][self._idx[l]]
                self._def_bonus[wid] = self._DEF_SCALE / (c + 1.0)
            else:
                self._def_bonus[wid] = 0.0

        # Sort per-letter lists by a static desirability score to find good moves quickly.
        # (Exact scoring still considers consecutive-letter bonus, which depends on current required letters.)
        self._static = [self._base[wid] + self._def_bonus[wid] for wid in range(self.n)]
        for i in range(26):
            self._by_letter[i].sort(key=self._static.__getitem__, reverse=True)

        # For partial-move selection (minimize penalty): per-letter lists sorted by length (then no-hyphen preference)
        self._by_letter_short = [[] for _ in range(26)]
        for i in range(26):
            self._by_letter_short[i] = sorted(
                self._by_letter[i],
                key=lambda wid: (self._len[wid], "-" in self.words[wid], -self._def_bonus[wid]),
            )

        # Limits to keep make_move fast
        self._MAX_SCAN = 50000
        self._MAX_CAND_EVAL = 800

    @staticmethod
    def _has_consecutive_bonus(word, a, b):
        if a == b:
            return (a + a) in word
        return (a + b) in word or (b + a) in word

    def _best_full_move(self, a, b, prev_len, history):
        if a not in self._idx or b not in self._idx:
            return None

        ia = self._idx[a]
        ib = self._idx[b]
        list_a = self._by_letter[ia]
        list_b = self._by_letter[ib]

        if a == b:
            source = list_a
            other_bit = 1 << ia
        else:
            # Scan the smaller candidate list first, filter by other letter via bitmask.
            if len(list_a) <= len(list_b):
                source = list_a
                other_bit = 1 << ib
            else:
                source = list_b
                other_bit = 1 << ia

        best_w = None
        best_score = -1e18

        scanned = 0
        evaluated = 0

        for wid in source:
            scanned += 1
            if scanned > self._MAX_SCAN and best_w is not None:
                break

            w = self.words[wid]
            if w in history:
                continue
            if self._len[wid] == prev_len:
                continue

            m = self._mask[wid]
            if (m & other_bit) == 0:
                continue

            score = self._base[wid]
            if self._has_consecutive_bonus(w, a, b):
                score *= 2.0
            score += self._def_bonus[wid]

            if score > best_score:
                best_score = score
                best_w = w

            evaluated += 1
            if evaluated >= self._MAX_CAND_EVAL and best_w is not None:
                break

        return best_w

    def _best_partial_move(self, a, b, prev_len, history):
        # Choose a short word containing exactly one of {a,b} as an allowed required letter.
        # (We enforce "other letter not present at all" to ensure it's truly partial.)
        candidates = []
        if a in self._idx:
            candidates.append((a, b, self._by_letter_short[self._idx[a]]))
        if b in self._idx and b != a:
            candidates.append((b, a, self._by_letter_short[self._idx[b]]))

        best_w = None
        best_val = -1e18  # higher is better (less negative penalty, more defensive)
        for keep, forbid, lst in candidates:
            scanned = 0
            for wid in lst:
                scanned += 1
                if scanned > 8000 and best_w is not None:
                    break

                w = self.words[wid]
                if w in history:
                    continue
                if self._len[wid] == prev_len:
                    continue
                if forbid in w:
                    continue

                # Heuristic for partial: minimize likely negative points -> prefer shorter (and no hyphen),
                # but still consider defensive bonus.
                penalty = self._base[wid]  # proportional to length (hyphen already discounted)
                val = (-penalty) + 0.8 * self._def_bonus[wid]
                if val > best_val:
                    best_val = val
                    best_w = w

                if best_w is not None and self._len[wid] <= 4:
                    # Usually can't do better than very short for partial
                    break

        return best_w

    def make_move(self, current_word, word_history):
        if not current_word:
            # Fallback: pick any unused word (should rarely happen)
            for w in self.words:
                if w not in word_history:
                    return w
            return "a"

        cw = current_word.lower()
        a = cw[0]
        b = cw[-1]
        prev_len = len(cw)

        # 1) Full move (contains BOTH required letters, obeys constraints)
        best = self._best_full_move(a, b, prev_len, word_history)
        if best is not None:
            return best

        # 2) Partial move (contains exactly ONE required letter), last resort
        partial = self._best_partial_move(a, b, prev_len, word_history)
        if partial is not None:
            return partial

        # 3) Absolute fallback to avoid crashing (may be invalid, but better than timeout/crash)
        for w in self.words:
            if w not in word_history and len(w) != prev_len:
                return w
        return next(iter(self.dictionary))
