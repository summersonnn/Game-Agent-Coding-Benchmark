"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-5.2
Run: 1
Generated: 2026-02-13 23:22:56
"""

import string

import random
import string

# The game framework is expected to provide this.
# from your_game_module import load_words


class WordMatrixAgent:
    """
    A safe, reasonably fast agent.

    Strategy (simple + robust):
    - Enumerate many valid board paths (length 2..MAX_PATH_LEN).
    - Prefer moves that clear many cells (best when word == path string).
    - If no exact word exists for a path string, try creating a dictionary word
      by inserting 1 (optionally 2) extra letters into the path string.
      (This guarantees the path letters are a subsequence of the word.)
    - If no valid move found, return "PASS" (never intentionally risk invalid).
    """

    def __init__(self, name: str):
        self.name = name
        self.dictionary = load_words()  # must be a set of lowercase words

        # Precompute adjacency on a 4x4 grid (indices 0..15).
        self._neighbors = [[] for _ in range(16)]
        for r in range(4):
            for c in range(4):
                i = 4 * r + c
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 4 and 0 <= nc < 4:
                        self._neighbors[i].append(4 * nr + nc)

        self._idx_to_rc = [(i // 4, i % 4) for i in range(16)]

        # Tuning knobs
        self.MAX_PATH_LEN = 7  # keep runtime stable; 7 already yields many paths
        self.MEMBERSHIP_BUDGET = 80_000  # max dict lookups per move (soft cap)

        # Common letters to try when inserting extras (higher hit-rate than full a-z)
        self.COMMON_INSERT_LETTERS = "etaoinshrdlucm"  # ~English frequency order

        # Deterministic tie-breaking randomness per agent name
        self._rng = random.Random((hash(name) & 0xFFFFFFFF) ^ 0xA5A5A5A5)

    def make_move(self, board, scores, total_passes):
        try:
            letters = self._flatten_board(board)
            non_empty = [i for i, ch in enumerate(letters) if ch]

            # Need at least 2 non-empty cells to form a valid path of length >= 2
            if len(non_empty) < 2:
                return "PASS"

            # Quick "no moves" check: no adjacent pair of non-empty cells
            if not self._has_adjacent_non_empty(letters, non_empty):
                return "PASS"

            max_len = min(self.MAX_PATH_LEN, len(non_empty))

            # If the game is about to end due to passes/fails, try a bit harder.
            # - Broaden insertion alphabet
            # - Allow 2 extra letters (more expensive)
            desperate = total_passes >= 4
            insert_alphabet = string.ascii_lowercase if desperate else self.COMMON_INSERT_LETTERS
            max_extra = 2 if desperate else 1

            # Membership lookup budget to keep move time bounded.
            budget = [self.MEMBERSHIP_BUDGET]
            def in_dict(w: str) -> bool:
                if budget[0] <= 0:
                    return False
                budget[0] -= 1
                return w in self.dictionary

            # Cache within this move: path_string -> best word (or None)
            local_cache = {}

            best = None
            best_key = None  # tuple for comparisons

            # Stack-based DFS over paths.
            # State: (current_idx, visited_mask, path_tuple, path_string)
            stack = []
            for start in non_empty:
                stack.append((start, 1 << start, (start,), letters[start]))

            while stack and budget[0] > 0:
                cur, mask, path, s = stack.pop()
                L = len(path)

                if L >= 2:
                    w = self._best_word_for_path_string(
                        s, in_dict=in_dict, cache=local_cache,
                        insert_alphabet=insert_alphabet, max_extra=max_extra
                    )
                    if w is not None:
                        # cleared = 2*L - len(w)  (since extras = len(w)-L)
                        cleared = 2 * L - len(w)
                        if cleared >= 0:
                            score = 10 + 10 * cleared
                            key = (score, cleared, L, -len(w))
                            if (best_key is None) or (key > best_key) or (key == best_key and self._rng.random() < 0.5):
                                best_key = key
                                best = (path, w)

                                # Upper bound if word == path and L == max_len:
                                # score = 10 + 10*L; cannot beat 10 + 10*max_len.
                                if score == 10 + 10 * max_len and len(w) == L:
                                    break

                if L == max_len:
                    continue

                # Extend path
                for nb in self._neighbors[cur]:
                    if not letters[nb]:
                        continue
                    bit = 1 << nb
                    if mask & bit:
                        continue
                    stack.append((nb, mask | bit, path + (nb,), s + letters[nb]))

            if best is None:
                return "PASS"

            path_indices, word = best
            path_coords = [self._idx_to_rc[i] for i in path_indices]
            return (path_coords, word)

        except Exception:
            # Never crash: return PASS instead.
            return "PASS"

    # -----------------------
    # Helpers
    # -----------------------

    def _flatten_board(self, board):
        """
        Returns a length-16 list of letters ('' for empty), validating lightly.
        """
        letters = []
        # Defensive: handle malformed boards gracefully.
        if not isinstance(board, list) or len(board) != 4:
            return [""] * 16
        for r in range(4):
            row = board[r]
            if not isinstance(row, list) or len(row) != 4:
                letters.extend([""] * 4)
                continue
            for c in range(4):
                ch = row[c]
                if isinstance(ch, str) and len(ch) == 1 and "a" <= ch <= "z":
                    letters.append(ch)
                else:
                    # treat everything else (including "") as empty
                    letters.append("")
        return letters

    def _has_adjacent_non_empty(self, letters, non_empty_indices):
        non_empty_set = set(non_empty_indices)
        for i in non_empty_indices:
            for nb in self._neighbors[i]:
                if nb in non_empty_set:
                    return True
        return False

    def _best_word_for_path_string(self, s, *, in_dict, cache, insert_alphabet, max_extra):
        """
        Find a dictionary word w such that:
          - s is a subsequence of w (guaranteed here by constructing w via insertions)
          - len(s) <= len(w) <= 2*len(s)
        Preference order: 0 extra letters, then 1, then 2 (if enabled).
        """
        if s in cache:
            return cache[s]

        L = len(s)

        # Extra = 0: exact match
        if in_dict(s):
            cache[s] = s
            return s

        # Extra = 1: single insertion anywhere
        if max_extra >= 1 and (L + 1) <= 2 * L:
            for i in range(L + 1):
                pre, post = s[:i], s[i:]
                for ch in insert_alphabet:
                    w = pre + ch + post
                    if in_dict(w):
                        cache[s] = w
                        return w

        # Extra = 2: two insertions anywhere (expensive; only when "desperate")
        if max_extra >= 2 and (L + 2) <= 2 * L:
            # Two-step insertion (may generate duplicates; budget limits keep it safe)
            for i in range(L + 1):
                pre, post = s[:i], s[i:]
                for ch1 in insert_alphabet:
                    w1 = pre + ch1 + post
                    # Now insert second char into w1
                    for j in range(len(w1) + 1):
                        pre2, post2 = w1[:j], w1[j:]
                        for ch2 in insert_alphabet:
                            w2 = pre2 + ch2 + post2
                            if in_dict(w2):
                                cache[s] = w2
                                return w2

        cache[s] = None
        return None
