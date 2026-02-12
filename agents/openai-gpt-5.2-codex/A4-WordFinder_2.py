"""
Agent Code: A4-WordFinder
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-12 09:30:10
"""


from collections import defaultdict, Counter


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # Provided by game environment

        # Keep normalized words only
        self.words = []
        self.word_set = set()
        for w in self.dictionary:
            if not isinstance(w, str):
                continue
            ww = w.strip().lower()
            if len(ww) >= 3:
                self.words.append(ww)
                self.word_set.add(ww)

        # Frequency of edge letters (used for defensive tie-breaking)
        edge_counter = Counter()
        for w in self.words:
            edge_counter[w[0]] += 1
            edge_counter[w[-1]] += 1
        self.edge_counter = edge_counter
        self.max_edge_freq = max(edge_counter.values()) if edge_counter else 1

        # Precompute static metadata and indexes for fast turn-time lookups
        self.meta = {}
        self.pair_index = defaultdict(list)    # key: (min_char, max_char) -> words
        self.single_index = defaultdict(list)  # key: char -> words (char appears internally)

        for w in self.words:
            internal = w[1:-1]
            internal_chars = set(internal)
            first = w[0]
            last = w[-1]
            has_hyphen = "-" in w
            length = len(w)

            self.meta[w] = {
                "len": length,
                "first": first,
                "last": last,
                "has_hyphen": has_hyphen,
                "internal_chars": internal_chars,
            }

            # Single-letter partial index
            for c in internal_chars:
                if first != c and last != c:
                    self.single_index[c].append(w)

            # Full-move pair index (unordered pair)
            chars = list(internal_chars)
            n = len(chars)
            for i in range(n):
                a = chars[i]
                if first != a and last != a:
                    self.pair_index[(a, a)].append(w)
                for j in range(i + 1, n):
                    b = chars[j]
                    if first != a and last != a and first != b and last != b:
                        key = (a, b) if a <= b else (b, a)
                        self.pair_index[key].append(w)

        # Sort indexed candidate lists with a static quality heuristic
        def static_rank(word):
            m = self.meta[word]
            base = m["len"] // 2 if m["has_hyphen"] else m["len"]
            defense = (
                (self.max_edge_freq - self.edge_counter[m["first"]]) +
                (self.max_edge_freq - self.edge_counter[m["last"]])
            )
            return (base, defense, m["len"])

        for k in list(self.pair_index.keys()):
            self.pair_index[k].sort(key=static_rank, reverse=True)
        for k in list(self.single_index.keys()):
            self.single_index[k].sort(key=static_rank, reverse=True)

    @staticmethod
    def _pair_key(a, b):
        return (a, b) if a <= b else (b, a)

    @staticmethod
    def _has_consecutive_bonus(word, req1, req2):
        if req1 == req2:
            return (req1 + req1) in word
        return (req1 + req2) in word or (req2 + req1) in word

    def _score_word(self, word, req1, req2):
        m = self.meta[word]
        points = m["len"] // 2 if m["has_hyphen"] else m["len"]
        if self._has_consecutive_bonus(word, req1, req2):
            points *= 2
        defense = (
            (self.max_edge_freq - self.edge_counter[m["first"]]) +
            (self.max_edge_freq - self.edge_counter[m["last"]])
        )
        return points, defense, m["len"]

    def _valid_full_move(self, word, req1, req2, prev_len, used):
        if word in used:
            return False
        m = self.meta[word]
        if m["len"] == prev_len:
            return False
        if m["first"] in (req1, req2) or m["last"] in (req1, req2):
            return False
        # Must contain BOTH required chars somewhere
        if req1 not in word or req2 not in word:
            return False
        # Each required char must appear internally (not only at edges)
        if req1 not in word[1:-1] or req2 not in word[1:-1]:
            return False
        return True

    def _valid_partial_move(self, word, req1, req2, prev_len, used):
        if word in used:
            return False
        m = self.meta[word]
        if m["len"] == prev_len:
            return False
        if m["first"] in (req1, req2) or m["last"] in (req1, req2):
            return False

        in1 = req1 in word[1:-1]
        in2 = req2 in word[1:-1]
        # Must contain exactly one required letter internally
        if in1 == in2:
            return False
        # And must not contain the other required letter anywhere
        if in1 and req2 in word:
            return False
        if in2 and req1 in word:
            return False
        return True

    def make_move(self, current_word, word_history):
        # Normalize game inputs
        current = (current_word or "").strip().lower()
        if len(current) < 2:
            # Emergency fallback: safest available long-ish word
            used = {w.lower() for w in word_history}
            for w in self.words:
                if w not in used:
                    return w
            return "the"

        req1 = current[0]
        req2 = current[-1]
        prev_len = len(current)
        used = {w.lower() for w in word_history}

        # 1) Try full valid move first
        best_word = None
        best_score = None
        key = self._pair_key(req1, req2)
        candidates = self.pair_index.get(key, [])

        for w in candidates:
            if not self._valid_full_move(w, req1, req2, prev_len, used):
                continue
            s = self._score_word(w, req1, req2)
            if best_score is None or s > best_score:
                best_score = s
                best_word = w

        if best_word is not None:
            return best_word

        # 2) Last resort: partial move (one required letter only)
        partial_best = None
        partial_score = None

        for req, other in ((req1, req2), (req2, req1)):
            for w in self.single_index.get(req, []):
                if not self._valid_partial_move(w, req, other, prev_len, used):
                    continue
                s = self._score_word(w, req1, req2)
                if partial_score is None or s > partial_score:
                    partial_score = s
                    partial_best = w

        if partial_best is not None:
            return partial_best

        # 3) Absolute emergency fallback to avoid crashing
        for w in self.words:
            if w not in used:
                return w
        return "the"