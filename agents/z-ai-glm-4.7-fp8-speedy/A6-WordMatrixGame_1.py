"""
Agent Code: A6-WordMatrixGame
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-13 22:39:54
"""

from typing import List, Tuple, Dict, Set, Optional

import random
from typing import List, Tuple, Dict, Set, Optional

# Provided function (assumed available)
def load_words() -> Set[str]:
    """Return a set of ~466k lowercase English words."""
    # In the actual environment this function is provided.
    # For completeness we include a dummy implementation; it will be replaced.
    return set()

class WordMatrixAgent:
    def __init__(self, name: str):
        self.name = name

        # 1. Load dictionary and keep only words that can ever be used (length <= 32)
        raw_words = load_words()
        self.word_set = {w for w in raw_words if len(w) <= 32}

        # 2. Group words by length for fast iteration
        self.words_by_length = [[] for _ in range(33)]  # index = length, up to 32
        for w in self.word_set:
            self.words_by_length[len(w)].append(w)

        # 3. Pre‑compute maps for patterns of length 2, 3, 4
        self.pair_map = {}   # pattern (2 letters) -> shortest word (len 2..4)
        self.trip_map = {}   # pattern (3 letters) -> shortest word (len 3..6)
        self.quad_map = {}   # pattern (4 letters) -> shortest word (len 4..8)

        self._build_pair_map()
        self._build_trip_map()
        self._build_quad_map()

        # 4. Cache for longer patterns (length 5 or 6)
        self.subseq_cache = {}

    # -----------------------------------------------------------------
    # Map building helpers
    # -----------------------------------------------------------------
    def _build_pair_map(self):
        for L in range(2, 5):          # words of length 2,3,4
            for word in self.words_by_length[L]:
                # generate all ordered pairs
                for i in range(L):
                    for j in range(i+1, L):
                        pat = word[i] + word[j]
                        if pat not in self.pair_map or len(word) < len(self.pair_map[pat]):
                            self.pair_map[pat] = word

    def _build_trip_map(self):
        for L in range(3, 7):          # words of length 3,4,5,6
            for word in self.words_by_length[L]:
                for i in range(L):
                    for j in range(i+1, L):
                        for k in range(j+1, L):
                            pat = word[i] + word[j] + word[k]
                            if pat not in self.trip_map or len(word) < len(self.trip_map[pat]):
                                self.trip_map[pat] = word

    def _build_quad_map(self):
        for L in range(4, 9):          # words of length 4,5,6,7,8
            for word in self.words_by_length[L]:
                for i in range(L):
                    for j in range(i+1, L):
                        for k in range(j+1, L):
                            for l in range(k+1, L):
                                pat = word[i] + word[j] + word[k] + word[l]
                                if pat not in self.quad_map or len(word) < len(self.quad_map[pat]):
                                    self.quad_map[pat] = word

    # -----------------------------------------------------------------
    # Subsequence test
    # -----------------------------------------------------------------
    @staticmethod
    def _is_subsequence(sub: str, s: str) -> bool:
        """Return True if `sub` is a subsequence of `s`."""
        i = 0
        for ch in s:
            if i < len(sub) and ch == sub[i]:
                i += 1
        return i == len(sub)

    # -----------------------------------------------------------------
    # Find shortest word containing a given pattern (cached)
    # -----------------------------------------------------------------
    def _find_shortest_word_containing(self, pat: str) -> Optional[str]:
        """Return the shortest word (len between len(pat) and 2*len(pat))
           that has `pat` as a subsequence, or None if none exists."""
        if pat in self.subseq_cache:
            return self.subseq_cache[pat]

        k = len(pat)
        for L in range(k, 2*k + 1):
            if L > 32:          # we only have words up to length 32
                break
            for word in self.words_by_length[L]:
                if self._is_subsequence(pat, word):
                    self.subseq_cache[pat] = word
                    return word
        self.subseq_cache[pat] = None
        return None

    # -----------------------------------------------------------------
    # Generate all simple paths (adjacent, no repeats, non‑empty cells)
    # -----------------------------------------------------------------
    def _generate_paths(self, board: List[List[str]]) -> List[Tuple[Tuple[Tuple[int, int], ...], str, int]]:
        """Return a list of (coords_tuple, letters_string, length) for all valid paths."""
        rows, cols = 4, 4
        paths = []

        def dfs(r: int, c: int, visited: Set[Tuple[int, int]],
                cur_coords: List[Tuple[int, int]], cur_str: str):
            if len(cur_coords) >= 2:
                paths.append((tuple(cur_coords), cur_str, len(cur_coords)))
            for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
                nr, nc = r+dr, c+dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr,nc) not in visited and board[nr][nc] != "":
                    visited.add((nr,nc))
                    cur_coords.append((nr,nc))
                    dfs(nr, nc, visited, cur_coords, cur_str + board[nr][nc])
                    cur_coords.pop()
                    visited.remove((nr,nc))

        for r in range(rows):
            for c in range(cols):
                if board[r][c] == "":
                    continue
                visited = {(r,c)}
                dfs(r, c, visited, [(r,c)], board[r][c])

        return paths

    # -----------------------------------------------------------------
    # Main decision method
    # -----------------------------------------------------------------
    def make_move(self, board: List[List[str]], scores: Dict[str, int], total_passes: int) -> Tuple[List[Tuple[int, int]], str] or str:
        my_score = scores[self.name]
        opp_score = next(v for k, v in scores.items() if k != self.name)

        # If we are ahead and the game is about to end, pass to secure the win.
        if total_passes >= 5 and my_score > opp_score:
            return "PASS"

        # Generate all possible paths
        paths = self._generate_paths(board)
        if not paths:                     # less than two non‑empty cells
            return "PASS"

        # Sort by length descending – longer paths have higher potential score
        paths.sort(key=lambda x: x[2], reverse=True)

        best_score = -1
        best_move = None

        for coords_tuple, pat, Lp in paths:
            # 1) Exact match (word == path letters)
            if pat in self.word_set:
                score = 10 + 10 * Lp
                if score > best_score:
                    best_score = score
                    best_move = (list(coords_tuple), pat)
                continue      # exact is optimal for this path

            # 2) Patterns of length 2‑4 – use precomputed maps
            if Lp <= 4:
                word = None
                if Lp == 2:
                    word = self.pair_map.get(pat)
                elif Lp == 3:
                    word = self.trip_map.get(pat)
                elif Lp == 4:
                    word = self.quad_map.get(pat)
                if word is not None:
                    cleared = 2 * Lp - len(word)
                    score = 10 + 10 * cleared
                    if score > best_score:
                        best_score = score
                        best_move = (list(coords_tuple), word)

            # 3) Longer patterns (5 or 6) – try to find a word, but prune if hopeless
            elif Lp <= 6:
                # Maximum possible score without an exact match is 10*Lp
                if 10 * Lp <= best_score:
                    continue
                word = self._find_shortest_word_containing(pat)
                if word is not None:
                    cleared = 2 * Lp - len(word)
                    score = 10 + 10 * cleared
                    if score > best_score:
                        best_score = score
                        best_move = (list(coords_tuple), word)

            # Patterns longer than 6 are ignored (probability of a word is negligible)

        if best_move is not None:
            return best_move
        else:
            return "PASS"
