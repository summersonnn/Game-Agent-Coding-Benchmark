"""
Agent Code: A4-WordFinder
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-17 14:14:06
"""

from collections import defaultdict

class WordFinderAgent:
    """
    WordFinderAgent for the WordFinder game.

    Strategy summary:
    - Precompute, for each dictionary word:
      - length, hyphen flag, set of interior adjacent 2-char substrings
      - index words by characters that appear in interior positions (not at word start or end)
    - On each move:
      1. Try to find any valid full-move words that contain BOTH required letters in interior.
         - Score each candidate using the game's scoring formula (hyphen penalty and consecutive-letter bonus).
         - Select the candidate with highest expected points; tie-break by making the opponent's next required letters as difficult as possible
           (heuristic: minimize the number of words that contain the opponent's required letters in interior).
      2. If no full move exists, attempt a partial move (contains exactly one required letter in interior and NOT the other letter anywhere).
         - Choose a partial word minimizing the expected penalty (shorter and hyphenated words preferred).
      3. If no partial move is available, fall back to a short unused dictionary word (best-effort).
    """
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # provided by the environment; set of lowercase words

        # Metadata per word
        self.word_len = {}
        self.has_hyphen = {}
        # interior_adj[w] = set of two-char substrings that occur fully in the interior of w (i.e., both chars not at start or end)
        self.interior_adj = {}

        # char_interior_map[c] = set of words where character c appears in interior and is NOT equal to the word's first or last character
        self.char_interior_map = defaultdict(set)

        # Build indices
        for w in self.dictionary:
            n = len(w)
            self.word_len[w] = n
            self.has_hyphen[w] = ('-' in w)

            # interior adjacency substrings (both chars strictly in interior positions)
            if n >= 4:
                adj = set()
                # interior-adjacent pairs: i from 1 .. n-3 inclusive => range(1, n-2)
                for i in range(1, n - 2):
                    adj.add(w[i : i + 2])
                self.interior_adj[w] = adj
            else:
                self.interior_adj[w] = set()

            # interior-valid characters: appear in w[1:-1] and are not equal to first or last char
            if n >= 3:
                first, last = w[0], w[-1]
                interior = w[1:-1]
                # use set to avoid duplicate insertions
                interior_valid_set = {ch for ch in set(interior) if ch != first and ch != last}
                for ch in interior_valid_set:
                    self.char_interior_map[ch].add(w)

        # Precompute counts for heuristic (how many words have a character in interior)
        self.char_interior_count = {ch: len(s) for ch, s in self.char_interior_map.items()}

    def make_move(self, current_word, word_history):
        a = current_word[0]
        b = current_word[-1]
        cw_len = len(current_word)

        # Helper to compute effective (positive) score for a word given required letters a,b
        def effective_score_for_word(w, req_a, req_b):
            n = self.word_len[w]
            hy = self.has_hyphen[w]
            adj = self.interior_adj.get(w, set())
            if req_a == req_b:
                consecutive = (req_a + req_a) in adj
            else:
                consecutive = (req_a + req_b) in adj or (req_b + req_a) in adj
            base = (n / 2.0) if hy else float(n)
            final = base * 2.0 if consecutive else base
            return final

        # 1) Try full-move candidates: words that contain BOTH a and b in interior (and do NOT have a or b at start/end)
        if a == b:
            cand_set = set(self.char_interior_map.get(a, set()))
        else:
            set_a = self.char_interior_map.get(a, set())
            set_b = self.char_interior_map.get(b, set())
            if not set_a or not set_b:
                cand_set = set()
            else:
                # intersect smaller into larger for speed
                if len(set_a) < len(set_b):
                    cand_set = {w for w in set_a if w in set_b}
                else:
                    cand_set = {w for w in set_b if w in set_a}

        # Filter out words already used and those with the same length as current word.
        full_candidates = []
        for w in cand_set:
            if w in word_history:
                continue
            if self.word_len[w] == cw_len:
                continue
            # safety: required letters must not appear at start or end of candidate (indexing step ensured this, but double-check)
            if w[0] == a or w[-1] == a or w[0] == b or w[-1] == b:
                continue
            full_candidates.append(w)

        if full_candidates:
            # Evaluate full candidates and pick best by effective score. Tie-break by minimizing opponent's options.
            best_score = -float("inf")
            best_candidates = []
            for w in full_candidates:
                score = effective_score_for_word(w, a, b)
                if score > best_score:
                    best_score = score
                    best_candidates = [w]
                elif score == best_score:
                    best_candidates.append(w)

            if len(best_candidates) == 1:
                return best_candidates[0]

            # Tie-breaker: choose candidate that gives the opponent the fewest interior options for their required letters
            best_choice = None
            best_avail = float("inf")
            for w in best_candidates:
                next_first, next_last = w[0], w[-1]
                # approximate opponent availability by sum of interior counts for the two letters (lower is better)
                avail = self.char_interior_count.get(next_first, 0) + self.char_interior_count.get(next_last, 0)
                if avail < best_avail:
                    best_avail = avail
                    best_choice = w
                elif avail == best_avail:
                    # further tie-break: prefer longer word (gives more points)
                    if best_choice is None or self.word_len[w] > self.word_len[best_choice]:
                        best_choice = w
            # If still None improbable, pick random
            return best_choice if best_choice is not None else random.choice(best_candidates)

        # 2) No full move possible -> attempt a partial move (contains exactly one required letter in interior, and does NOT contain the other letter anywhere)
        partial_best = None
        partial_best_val = float("inf")  # minimize expected penalty magnitude

        # Consider words containing 'a' but not 'b', and vice versa
        for letter, other in ((a, b), (b, a)):
            for w in self.char_interior_map.get(letter, set()):
                if w in word_history:
                    continue
                if self.word_len[w] == cw_len:
                    continue
                # The other required letter must NOT appear anywhere in the word
                if other in w:
                    continue
                # This qualifies as a partial move. Choose one minimizing expected penalty.
                # Use the same base scoring function but note no consecutive bonus (only one letter present), and hyphen reduces penalty.
                eff = (self.word_len[w] / 2.0) if self.has_hyphen[w] else float(self.word_len[w])
                if eff < partial_best_val:
                    partial_best_val = eff
                    partial_best = w
                elif eff == partial_best_val:
                    # tie-break: prefer one that leaves opponent fewer options (heuristic)
                    prev = partial_best
                    if prev is None:
                        partial_best = w
                    else:
                        avail_w = self.char_interior_count.get(w[0], 0) + self.char_interior_count.get(w[-1], 0)
                        avail_prev = self.char_interior_count.get(prev[0], 0) + self.char_interior_count.get(prev[-1], 0)
                        if avail_w < avail_prev:
                            partial_best = w
                        elif avail_w == avail_prev and self.word_len[w] > self.word_len[prev]:
                            partial_best = w

        if partial_best is not None:
            return partial_best

        # 3) As a last resort, return a short unused word (best-effort). This may be invalid if truly no partial/full moves exist.
        fallback = None
        min_len = float("inf")
        for w in self.dictionary:
            if w in word_history:
                continue
            lw = self.word_len.get(w, len(w))
            if lw == cw_len:
                continue
            if lw < min_len:
                min_len = lw
                fallback = w
                if min_len <= 3:
                    break
        if fallback is not None:
            return fallback

        # If everything used (very unlikely), pick any word (will be handled by the engine)
        return random.choice(list(self.dictionary))
