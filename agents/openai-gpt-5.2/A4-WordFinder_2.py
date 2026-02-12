"""
Agent Code: A4-WordFinder
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-12 09:30:10
"""

import heapq
from collections import defaultdict

import random
import heapq
from collections import defaultdict


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # provided by environment

        # Tunables (picked to be safe on time/memory across many turns)
        self.TOPK_PER_PAIR = 900          # store up to this many "good" words per required-letter pair
        self.TOPK_PARTIAL_PER_CHAR = 1400 # store up to this many short partial-move candidates per letter
        self.DEFENSE_WEIGHT = 0.75        # how much to value making opponent's next pair hard
        self.DEFENSE_SCALE = 12.0         # scale for defense term
        self.MAX_EVAL = 350               # max candidates to evaluate deeply (with bonus check) per move

        self.words = list(self.dictionary)
        self.n = len(self.words)

        self.starts = [w[0] if w else "" for w in self.words]
        self.ends = [w[-1] if w else "" for w in self.words]
        self.lens = [len(w) for w in self.words]
        self.has_hyphen = [("-" in w) for w in self.words]
        # Base points used by the engine are unknown to us; for ranking, follow spec examples (floor on half points).
        self.base_points = [(len(w) // 2 if ("-" in w) else len(w)) for w in self.words]

        # Build a compact internal-character mask for fast membership checks.
        self.char_to_bit = {}
        self._internal_mask = [0] * self.n

        # Pair availability counts (for defensive play) under the strict "full move" constraints:
        # required letters are internal AND neither required letter appears at the word's start or end.
        self.pair_counts = defaultdict(int)

        # Pass 1: build internal masks and pair_counts
        for i, w in enumerate(self.words):
            if len(w) < 3:
                continue
            internal = w[1:-1]
            if not internal:
                continue
            internal_set = set(internal)

            # mask + bit assignment
            m = 0
            for ch in internal_set:
                b = self.char_to_bit.get(ch)
                if b is None:
                    b = len(self.char_to_bit)
                    self.char_to_bit[ch] = b
                m |= (1 << b)
            self._internal_mask[i] = m

            s = self.starts[i]
            e = self.ends[i]
            lst = sorted(internal_set)
            for ia, a in enumerate(lst):
                for b in lst[ia:]:
                    if s == a or s == b or e == a or e == b:
                        continue
                    self.pair_counts[(a, b)] += 1

        # Helpers for defensive evaluation
        def pair_key(a, b):
            return (a, b) if a <= b else (b, a)

        # Pass 2: keep only top-K candidates per pair, and top-K shortest candidates per char for partial moves
        pair_heaps = defaultdict(list)     # key -> min-heap of (quality, base_points, idx)
        partial_heaps = defaultdict(list)  # char -> min-heap of (-len, defense, idx) (so we can pop longest/worst)

        for i, w in enumerate(self.words):
            if len(w) < 3:
                continue
            internal = w[1:-1]
            if not internal:
                continue
            internal_set = set(internal)
            if not internal_set:
                continue

            s = self.starts[i]
            e = self.ends[i]
            next_k = pair_key(s, e)
            next_count = self.pair_counts.get(next_k, 0)
            defense = self.DEFENSE_SCALE / (1 + next_count)

            base = self.base_points[i]
            quality = base + self.DEFENSE_WEIGHT * defense

            # Partial move index: words that contain ch internally and do not start/end with ch
            L = self.lens[i]
            for ch in internal_set:
                if s == ch or e == ch:
                    continue
                h = partial_heaps[ch]
                heapq.heappush(h, (-L, defense, i))
                if len(h) > self.TOPK_PARTIAL_PER_CHAR:
                    heapq.heappop(h)  # removes longest; for ties removes smaller defense first

            # Full move index: for every unordered pair inside internal_set, if neither letter is at start/end
            lst = sorted(internal_set)
            for ia, a in enumerate(lst):
                for b in lst[ia:]:
                    if s == a or s == b or e == a or e == b:
                        continue
                    k = (a, b)  # already sorted due to lst ordering
                    h = pair_heaps[k]
                    heapq.heappush(h, (quality, base, i))
                    if len(h) > self.TOPK_PER_PAIR:
                        heapq.heappop(h)

        # Freeze heaps into sorted candidate lists (best first)
        self.pair_candidates = {}
        for k, h in pair_heaps.items():
            h.sort(reverse=True)  # sort by (quality, base, idx)
            self.pair_candidates[k] = [idx for (_, _, idx) in h]

        self.partial_candidates = {}
        for ch, h in partial_heaps.items():
            # h stores (-len, defense, idx); sort by shortest length then highest defense
            h.sort(key=lambda t: (-t[0], -t[1]))
            self.partial_candidates[ch] = [idx for (_, _, idx) in h]

    @staticmethod
    def _pair_key(a, b):
        return (a, b) if a <= b else (b, a)

    @staticmethod
    def _bonus_applies(word, a, b):
        # Bonus needs the two required letters consecutive, and both not at the word edges.
        # Checking within [1, len(word)-2) via find(..., 1, len(word)-1) ensures both letters are internal.
        if len(word) < 4:
            return False
        end = len(word) - 1
        if a == b:
            return word.find(a + a, 1, end) != -1
        return (word.find(a + b, 1, end) != -1) or (word.find(b + a, 1, end) != -1)

    def _bit(self, ch):
        b = self.char_to_bit.get(ch)
        if b is None:
            return 0
        return 1 << b

    def make_move(self, current_word, word_history):
        cw = (current_word or "").lower()
        if not cw:
            # Extremely defensive fallback; should not happen in normal games.
            for w in self.words:
                if w not in word_history:
                    return w
            return "a"

        a = cw[0]
        b = cw[-1]
        prev_len = len(cw)
        key = self._pair_key(a, b)

        # Try full move from precomputed top candidates for this required pair.
        cand = self.pair_candidates.get(key, [])
        best_word = None
        best_score = None

        # Precompute bits for fast internal membership checks in partial search (full search is pre-filtered)
        bit_a = self._bit(a)
        bit_b = self._bit(b)

        evald = 0
        for idx in cand:
            w = self.words[idx]
            if w in word_history:
                continue
            if self.lens[idx] == prev_len:
                continue

            # Compute actual points including consecutive-bonus (we already included hyphen floor in base_points)
            pts = self.base_points[idx]
            if self._bonus_applies(w, a, b):
                pts *= 2

            # Defensive term based on how many full-move options exist for opponent's next required pair
            next_key = self._pair_key(w[0], w[-1])
            next_count = self.pair_counts.get(next_key, 0)
            defense = self.DEFENSE_SCALE / (1 + next_count)
            total = pts + self.DEFENSE_WEIGHT * defense

            if best_score is None or total > best_score:
                best_score = total
                best_word = w

            evald += 1
            if evald >= self.MAX_EVAL and best_word is not None:
                # Candidates are already high-quality; stop early.
                break

        if best_word is not None:
            return best_word

        # No full move found from our cached top list.
        # Attempt a partial move: a word that contains exactly one of {a,b} internally,
        # and does not start/end with either required letter, and length differs.
        def is_valid_partial(idx, want_a):
            w = self.words[idx]
            if w in word_history:
                return False
            if self.lens[idx] == prev_len:
                return False
            if not w:
                return False
            if w[0] == a or w[-1] == a or w[0] == b or w[-1] == b:
                return False

            m = self._internal_mask[idx]
            has_a = (m & bit_a) != 0
            has_b = (m & bit_b) != 0

            if a == b:
                # "Partial" doesn't really make sense if required letters are identical; just need internal 'a'
                return has_a
            return (has_a and not has_b) if want_a else (has_b and not has_a)

        # Choose the least-damaging partial (shortest), among candidates for a or b.
        best_partial = None
        best_partial_len = None
        for want_a, ch in ((True, a), (False, b)):
            for idx in self.partial_candidates.get(ch, []):
                if is_valid_partial(idx, want_a):
                    L = self.lens[idx]
                    if best_partial is None or L < best_partial_len:
                        best_partial = self.words[idx]
                        best_partial_len = L
                    break  # shortest for this letter-list found; no need to keep scanning

        if best_partial is not None:
            return best_partial

        # Slow fallback: scan some random unused words to at least avoid an invalid move if possible.
        # Try to find any word containing a or b internally (not at edges), with differing length.
        # (This is still "partial" if it doesn't contain both letters internally.)
        tries = 2500
        for _ in range(tries):
            w = self.words[random.randrange(self.n)]
            if w in word_history:
                continue
            if len(w) == prev_len or len(w) < 3:
                continue
            if w[0] == a or w[-1] == a or w[0] == b or w[-1] == b:
                continue
            m = self._internal_mask[self.words.index(w)] if False else None  # avoid O(n) index lookup

            internal = w[1:-1]
            if (a in internal) or (b in internal):
                return w

        # Absolute last resort (likely -10 invalid, but avoid crash/timeout).
        for w in self.words:
            if w not in word_history:
                return w
        return "a"
