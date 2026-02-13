"""
Agent Code: A6-WordMatrixGame
Model: mistralai/mistral-large-2512
Run: 1
Generated: 2026-02-12 19:13:59
"""

from collections import deque

import random
from collections import deque

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = self.load_words()
        # Precompute word lengths for faster filtering
        self.word_lengths = set(len(word) for word in self.dictionary)
        # Common prefixes for quick filtering
        self.prefixes = set()
        for word in self.dictionary:
            for i in range(1, len(word)+1):
                self.prefixes.add(word[:i])

    def load_words(self):
        # In a real implementation, this would load from a file
        # For this example, we'll use a small subset
        return {
            'cat', 'dog', 'bat', 'rat', 'car', 'coat', 'cot', 'act', 'art',
            'tar', 'oat', 'goat', 'boat', 'toad', 'road', 'card', 'cord',
            'core', 'care', 'race', 'acre', 'react', 'trace', 'crate',
            'actor', 'taco', 'roar', 'root', 'roast', 'soar', 'sort',
            'star', 'stare', 'start', 'arts', 'rats', 'cats', 'dogs',
            'bats', 'cars', 'coats', 'goats', 'boats', 'roads', 'cards'
        }

    def make_move(self, board, scores, total_passes):
        # Check if we should pass (game is nearly over)
        if total_passes >= 4:
            return "PASS"

        # Find all possible paths and potential words
        all_paths = self.find_all_paths(board)
        if not all_paths:
            return "PASS"

        # Evaluate paths and find matching words
        best_move = None
        best_score = -float('inf')

        for path in all_paths:
            path_letters = [board[r][c] for r, c in path]
            path_str = ''.join(path_letters)
            min_len = len(path)
            max_len = min(2 * min_len, 15)  # Max word length in dictionary

            # Find all words that can be formed with this path
            for length in range(min_len, max_len + 1):
                if length not in self.word_lengths:
                    continue

                # Generate all possible words of this length that contain path as subsequence
                words = self.find_words_with_subsequence(path_letters, length)
                if not words:
                    continue

                # Calculate potential score for each word
                for word in words:
                    # Calculate how many cells would be cleared
                    extra_letters = len(word) - len(path)
                    cleared_cells = len(path) - extra_letters if extra_letters >= 0 else 0
                    score = 10 + (10 * cleared_cells)

                    # Prefer moves that clear more cells
                    if score > best_score or (score == best_score and cleared_cells > 0):
                        best_score = score
                        best_move = (path, word)

        if best_move:
            return best_move
        return "PASS"

    def find_all_paths(self, board):
        """Find all valid paths on the board (length >= 2)"""
        paths = []
        rows, cols = 4, 4

        for i in range(rows):
            for j in range(cols):
                if board[i][j] == "":
                    continue
                # BFS to find all paths starting at (i,j)
                queue = deque()
                queue.append((i, j, [(i, j)], {board[i][j]}))

                while queue:
                    r, c, path, used_letters = queue.popleft()
                    if len(path) >= 2:
                        paths.append(path)

                    # Explore neighbors
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if (nr, nc) not in path and board[nr][nc] != "":
                                new_letters = used_letters.copy()
                                new_letters.add(board[nr][nc])
                                queue.append((nr, nc, path + [(nr, nc)], new_letters))

        return paths

    def find_words_with_subsequence(self, subsequence, max_length):
        """Find all words in dictionary that contain the subsequence and are <= max_length"""
        sub_len = len(subsequence)
        words = []

        for word in self.dictionary:
            if len(word) > max_length:
                continue
            if len(word) < sub_len:
                continue

            # Check if word contains subsequence
            it = iter(word)
            if all(c in it for c in subsequence):
                words.append(word)

        return words
