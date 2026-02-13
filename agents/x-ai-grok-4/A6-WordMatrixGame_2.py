"""
Agent Code: A6-WordMatrixGame
Model: x-ai/grok-4
Run: 2
Generated: 2026-02-13 22:53:02
"""



import random

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize your agent.
        Pre-process the dictionary here for fast lookups.
        """
        self.name = name
        self.dictionary = load_words()  # Returns set of ~466k lowercase words
        self.trie = TrieNode()
        for word in self.dictionary:
            if len(word) < 2:
                continue
            node = self.trie
            for char in word:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.is_end = True

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
        results = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        def dfs(r, c, node, path, visited):
            char = board[r][c]
            if char not in node.children:
                return
            node = node.children[char]
            visited.add((r, c))
            path.append((r, c))
            if node.is_end and len(path) >= 2:
                word = ''.join(board[pr][pc] for pr, pc in path)
                results.append((list(path), word))
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and board[nr][nc] != "" and (nr, nc) not in visited:
                    dfs(nr, nc, node, path, visited)
            visited.remove((r, c))
            path.pop()

        for i in range(4):
            for j in range(4):
                if board[i][j] != "":
                    visited = set()
                    path = []
                    dfs(i, j, self.trie, path, visited)

        if not results:
            return "PASS"

        # Choose the one with maximum path length
        best = max(results, key=lambda x: len(x[0]))
        return best
