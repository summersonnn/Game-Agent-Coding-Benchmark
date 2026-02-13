"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-13 22:39:54
"""

from typing import List, Tuple, Union, Set

import random
from typing import List, Tuple, Union, Set

# ----------------------------------------------------------------------
# Helper: load the dictionary.
# ----------------------------------------------------------------------
def load_words() -> Set[str]:
    """
    Load the word list used by the game.
    Replace the body of this function with the actual loading logic
    (e.g. reading a file, downloading a resource, etc.).
    The function must return a set of lowercase strings.
    """
    # ----- Example stub -------------------------------------------------
    # For a real game you would load something like:
    #   with open("words.txt") as f:
    #       return {line.strip().lower() for line in f if line.strip()}
    # --------------------------------------------------------------------
    # Here we return a tiny static set so the file can be executed
    # without external resources.  In production replace this with the
    # real dictionary.
    return {
        "cat", "dog", "rat", "art", "cart", "coat", "cater", "carts",
        "taco", "coat", "read", "dear", "dare", "ear", "are", "tea",
        "ate", "eat", "tone", "note", "stone", "scent", "cent", "sent",
        "tent", "net", "ten", "ant", "tan", "bat", "tab", "cab", "abc",
        # … (all other words) …
    }
# ----------------------------------------------------------------------


class WordMatrixAgent:
    """
    A minimal yet functional agent for the Word‑Matrix game.

    The agent looks for an *exact* match between a board path and a dictionary
    word.  Because the word length equals the path length, the move clears every
    cell on the path and yields the highest possible score for that turn
    (10 + 10 × cleared_cells).

    If no such path exists the agent simply PASSes.
    """

    def __init__(self, name: str):
        self.name = name
        # Load the whole dictionary once – O(N) where N ≈ 466k.
        self.dictionary: Set[str] = load_words()

        # Pre‑compute the set of all possible word lengths we might need.
        # The longest path we will ever try is 8 (half of the 4×4 board),
        # but we keep it generous.
        self.max_path_len = 8
        self.allowed_lengths = {
            l for w in self.dictionary for l in (len(w),) if 2 <= l <= self.max_path_len
        }

        # Directions: up, down, left, right (no diagonals)
        self.dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

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
        Return either a (path, word) tuple or the string "PASS".

        Parameters
        ----------
        board : List[List[str]]
            4 × 4 matrix of lowercase letters or empty strings.
        scores : dict
            Current scores, e.g. {"Agent-1": 30, "Agent-2": 10}
        total_passes : int
            Number of consecutive PASS/invalid moves in the game so far.

        Returns
        -------
        Union[Tuple[List[Tuple[int, int]], str], str]
            * (path, word) – a legal move
            * "PASS"      – skip the turn
        """
        # ------------------------------------------------------------------
        # 1️⃣  Gather all non‑empty cells as starting points
        # ------------------------------------------------------------------
        non_empty = [(r, c) for r in range(4) for c in range(4) if board[r][c]]
        if len(non_empty) < 2:
            # No possible path of length ≥2 – we must PASS.
            return "PASS"

        # ------------------------------------------------------------------
        # 2️⃣  Depth‑first search for *any* exact‑match path.
        # ------------------------------------------------------------------
        visited = [[False] * 4 for _ in range(4)]

        def dfs(path: List[Tuple[int, int]]) -> Union[Tuple[List[Tuple[int, int]], str], None]:
            """Recursive DFS that stops as soon as it finds a valid move."""
            # Stop if path already too long for any word in the dictionary.
            if len(path) > self.max_path_len:
                return None

            # Build the string formed by the current path.
            word_candidate = "".join(board[r][c] for r, c in path)

            # Check only when length ≥ 2 (the rule) and when the length is
            # present in the dictionary (fast filter).
            if len(path) >= 2 and len(word_candidate) in self.allowed_lengths:
                if word_candidate in self.dictionary:
                    # Exact match – this is the best possible move.
                    return (list(path), word_candidate)

            # Continue expanding the path.
            r_last, c_last = path[-1]
            for dr, dc in self.dirs:
                nr, nc = r_last + dr, c_last + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and not visited[nr][nc] and board[nr][nc]:
                    visited[nr][nc] = True
                    path.append((nr, nc))
                    result = dfs(path)
                    if result:
                        return result
                    # backtrack
                    path.pop()
                    visited[nr][nc] = False
            return None

        # Try every cell as a start point.
        for sr, sc in non_empty:
            visited[sr][sc] = True
            result = dfs([(sr, sc)])
            visited[sr][sc] = False
            if result:
                return result

        # ------------------------------------------------------------------
        # 3️⃣  No exact‑match found → PASS.
        # ------------------------------------------------------------------
        return "PASS"

    # ------------------------------------------------------------------
    # Optional helper – you can use it later for a “sub‑sequence” search.
    # ------------------------------------------------------------------
    @staticmethod
    def is_subsequence(path_letters: List[str], word: str) -> bool:
        """
        Return True iff the letters in `path_letters` appear in `word`
        in the same order (not necessarily contiguously).
        """
        it = iter(word)
        return all(ch in it for ch in path_letters)


# ----------------------------------------------------------------------
# Example of how the agent would be instantiated and called.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Small demo board (feel free to replace with any 4×4 configuration)
    demo_board = [
        ["c", "a", "t", "s"],
        ["d", "o", "g", "" ],
        ["r", "a", "t", "" ],
        ["",  "",  "",  "" ],
    ]

    agent = WordMatrixAgent(name="ExactMatchBot")
    move = agent.make_move(demo_board, {"Agent-1": 0, "Agent-2": 0}, total_passes=0)
    print("Chosen move:", move)
