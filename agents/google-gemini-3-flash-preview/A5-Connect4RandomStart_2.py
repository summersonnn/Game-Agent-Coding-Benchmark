"""
Agent Code: A5-Connect4RandomStart
Model: google-gemini-3-flash-preview
Run: 2
Generated: 2026-02-12 14:51:12
"""

import collections

class WordMatrixAgent:
    def __init__(self, name, word_list):
        """
        Initialize the agent and pre-process the dictionary.
        word_list: a collection of lowercase English words.
        """
        self.name = name
        # Organize dictionary by length for efficiency: {length: set(words)}
        self.words_by_len = collections.defaultdict(set)
        for word in word_list:
            word = word.lower()
            if 2 <= len(word) <= 32: # Max path 16 * 2 = 32
                self.words_by_len[len(word)].add(word)
        
        # Keep a flat set for O(1) exact matches
        self.dictionary_set = set(word_list)

    def is_subsequence(self, path_str, word):
        """Checks if path_str is a subsequence of word."""
        it = iter(word)
        return all(char in it for char in path_str)

    def find_best_word_for_path(self, path_str):
        """
        Finds the shortest valid word for a given path string.
        Shorter words = more cleared cells = higher score.
        """
        p_len = len(path_str)
        
        # Priority 1: Exact Match (Length of word == Length of path)
        if path_str in self.dictionary_set:
            return path_str
            
        # Priority 2: Subsequence matches (Length + 1 up to Length * 2)
        for length in range(p_len + 1, (2 * p_len) + 1):
            for word in self.words_by_len[length]:
                if self.is_subsequence(path_str, word):
                    return word
        return None

    def get_neighbors(self, r, c, board):
        """Returns valid Up/Down/Left/Right neighbors."""
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4 and board[nr][nc] != "":
                neighbors.append((nr, nc))
        return neighbors

    def make_move(self, board, scores, total_passes):
        """
        Scans the board for the highest-scoring valid move.
        """
        best_move = None
        max_cleared = -1

        # Iterate through every cell as a potential starting point
        for r in range(4):
            for c in range(4):
                if board[r][c] == "":
                    continue
                
                # Start DFS to find paths (limited to length 8 for performance)
                stack = [([(r, c)], board[r][c])]
                
                while stack:
                    path, path_str = stack.pop()
                    
                    # Try to find a word for this path
                    if len(path) >= 2:
                        word = self.find_best_word_for_path(path_str)
                        if word:
                            # Efficiency: Cleared cells = len(path) - (len(word) - len(path))
                            # Simplified: 2 * len(path) - len(word)
                            cleared_cells = 2 * len(path) - len(word)
                            
                            if cleared_cells > max_cleared:
                                max_cleared = cleared_cells
                                best_move = (path, word)
                                
                                # Early exit for a "perfect" long path
                                if cleared_cells >= 6: 
                                    return best_move

                    # Continue DFS if path length is manageable
                    if len(path) < 8: 
                        curr_r, curr_c = path[-1]
                        for nr, nc in self.get_neighbors(curr_r, curr_c, board):
                            if (nr, nc) not in path:
                                stack.append((path + [(nr, nc)], path_str + board[nr][nc]))

        return best_move if best_move else "PASS"