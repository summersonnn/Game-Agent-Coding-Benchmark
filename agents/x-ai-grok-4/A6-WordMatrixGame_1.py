"""
Agent Code: A6-WordMatrixGame
Model: x-ai/grok-4
Run: 1
Generated: 2026-02-13 22:53:02
"""

from collections import defaultdict

import random
from collections import defaultdict

def load_words():
    # Assuming load_words is defined elsewhere to return a set of words.
    # For completeness, here's a stub; replace with actual implementation if needed.
    return set()  # Replace with actual dictionary loading

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize your agent.
        Pre-process the dictionary here for fast lookups.
        """
        self.name = name
        self.dictionary = load_words()  # Returns set of ~466k lowercase words
        self.words_by_len = defaultdict(list)
        for w in self.dictionary:
            if 2 <= len(w) <= 16:
                self.words_by_len[len(w)].append(w)

    def find_path_for_word(self, board, word):
        L = len(word)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        def dfs(idx, r, c, visited, path):
            if idx == L:
                return True
            for dr, dc in directions:
                nr = r + dr
                nc = c + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and board[nr][nc] == word[idx]:
                    visited.add((nr, nc))
                    path.append((nr, nc))
                    if dfs(idx + 1, nr, nc, visited, path):
                        return True
                    path.pop()
                    visited.remove((nr, nc))
            return False

        for i in range(4):
            for j in range(4):
                if board[i][j] == word[0]:
                    visited = set([(i, j)])
                    path = [(i, j)]
                    if dfs(1, i, j, visited, path):
                        return path
        return None

    def make_move(self, board, scores, total_passes):
        """
        Called when it's your turn. Single attempt only.

        Parameters:
        -----------
        board : list[list[str]]
            4x4 grid. Example: [['c','a','t','s'], ['d','o','g',''], ...]
        
        scores : dict
            Current scores. Example: {"Agent-1": 30, "Agent-2": 10}

        total_passes : int
            Number of consecutive passes/fails so far. Game ends at 6.

        Returns:
        --------
        tuple[list[tuple[int,int]], str] or str
            - A tuple (path, word) where path is a list of (row, col) coordinates.
            - OR the string "PASS" to skip turn.
        """
        for length in range(16, 1, -1):
            for word in self.words_by_len[length]:
                path = self.find_path_for_word(board, word)
                if path is not None:
                    return (path, word)
        return "PASS"
