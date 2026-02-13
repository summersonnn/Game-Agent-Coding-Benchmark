"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-5.2-codex
Run: 1
Generated: 2026-02-13 23:22:56
"""



import random

# A tiny trie implementation for fast prefix checks
class TrieNode:
    __slots__ = ("children", "is_word")
    def __init__(self):
        self.children = {}
        self.is_word = False


class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize the agent and preprocess the dictionary.
        We build:
          1) A trie of words length 2..16 (for exact path matches).
          2) A pair->word lookup for length‑2 paths with subsequence words (length <=4).
        """
        self.name = name
        self.dictionary = load_words()

        self.max_len = 16
        self.root = TrieNode()
        self.pair_to_word = {}

        # Build trie and pair map
        for w in self.dictionary:
            w = w.strip().lower()
            if not w.isalpha():
                continue

            L = len(w)

            # Trie for exact matches (path length == word length)
            if 2 <= L <= self.max_len:
                node = self.root
                for ch in w:
                    if ch not in node.children:
                        node.children[ch] = TrieNode()
                    node = node.children[ch]
                node.is_word = True

            # Pair map for subsequence fallback (path length 2, word length <= 4)
            if 2 <= L <= 4:
                for i in range(L - 1):
                    for j in range(i + 1, L):
                        pair = w[i] + w[j]
                        if pair not in self.pair_to_word or L < len(self.pair_to_word[pair]):
                            self.pair_to_word[pair] = w

    def make_move(self, board, scores, total_passes):
        """
        Main decision routine.
        Strategy:
          1) Find the longest exact word along a valid path (best score).
          2) If none exists, attempt a 2‑cell path with a word that contains
             those letters as a subsequence (word length <= 4).
          3) Otherwise PASS.
        """
        n = 4
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        best_word = ""
        best_path = None
        visited = [[False] * n for _ in range(n)]

        # DFS to find longest exact word
        def dfs(r, c, node, word, path):
            nonlocal best_word, best_path
            if node.is_word and len(word) >= 2:
                if len(word) > len(best_word):
                    best_word = word
                    best_path = path.copy()

            if len(word) >= self.max_len:
                return

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and not visited[nr][nc]:
                    letter = board[nr][nc]
                    if letter and letter in node.children:
                        visited[nr][nc] = True
                        dfs(nr, nc, node.children[letter],
                            word + letter, path + [(nr, nc)])
                        visited[nr][nc] = False

        # Run DFS from each non-empty cell
        for r in range(n):
            for c in range(n):
                letter = board[r][c]
                if letter and letter in self.root.children:
                    visited[r][c] = True
                    dfs(r, c, self.root.children[letter], letter, [(r, c)])
                    visited[r][c] = False

        if best_word:
            return (best_path, best_word)

        # Fallback: 2-cell path with subsequence word (length <=4)
        best_fallback = None
        best_score = -1
        for r in range(n):
            for c in range(n):
                a = board[r][c]
                if not a:
                    continue
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc]:
                        b = board[nr][nc]
                        pair = a + b
                        if pair in self.pair_to_word:
                            word = self.pair_to_word[pair]
                            wlen = len(word)
                            score = 10 + 10 * (4 - wlen)  # p=2 -> cleared=4-w
                            if score > best_score:
                                best_score = score
                                best_fallback = ([(r, c), (nr, nc)], word)

        if best_fallback:
            return best_fallback

        return "PASS"
