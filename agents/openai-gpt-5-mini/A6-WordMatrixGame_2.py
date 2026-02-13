"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-5-mini
Run: 2
Generated: 2026-02-12 19:13:59
"""

import sys

import sys

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize the agent.
        load_words() must be available and return an iterable of lowercase words.
        """
        self.name = name
        self.dictionary = set(load_words())  # set for O(1) membership checks
        # Limit depth of path search to keep runtime reasonable
        self.max_search_len = 8
        self._build_prefixes()

    def _build_prefixes(self):
        """
        Build a set of prefixes (up to max_search_len) to prune DFS branches.
        """
        max_pref = self.max_search_len
        prefixes = set()
        for w in self.dictionary:
            limit = min(len(w), max_pref)
            for i in range(1, limit + 1):
                prefixes.add(w[:i])
        self.prefix_set = prefixes

    def make_move(self, board, scores, total_passes):
        """
        Return either "PASS" or a tuple (path, word).
        path: list of (row, col) coordinates (must be length >= 2)
        word: lowercase string present in the dictionary, and equal to the concatenation
              of the letters along 'path' (so subsequence requirement is satisfied
              and len(word) == len(path) => maximum clear for that path).
        """
        try:
            # Safety: ensure recursion can handle our DFS depth
            sys.setrecursionlimit(10000)

            R = len(board)
            C = len(board[0]) if R > 0 else 0

            best_len = 0
            best_path = None
            best_word = None

            def in_bounds(r, c):
                return 0 <= r < R and 0 <= c < C

            # DFS from each non-empty cell
            for r0 in range(R):
                for c0 in range(C):
                    ch0 = board[r0][c0]
                    if not ch0:
                        continue
                    start_mask = 1 << (r0 * C + c0)

                    def dfs(r, c, s, path, visited_mask):
                        nonlocal best_len, best_path, best_word
                        # prune by maximum allowed length
                        if len(s) > self.max_search_len:
                            return
                        # prune by prefix: if no dictionary word starts with 's', stop
                        if s not in self.prefix_set:
                            return
                        # valid candidate if it's a dictionary word and length >= 2
                        if len(s) >= 2 and s in self.dictionary:
                            if len(s) > best_len:
                                best_len = len(s)
                                best_path = list(path)
                                best_word = s
                                # if we've reached the search limit, it's the best possible here
                                # (can't find longer than max_search_len)
                        # explore neighbors (up/down/left/right)
                        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                            if not in_bounds(nr, nc):
                                continue
                            pos = nr * C + nc
                            if visited_mask & (1 << pos):
                                continue
                            ch = board[nr][nc]
                            if not ch:
                                continue
                            dfs(nr, nc, s + ch, path + [(nr, nc)], visited_mask | (1 << pos))

                    dfs(r0, c0, ch0, [(r0, c0)], start_mask)
                    if best_len == self.max_search_len:
                        break
                if best_len == self.max_search_len:
                    break

            if best_path is not None and len(best_path) >= 2:
                # Return the found path and word (exact match -> clears all cells in the path)
                return (best_path, best_word)

            # No suitable exact contiguous word found; pass safely
            return "PASS"

        except Exception:
            # Never crash the agent — prefer a safe PASS
            return "PASS"
