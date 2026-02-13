"""
Agent Code: A6-WordMatrixGame
Model: google-gemini-3-flash-preview
Run: 1
Generated: 2026-02-12 18:13:26
"""

import random

class WordMatrixAgent:
    def __init__(self, name, dictionary_set):
        self.name = name
        # Pre-filter dictionary by length (max 32 as per 2 * 16 board size)
        self.dictionary = dictionary_set
        # Group words by length for faster lookup
        self.words_by_len = {}
        for w in self.dictionary:
            self.words_by_len.setdefault(len(w), []).append(w)

    def is_subsequence(self, sub, full):
        """Checks if 'sub' string is a subsequence of 'full' string."""
        it = iter(full)
        return all(char in it for char in sub)

    def get_neighbors(self, pos, board):
        r, c = pos
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4 and board[nr][nc] != "":
                neighbors.append((nr, nc))
        return neighbors

    def find_path_and_word(self, board):
        # Start from every non-empty cell
        start_cells = [(r, c) for r in range(4) for c in range(4) if board[r][c] != ""]
        random.shuffle(start_cells)

        for start in start_cells:
            # Simple DFS to find a path of length 3 to 5
            stack = [([start], board[start[0]][start[1]])]
            while stack:
                path, sequence = stack.pop()
                
                # Try to find a perfect match (len(word) == len(path))
                if len(path) >= 2:
                    if len(path) in self.words_by_len:
                        for word in self.words_by_len[len(path)]:
                            if word == sequence: # Perfect match found
                                return path, word

                # Search deeper if path isn't too long
                if len(path) < 5:
                    for neighbor in self.get_neighbors(path[-1], board):
                        if neighbor not in path:
                            new_path = path + [neighbor]
                            new_seq = sequence + board[neighbor[0]][neighbor[1]]
                            stack.append((new_path, new_seq))
        return None

    def make_move(self, board, scores, total_passes):
        try:
            result = self.find_path_and_word(board)
            if result:
                return result
            return "PASS"
        except Exception:
            return "PASS"