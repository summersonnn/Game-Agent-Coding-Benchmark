"""
Agent Code: A4-WordFinder
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict, Counter

class WordFinderAgent:
    """
    WordFinderAgent implementation that:
    - Precomputes interior-letter and any-letter indexes for fast lookup.
    - Prefers long, non-hyphenated words.
    - Prioritizes words that contain the two required letters consecutively (interior) for the 2x bonus.
    - Avoids returning words that are in word_history, have the same length as current_word,
      or have the required letters at the start or end.
    - Falls back to a partial move (contains exactly one required letter interiorly) if no full valid word exists.
    - As a last resort returns a short unused dictionary word (may be invalid) to avoid crashes.
    """
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # Provided by environment; set of lowercase words

        # Maps char -> set(words) where the char appears anywhere
        self.any_index = defaultdict(set)
        # Maps char -> set(words) where the char appears in an interior position (not first or last)
        self.interior_index = defaultdict(set)

        # Frequency counts for first and last letters (used for defensive tie-breaking)
        self.first_counts = Counter()
        self.last_counts = Counter()

        # Build indexes
        for w in self.dictionary:
            if not w:
                continue
            lw = w  # words are lowercase from load_words()
            self.first_counts[lw[0]] += 1
            self.last_counts[lw[-1]] += 1

            # characters anywhere in the word
            for c in set(lw):
                self.any_index[c].add(lw)

            # interior characters (positions 1..len-2)
            if len(lw) >= 3:
                for c in set(lw[1:-1]):
                    self.interior_index[c].add(lw)

        # Precompute a list of words sorted by increasing length for fallback (short words first)
        self.words_by_short_length = sorted(self.dictionary, key=lambda w: (len(w), w))

    def _has_interior_consecutive_pair(self, word, a, b):
        """Return True if 'ab' or 'ba' occurs such that neither letter is at start/end."""
        L = len(word)
        # Need indices i and i+1 such that i >= 1 and i+1 <= L-2 -> i in [1, L-3]
        # If L < 4 it's impossible for a consecutive interior pair to satisfy the position constraint.
        if L < 4:
            return False
        for i in range(1, L - 2 + 1):  # up to L-3 inclusive
            c1, c2 = word[i], word[i + 1]
            if (c1 == a and c2 == b) or (c1 == b and c2 == a):
                return True
        return False

    def _estimate_score(self, word, a, b):
        """Estimate effective points for choosing 'word' given required letters a,b.
        This uses integer math consistent with game description: hyphen halves by integer division,
        and consecutive interior pair doubles the resulting base points.
        """
        base = len(word)
        if '-' in word:
            base = base // 2
        if self._has_interior_consecutive_pair(word, a, b):
            base = base * 2
        return base

    def _pick_best_from(self, candidates, a, b, current_len, used):
        """Select the best candidate by estimated score, break ties defensively using first+last frequency."""
        best_score = -1
        best_words = []
        for w in candidates:
            # additional safety checks (some may slip through indexes)
            if w in used:
                continue
            if len(w) == current_len:
                continue
            # required letters must NOT be at start or end of the new word
            if w[0] == a or w[-1] == a or w[0] == b or w[-1] == b:
                continue
            score = self._estimate_score(w, a, b)
            if score > best_score:
                best_score = score
                best_words = [w]
            elif score == best_score:
                best_words.append(w)

        if not best_words:
            return None

        # tie-breaker: choose word whose first+last letter frequency is minimal (defensive)
        def difficulty_metric(word):
            return self.first_counts.get(word[0], 0) + self.last_counts.get(word[-1], 0)

        best_words.sort(key=lambda w: (difficulty_metric(w), -len(w), w))
        # choose randomly among the top few with identical metrics to add variety
        top_metric = difficulty_metric(best_words[0])
        top_len = len(best_words[0])
        top_group = [w for w in best_words if difficulty_metric(w) == top_metric and len(w) == top_len]
        return random.choice(top_group)

    def make_move(self, current_word, word_history):
        try:
            cur = (current_word or "").lower()
            used = set(w.lower() for w in word_history) if word_history is not None else set()
            if not cur:
                # If for some reason current_word is empty, return a short unused word
                for w in self.words_by_short_length:
                    if w not in used:
                        return w
                # fallback
                return random.choice(list(self.dictionary))

            a, b = cur[0], cur[-1]
            current_len = len(cur)

            # 1) Try to find full valid words that contain BOTH required letters in interior positions
            set_a = self.interior_index.get(a, set())
            set_b = self.interior_index.get(b, set())
            full_candidates = set_a & set_b

            best_full = self._pick_best_from(full_candidates, a, b, current_len, used)
            if best_full:
                return best_full

            # 2) No full valid words: try Partial Move = contains EXACTLY ONE of the required letters,
            #    that letter must appear in interior (and the other letter must not appear anywhere).
            partial_candidates = []
            for letter, other in ((a, b), (b, a)):
                for w in self.interior_index.get(letter, set()):
                    if w in used:
                        continue
                    if len(w) == current_len:
                        continue
                    # other letter must NOT appear anywhere in the word
                    if other in w:
                        continue
                    # ensure neither required letter appears at the start or end (rule still applies)
                    if w[0] == a or w[-1] == a or w[0] == b or w[-1] == b:
                        continue
                    partial_candidates.append(w)

            if partial_candidates:
                # minimize length (to reduce negative penalty), then defensive tie-break
                partial_candidates.sort(key=lambda w: (len(w), self.first_counts.get(w[0], 0) + self.last_counts.get(w[-1], 0), w))
                # pick among shortest ones randomly
                min_len = len(partial_candidates[0])
                top_group = [w for w in partial_candidates if len(w) == min_len]
                return random.choice(top_group)

            # 3) Last resort: return a short unused dictionary word (may be invalid).
            for w in self.words_by_short_length:
                if w not in used and len(w) != current_len:
                    return w

            # If everything is used (very unlikely), just return a random dictionary word
            return random.choice(list(self.dictionary))

        except Exception:
            # On any internal error, return a safe random choice to avoid crashing the game loop
            try:
                # prefer a short unused word if possible
                used = set(w.lower() for w in word_history) if word_history is not None else set()
                for w in self.words_by_short_length:
                    if w not in used:
                        return w
                return random.choice(list(self.dictionary))
            except Exception:
                # worst-case fallback
                return "a"
