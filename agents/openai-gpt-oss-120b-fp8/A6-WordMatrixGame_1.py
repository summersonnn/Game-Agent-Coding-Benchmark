"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-oss-120b@preset/fp8
Run: 1
Generated: 2026-02-13 22:39:54
"""

import os
import re
from collections import defaultdict
from typing import List, Tuple, Union

# --------------------------------------------------------------
#  WordMatrixAgent – a simple but effective player for the
#  4×4 “WordMatrixGame (Simplified)”.
#
#  What it does
#  -------------
#  * Loads the supplied dictionary once (≈ 466 k words) and stores it
#    in a few convenient data‑structures:
#        – a set for O(1) exact‑match look‑ups,
#        – a dict that groups words by length (helps when we need a
#          word that is longer than the path),
#        – a compiled‑regex cache (optional, speeds up the “sub‑seq”
#          search a little).
#
#  * On every call to ``make_move`` it enumerates **all** legal paths
#    on the current board (length 2 … MAX_PATH_LEN).  Because the board
#    is only 4×4 the total number of paths is tiny (a few thousand at
#    most) and a brute‑force search is perfectly fine.
#
#  * For each path it first checks whether the letters on the path
#    already form a dictionary word (the *perfect* move – clears every
#    cell of the path).  If a perfect move exists we return the first
#    one we find.
#
#  * If no perfect move exists we look for the *best* longer word.
#    “Best’’ means:
#        – minimise the number of extra letters (len(word)‑len(path)),
#        – if several candidates have the same number of extras,
#          prefer the longer path (more cells cleared → more points).
#
#  * If no legal move can be found the agent simply returns ``\"PASS\"``.
#
#  The code is deliberately written to be easy to read and modify.
# --------------------------------------------------------------

import os
import re
from collections import defaultdict
from typing import List, Tuple, Union

# ----------------------------------------------------------------------
# Helper – load the dictionary (the environment that runs the game must
# provide a file called ``words.txt`` in the same directory; each line
# contains one lower‑case word).
# ----------------------------------------------------------------------
def load_words() -> set:
    """
    Load the word list that the competition supplies.
    Returns a set of lower‑case words.
    """
    # The exact location of the dictionary is not prescribed in the spec.
    # The usual convention for these sandbox games is a file called
    # ``words.txt`` placed next to the source file.
    path = os.path.join(os.path.dirname(__file__), "words.txt")
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


# ----------------------------------------------------------------------
# Core agent
# ----------------------------------------------------------------------
class WordMatrixAgent:
    """
    A deterministic, rule‑following agent for the 4×4 Word‑Matrix game.
    """

    # The longest path we ever need to examine.
    # A path longer than 6 cells would already allow a word up to length 12,
    # but the board only has 16 cells, so 6 is a safe compromise between
    # completeness and speed.
    MAX_PATH_LEN = 6

    # Directions for orthogonal (no diagonal) moves.
    _DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def __init__(self, name: str):
        self.name = name

        # --------------------------------------------------------------
        # 1️⃣  Load and index the dictionary
        # --------------------------------------------------------------
        self.dictionary: set = load_words()

        # Group words by length – this makes the “search for a longer word”
        # step very cheap because we only iterate over the relevant lengths.
        self.words_by_len: defaultdict[int, List[str]] = defaultdict(list)
        for w in self.dictionary:
            self.words_by_len[len(w)].append(w)

        # Pre‑compile a simple cache for regexes that we will generate
        # from path strings (e.g. "c.*a.*t").
        self._regex_cache: dict = {}

    # ------------------------------------------------------------------
    # Public API – called by the game engine
    # ------------------------------------------------------------------
    def make_move(
        self,
        board: List[List[str]],
        scores: dict,
        total_passes: int,
    ) -> Union[Tuple[List[Tuple[int, int]], str], str]:
        """
        Return a legal move or 'PASS'.

        Parameters
        ----------
        board : 4×4 list of lists containing either a lower‑case letter or
                the empty string "".
        scores : dict with the two players' current scores.
        total_passes : number of consecutive PASS / invalid / timeout moves
                       that have already happened.

        Returns
        -------
        (path, word)  where ``path`` is a list of (row, col) tuples
        or the string ``'PASS'``.
        """
        # --------------------------------------------------------------
        # 2️⃣  Enumerate every legal path on the board (length >= 2)
        # --------------------------------------------------------------
        all_paths = self._enumerate_paths(board)

        # Keep track of the *best* candidate we have seen so far.
        # A tuple (extra_letters, -path_len, path, word) is used for easy
        # comparison: fewer extras is better; for a tie a longer path is
        # preferred.
        best_candidate = None  # type: Union[None, Tuple[int, int, List[Tuple[int, int]], str]]

        for path in all_paths:
            path_letters = "".join(board[r][c] for r, c in path)

            # ---------------------------------------------------------
            # a)  Perfect move – word length == path length
            # ---------------------------------------------------------
            if path_letters in self.dictionary:
                # Immediate return – this clears every cell of the path,
                # which yields the maximum possible points for this path.
                return (path, path_letters)

            # ---------------------------------------------------------
            # b)  Look for longer words (len = path_len + 1 … 2*path_len)
            # ---------------------------------------------------------
            path_len = len(path)
            min_len = path_len + 1
            max_len = min(2 * path_len, max(self.words_by_len.keys()))
            # Build a regex that forces the path letters to appear as a
            # subsequence (e.g. "c.*a.*t").
            regex = self._get_regex_for_path(path_letters)

            # Iterate only over the word lengths that are allowed.
            for wlen in range(min_len, max_len + 1):
                for cand in self.words_by_len.get(wlen, []):
                    if regex.fullmatch(cand):
                        extra = wlen - path_len       # number of extra letters
                        candidate = (extra, -path_len, path, cand)
                        if (best_candidate is None) or (candidate < best_candidate):
                            best_candidate = candidate
                        # We cannot break here – a word of the same length but
                        # with fewer extras does not exist, but a *different*
                        # path might give 0 extras (which we would have caught
                        # earlier).  Still, once we have found a word with
                        # extra == 1 we could stop scanning longer lengths,
                        # but the board is tiny, so we keep it simple.

        # --------------------------------------------------------------
        # 3️⃣  Return the best candidate we discovered (if any)
        # --------------------------------------------------------------
        if best_candidate is not None:
            _, _, path, word = best_candidate
            return (path, word)

        # --------------------------------------------------------------
        # 4️⃣  No legal move → PASS
        # --------------------------------------------------------------
        return "PASS"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _enumerate_paths(self, board: List[List[str]]) -> List[List[Tuple[int, int]]]:
        """
        Return a list of all legal paths (length >= 2) on the current board.
        A path is a list of (row, col) tuples.
        """
        rows, cols = 4, 4
        paths: List[List[Tuple[int, int]]] = []

        def dfs(r: int, c: int, visited: List[Tuple[int, int]]):
            if len(visited) >= 2:
                # Record a copy – the caller may modify the list later.
                paths.append(visited.copy())

            if len(visited) == self.MAX_PATH_LEN:
                return

            for dr, dc in self._DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if board[nr][nc] == "":
                        continue                    # cannot step on empty cell
                    if (nr, nc) in visited:
                        continue                    # cannot reuse a cell
                    visited.append((nr, nc))
                    dfs(nr, nc, visited)
                    visited.pop()

        for r in range(rows):
            for c in range(cols):
                if board[r][c] == "":
                    continue
                dfs(r, c, [(r, c)])

        return paths

    def _get_regex_for_path(self, letters: str) -> re.Pattern:
        """
        Build (or fetch from cache) a regex that matches any word that
        contains ``letters`` as a subsequence, preserving order.
        Example: letters = "cat"  →  pattern "^c.*a.*t$"
        """
        if letters in self._regex_cache:
            return self._regex_cache[letters]

        # Escape any regex‑special characters that might appear in the word
        # list (unlikely for pure lower‑case letters, but safe).
        escaped = [re.escape(ch) for ch in letters]
        pattern = "^" + ".*".join(escaped) + "$"
        compiled = re.compile(pattern)
        self._regex_cache[letters] = compiled
        return compiled


# ----------------------------------------------------------------------
#  Example of how the agent could be instantiated and used (not part of
#  the required answer, just for illustration):
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # A tiny board for quick manual testing.
    test_board = [
        ["c", "a", "t", "s"],
        ["d", "o", "g", ""],
        ["p", "e", "n", ""],
        ["",  "",  "",  ""],
    ]

    agent = WordMatrixAgent(name="SimpleAgent")
    move = agent.make_move(test_board, {"Agent-1": 0, "Agent-2": 0}, total_passes=0)
    print("Chosen move:", move)
