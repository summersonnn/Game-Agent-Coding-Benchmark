"""
Agent Code: A6-WordMatrixGame
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-13 22:39:54
"""

from itertools import combinations

import random
from itertools import combinations

class TrieNode:
    __slots__ = ['children', 'is_word']
    def __init__(self):
        self.children = {}
        self.is_word = False

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # Assume this returns set of lowercase words
        
        # Build trie for exact word matching
        self.trie_root = TrieNode()
        for word in self.dictionary:
            node = self.trie_root
            for char in word:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.is_word = True
        
        # Precompute maps for subsequence searches (L=2,3,4)
        # Map: subsequence_string -> shortest word containing it (within length constraints)
        self.subseq_maps = {2: {}, 3: {}, 4: {}}
        
        for word in self.dictionary:
            n = len(word)
            # Only consider words that could be used (length between L and 2L)
            for L in [2, 3, 4]:
                if L <= n <= 2 * L:
                    # Generate all subsequences of length L
                    for indices in combinations(range(n), L):
                        subseq = ''.join(word[i] for i in indices)
                        # Store shortest word for this subsequence
                        if subseq not in self.subseq_maps[L] or n < len(self.subseq_maps[L][subseq]):
                            self.subseq_maps[L][subseq] = word
    
    def make_move(self, board, scores, total_passes):
        """
        Find best valid move or PASS.
        Returns: (path, word) or "PASS"
        """
        best_score = -10  # Worse than PASS (0) and invalid (-10)
        best_move = None
        
        # 1. Search for exact matches (word == path string) - highest efficiency
        exact_path, exact_word, exact_score = self._find_exact_match(board)
        if exact_score > best_score:
            best_score = exact_score
            best_move = (exact_path, exact_word)
        
        # 2. Search for non-exact matches with L=2,3,4
        for L in [4, 3, 2]:  # Try longer paths first for potentially higher scores
            non_exact_path, non_exact_word, non_exact_score = self._find_non_exact_match(board, L)
            if non_exact_score > best_score:
                best_score = non_exact_score
                best_move = (non_exact_path, non_exact_word)
        
        # 3. Return best move or PASS
        if best_move:
            return best_move
        return "PASS"
    
    def _find_exact_match(self, board):
        """
        Find longest path that spells an exact dictionary word.
        Returns: (path, word, score) or (None, None, -1)
        """
        best_path = None
        best_word = None
        best_score = -1
        
        # DFS from each starting cell
        for i in range(4):
            for j in range(4):
                if board[i][j]:
                    self._dfs_exact(
                        i, j, board,
                        path=[(i, j)],
                        current_str=board[i][j],
                        node=self.trie_root,
                        best=[best_path, best_word, best_score]
                    )
                    # Update from reference
                    best_path, best_word, best_score = best[0], best[1], best[2]
        
        if best_path:
            # Score: 10 + 10 * cleared_cells = 10 + 10 * len(path) (since word==path)
            return best_path, best_word, 10 + 10 * len(best_path)
        return None, None, -1
    
    def _dfs_exact(self, i, j, board, path, current_str, node, best):
        """
        DFS for exact matches using trie.
        best = [best_path, best_word, best_score] (mutable)
        """
        # Check if current string is a complete word (path length >=2)
        if node.is_word and len(path) >= 2:
            score = 10 + 10 * len(path)
            if score > best[2]:
                best[0] = tuple(path)  # Store as tuple for immutability
                best[1] = current_str
                best[2] = score
        
        # Explore neighbors
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < 4 and 0 <= nj < 4:
                if board[ni][nj] and (ni, nj) not in path:
                    next_char = board[ni][nj]
                    if next_char in node.children:
                        self._dfs_exact(
                            ni, nj, board,
                            path + [(ni, nj)],
                            current_str + next_char,
                            node.children[next_char],
                            best
                        )
    
    def _find_non_exact_match(self, board, L):
        """
        Find path of length L and word where path is subsequence of word.
        Word length must be between L and 2L.
        Returns: (path, word, score) or (None, None, -1)
        """
        best_path = None
        best_word = None
        best_score = -1
        word_map = self.subseq_maps[L]
        
        # Generate all paths of length L
        for i in range(4):
            for j in range(4):
                if board[i][j]:
                    self._dfs_path(
                        L, i, j, board,
                        path=[(i, j)],
                        visited={(i, j)},
                        current_str=board[i][j],
                        best=[best_path, best_word, best_score],
                        word_map=word_map
                    )
                    best_path, best_word, best_score = best[0], best[1], best[2]
        
        if best_path:
            word_len = len(best_word)
            cleared = 2 * L - word_len
            score = 10 + 10 * cleared
            return best_path, best_word, score
        return None, None, -1
    
    def _dfs_path(self, L, i, j, board, path, visited, current_str, best, word_map):
        """
        DFS for paths of exact length L.
        """
        if len(path) == L:
            if current_str in word_map:
                word = word_map[current_str]
                # Double-check constraints (should hold by construction)
                if L <= len(word) <= 2 * L:
                    # Evaluate this candidate
                    cleared = 2 * L - len(word)
                    score = 10 + 10 * cleared
                    if score > best[2]:
                        best[0] = tuple(path)
                        best[1] = word
                        best[2] = score
            return
        
        # Continue path
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < 4 and 0 <= nj < 4:
                if board[ni][nj] and (ni, nj) not in visited:
                    self._dfs_path(
                        L, ni, nj, board,
                        path + [(ni, nj)],
                        visited | {(ni, nj)},
                        current_str + board[ni][nj],
                        best,
                        word_map
                    )
