"""
Agent Code: A6-WordMatrixGame
Model: stepfun/step-3.5-flash:free
Run: 2
Generated: 2026-02-13 23:21:08
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # Assume this returns set of ~466k lowercase words
        self.words_by_length = defaultdict(set)
        for word in self.dictionary:
            self.words_by_length[len(word)].add(word)
    
    def make_move(self, board, scores, total_passes):
        """
        Find the best valid move according to strategy:
        1. Longest exact word match (path string == word)
        2. If none, longest path with word length = path length + 1
        3. Otherwise, pass
        """
        # Generate all possible paths of length 2-8
        # We'll collect paths by length, longest first
        for L in range(8, 1, -1):  # L from 8 down to 2
            paths = self._generate_paths(board, L)
            # First try: exact match (word == path string)
            for path, s in paths:
                if s in self.dictionary:
                    return (path, s)
        
        # If no exact match, try path with word length = L+1
        for L in range(8, 1, -1):
            paths = self._generate_paths(board, L)
            for path, s in paths:
                # Generate all candidate words by inserting one letter into s
                for i in range(L + 1):  # insertion positions 0..L
                    for c in 'abcdefghijklmnopqrstuvwxyz':
                        candidate = s[:i] + c + s[i:]
                        if candidate in self.words_by_length.get(L + 1, set()):
                            return (path, candidate)
        
        # No valid move found, pass
        return "PASS"
    
    def _generate_paths(self, board, length):
        """
        Generate all simple paths (no revisits) of exactly `length` cells
        that are adjacent (horizontally/vertically) and contain only non-empty cells.
        Returns list of (path, string) where path is list of (r,c) and string is concatenated letters.
        """
        paths = []
        rows, cols = 4, 4
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == "":
                    continue
                # DFS stack: (current_path, current_string, visited_set)
                stack = [ ([(r, c)], board[r][c], {(r, c)}) ]
                while stack:
                    path, s, visited = stack.pop()
                    if len(path) == length:
                        paths.append((path, s))
                        continue
                    last_r, last_c = path[-1]
                    for dr, dc in directions:
                        nr, nc = last_r + dr, last_c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if board[nr][nc] != "" and (nr, nc) not in visited:
                                new_path = path + [(nr, nc)]
                                new_s = s + board[nr][nc]
                                new_visited = visited | {(nr, nc)}
                                stack.append((new_path, new_s, new_visited))
        return paths
