"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-5.2-codex
Run: 2
Generated: 2026-02-13 23:22:56
"""



import random

class WordMatrixAgent:
    """
    Simple and safe agent:
    - Builds a trie of dictionary words of length 2..16.
    - Finds the longest word that can be formed by a 4-neighbor path
      that exactly matches the word (so the move is always valid).
    - If no word is found, returns PASS.
    """

    _trie = None
    _neighbors = None
    _max_len = 0

    def __init__(self, name):
        self.name = name

        # Build shared trie once
        if WordMatrixAgent._trie is None:
            try:
                words = load_words()
            except Exception:
                # Fallback small list if load_words is unavailable
                words = {"at", "cat", "dog", "hat", "rat", "to", "in", "on"}

            # Filter words to lengths 2..16 (path length limit)
            valid_words = [w for w in words if w.isalpha() and 2 <= len(w) <= 16]

            trie = {}
            max_len = 0
            for w in valid_words:
                max_len = max(max_len, len(w))
                node = trie
                for ch in w:
                    node = node.setdefault(ch, {})
                node["$"] = w  # end-of-word marker

            WordMatrixAgent._trie = trie
            WordMatrixAgent._max_len = max_len

            # Precompute neighbors for 4x4 board
            n = 4
            neighbors = [[[] for _ in range(n)] for _ in range(n)]
            for r in range(n):
                for c in range(n):
                    if r > 0: neighbors[r][c].append((r - 1, c))
                    if r < n - 1: neighbors[r][c].append((r + 1, c))
                    if c > 0: neighbors[r][c].append((r, c - 1))
                    if c < n - 1: neighbors[r][c].append((r, c + 1))
            WordMatrixAgent._neighbors = neighbors

        self.trie = WordMatrixAgent._trie
        self.neighbors = WordMatrixAgent._neighbors
        self.max_len = WordMatrixAgent._max_len

    def make_move(self, board, scores, total_passes):
        self.board = board
        self.best_word = None
        self.best_path = None
        self.best_len = 0
        self.visited = [[False] * 4 for _ in range(4)]

        for r in range(4):
            for c in range(4):
                ch = board[r][c]
                if ch and ch in self.trie:
                    self.visited[r][c] = True
                    self._dfs(r, c, self.trie[ch], [(r, c)])
                    self.visited[r][c] = False

        if self.best_word:
            return (self.best_path, self.best_word)
        return "PASS"

    def _dfs(self, r, c, node, path):
        if "$" in node:
            word = node["$"]
            if len(word) > self.best_len:
                self.best_len = len(word)
                self.best_word = word
                self.best_path = list(path)

        if len(path) >= self.max_len:
            return

        for nr, nc in self.neighbors[r][c]:
            if not self.visited[nr][nc]:
                ch = self.board[nr][nc]
                if ch and ch in node:
                    self.visited[nr][nc] = True
                    path.append((nr, nc))
                    self._dfs(nr, nc, node[ch], path)
                    path.pop()
                    self.visited[nr][nc] = False
