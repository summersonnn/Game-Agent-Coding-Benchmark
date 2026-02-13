"""
Agent Code: A6-WordMatrixGame
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 1
Generated: 2026-02-13 22:39:54
"""

import itertools
from collections import defaultdict

class TrieNode:
    __slots__ = ('children', 'is_end')
    def __init__(self):
        self.children = {}
        self.is_end = False

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize the agent: load the dictionary and build a trie.
        In a real game, the dictionary would be loaded from a file.
        Here we use a small sample for illustration.
        """
        self.name = name
        # Sample dictionary (replace with actual word list)
        self.dictionary = {
            "cat", "cats", "coat", "scat", "cast", "act", "tac", "at",
            "dog", "dogs", "god", "good", "go", "do", "od",
            "rat", "rate", "art", "tar", "tra",
            "bat", "bath", "hat", "heat", "eat",
            "sit", "its", "is", "it", "si",
            "sun", "run", "fun", "fund", "find",
            "note", "tone", "one", "net", "ten",
            "star", "arts", "rats", "tars",
            "board", "broad", "road", "bar",
            "game", "gamer", "rage", "gear",
            "word", "row", "rod", "ord",
            "matrix", "max", "rim", "ram",
            "play", "lay", "pay", "pray",
            "agent", "age", "gent", "get",
            "turn", "run", "urn", "nut",
            "score", "core", "ore", "sore",
            "point", "pint", "pin", "pit",
            "valid", "lid", "via", "dial",
            "path", "pat", "hat", "tap",
            "cell", "ell", "el", "le",
            "letter", "let", "tee", "ere",
            "empty", "pty", "met", "pet"
        }
        # Build trie for subsequence matching
        self.trie = TrieNode()
        for word in self.dictionary:
            node = self.trie
            for ch in word:
                if ch not in node.children:
                    node.children[ch] = TrieNode()
                node = node.children[ch]
            node.is_end = True

        # For quick exact match
        self.word_set = self.dictionary

    def make_move(self, board, scores, total_passes):
        """
        Called when it's your turn. Returns either (path, word) or "PASS".
        """
        # Get all non-empty cells
        cells = [(r, c) for r in range(4) for c in range(4) if board[r][c] != ""]
        if len(cells) < 2:
            return "PASS"

        # Enumerate all simple paths of length 2..8 (adjustable)
        paths = []
        for start in cells:
            self._dfs_paths(board, start, [start], set([start]), paths)

        # Sort paths by length descending to maximize score? Not necessary, just first found.
        for path in paths:
            path_str = ''.join(board[r][c] for (r, c) in path)
            L = len(path)

            # 1. Exact match
            if path_str in self.word_set:
                return (path, path_str)

            # 2. Subsequence match
            word = self._find_subsequence_word(path_str, L)
            if word:
                return (path, word)

        # No valid move found
        return "PASS"

    def _dfs_paths(self, board, current, path, visited, paths, max_len=8):
        """Depth‑first search to collect all simple paths up to max_len."""
        if len(path) >= 2:
            paths.append(path[:])  # store a copy
        if len(path) >= max_len:
            return
        r, c = current
        for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < 4 and 0 <= nc < 4 and board[nr][nc] != "" and (nr, nc) not in visited:
                visited.add((nr, nc))
                path.append((nr, nc))
                self._dfs_paths(board, (nr, nc), path, visited, paths, max_len)
                path.pop()
                visited.remove((nr, nc))

    def _find_subsequence_word(self, pattern, path_len):
        """
        Search the trie for any word that contains `pattern` as a subsequence
        and whose length is between path_len and 2*path_len.
        Returns the word if found, else None.
        """
        max_len = 2 * path_len
        result = [None]  # use a list to allow modification in nested function

        def dfs(node, i, current_word):
            # If we already have a result, stop
            if result[0] is not None:
                return
            # Prune if length already too long
            if len(current_word) > max_len:
                return
            # Minimum required length to finish the pattern
            remaining = len(pattern) - i
            if len(current_word) + remaining > max_len:
                return
            # Check if we have a complete word that matches the pattern
            if node.is_end and i == len(pattern):
                result[0] = current_word
                return
            # Try all children
            for ch, child in node.children.items():
                # Option 1: if ch matches the next pattern letter, consume it
                if i < len(pattern) and ch == pattern[i]:
                    dfs(child, i+1, current_word + ch)
                # Option 2: skip this character (extra letter) – always possible
                dfs(child, i, current_word + ch)

        dfs(self.trie, 0, "")
        return result[0]