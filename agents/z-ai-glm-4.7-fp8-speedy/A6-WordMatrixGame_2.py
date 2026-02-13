"""
Agent Code: A6-WordMatrixGame
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-13 22:39:54
"""

import itertools

import itertools
import random

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        # Load dictionary
        words = load_words()                     # returns set of words
        self.word_set = words

        # ---------- Precompute maps for extra‑letter moves ----------
        # Sort words by length so that the first time we see a subsequence
        # we store the shortest word.
        word_list = sorted(self.word_set, key=len)

        self.pair_map   = {}   # key: 2‑letter string -> shortest word (len 2‑4)
        self.triple_map = {}   # key: 3‑letter string -> shortest word (len 3‑6)
        self.quad_map   = {}   # key: 4‑letter string -> shortest word (len 4‑8)

        for w in word_list:
            lw = len(w)
            # pairs
            if lw <= 4:
                for i, j in itertools.combinations(range(lw), 2):
                    seq = w[i] + w[j]
                    if seq not in self.pair_map:
                        self.pair_map[seq] = w
            # triples
            if 3 <= lw <= 6:
                for i, j, k in itertools.combinations(range(lw), 3):
                    seq = w[i] + w[j] + w[k]
                    if seq not in self.triple_map:
                        self.triple_map[seq] = w
            # quadruples
            if 4 <= lw <= 8:
                for idxs in itertools.combinations(range(lw), 4):
                    seq = ''.join(w[i] for i in idxs)
                    if seq not in self.quad_map:
                        self.quad_map[seq] = w

        # ---------- Precompute neighbours for the 4x4 grid ----------
        self.neighbours = [[] for _ in range(16)]
        for idx in range(16):
            r, c = divmod(idx, 4)
            for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
                nr, nc = r+dr, c+dc
                if 0 <= nr < 4 and 0 <= nc < 4:
                    self.neighbours[idx].append(nr*4 + nc)

        # ---------- Popcount table for all 16‑bit masks ----------
        self.popcount = [bin(i).count('1') for i in range(1<<16)]

    # -----------------------------------------------------------------
    def make_move(self, board, scores, total_passes):
        # Flatten the board to a list of 16 strings (empty string for empty cells)
        flat = []
        for r in range(4):
            for c in range(4):
                flat.append(board[r][c])

        # If no two adjacent non‑empty cells exist, we must pass
        if not self._has_adjacent_nonempty(flat):
            return "PASS"

        # 1) Try to find the longest exact word (path spells the word)
        best_exact = self._longest_exact_word(flat)
        if best_exact is not None:
            return best_exact

        # 2) If no exact word, try extra‑letter moves for lengths 2‑4
        best_extra = self._best_extra_move(flat)
        if best_extra is not None:
            return best_extra

        # 3) Nothing valid
        return "PASS"

    # -----------------------------------------------------------------
    def _has_adjacent_nonempty(self, flat):
        """Return True if there exists a pair of adjacent non‑empty cells."""
        for i in range(16):
            if flat[i] == "":
                continue
            r, c = divmod(i, 4)
            # right neighbour
            if c < 3 and flat[i+1] != "":
                return True
            # down neighbour
            if r < 3 and flat[i+4] != "":
                return True
        return False

    # -----------------------------------------------------------------
    def _longest_exact_word(self, flat):
        """DFS to find the longest word that can be formed exactly by a path.
        Returns (path, word) or None."""
        best_len = 0
        best_path = None
        best_word = None

        starts = [i for i in range(16) if flat[i] != ""]

        # Recursive DFS with backtracking
        def dfs(idx, visited, cur_chars, cur_path):
            nonlocal best_len, best_path, best_word

            # Check if current string is a word
            if len(cur_chars) >= 2:
                s = ''.join(cur_chars)
                if s in self.word_set and len(s) > best_len:
                    best_len = len(s)
                    best_path = cur_path.copy()
                    best_word = s

            # Prune: even if we could visit all remaining cells we cannot beat best_len
            if len(cur_chars) + (16 - self.popcount[visited]) <= best_len:
                return

            # Extend to neighbours
            for nb in self.neighbours[idx]:
                if not (visited & (1 << nb)):
                    cur_chars.append(flat[nb])
                    cur_path.append(nb)
                    dfs(nb, visited | (1 << nb), cur_chars, cur_path)
                    cur_path.pop()
                    cur_chars.pop()

        for start in starts:
            dfs(start, 1 << start, [flat[start]], [start])

        if best_len > 0:
            # Convert indices to (row, col) tuples
            path_coords = [(i//4, i%4) for i in best_path]
            return (path_coords, best_word)
        return None

    # -----------------------------------------------------------------
    def _best_extra_move(self, flat):
        """Generate all paths of length 2‑4 and look for the shortest word
        that contains the path as a subsequence using the precomputed maps.
        Returns the move with the highest score, or None."""
        best_score = -1
        best_move = None

        starts = [i for i in range(16) if flat[i] != ""]

        def dfs(idx, visited, cur_path):
            nonlocal best_score, best_move
            L = len(cur_path)
            if L >= 2:
                s = ''.join(flat[i] for i in cur_path)
                word = None
                if L == 2:
                    word = self.pair_map.get(s)
                elif L == 3:
                    word = self.triple_map.get(s)
                elif L == 4:
                    word = self.quad_map.get(s)

                if word is not None:
                    Wlen = len(word)
                    score = 10 + 10 * (2*L - Wlen)   # cleared = 2L - Wlen
                    if score > best_score:
                        best_score = score
                        path_coords = [(i//4, i%4) for i in cur_path]
                        best_move = (path_coords, word)

            if L == 4:          # we only need up to length 4
                return

            for nb in self.neighbours[idx]:
                if not (visited & (1 << nb)):
                    dfs(nb, visited | (1 << nb), cur_path + [nb])

        for start in starts:
            dfs(start, 1 << start, [start])

        return best_move
