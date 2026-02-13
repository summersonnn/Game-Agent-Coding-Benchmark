"""
Agent Code: A6-WordMatrixGame
Model: google-gemini-3-pro-preview
Run: 1
Generated: 2026-02-12 18:13:26
"""

import random

class WordMatrixAgent:
    def __init__(self, name, dictionary_words):
        """
        Initialize the agent and optimize the dictionary.
        dictionary_words should be an iterable of valid strings.
        """
        self.name = name
        # Use a set for O(1) lookups. 
        # Filter out words that are too short to be legal.
        self.dictionary = {word.lower() for word in dictionary_words if len(word) >= 2}

    def make_move(self, board, scores, total_passes):
        """
        Executes a turn by searching for exact path-to-word matches.
        """
        rows, cols = 4, 4
        
        def dfs(r, c, current_path, current_word):
            # If our path is valid and forms a complete word, return it immediately
            if len(current_path) >= 2 and current_word in self.dictionary:
                return current_path, current_word

            # Stop searching if the path gets too long (optimization to avoid timeouts)
            if len(current_path) >= 6:
                return None

            # Explore adjacent cells (Horizontal and Vertical only)
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                
                # Check boundaries, ensure cell isn't empty, and avoid revisiting cells
                if (0 <= nr < rows and 0 <= nc < cols and 
                    board[nr][nc] != "" and 
                    (nr, nc) not in current_path):
                    
                    next_path = current_path + [(nr, nc)]
                    next_word = current_word + board[nr][nc]
                    
                    result = dfs(nr, nc, next_path, next_word)
                    if result:
                        return result # Bubble up the successful move
            return None

        # Iterate through every cell on the board to start the DFS
        for r in range(rows):
            for c in range(cols):
                if board[r][c] != "":
                    # Try to find a valid exact match starting from this cell
                    move = dfs(r, c, [(r, c)], board[r][c])
                    if move:
                        return move # Returns (path, word)

        # If no exact matches are found anywhere, safely pass to avoid the -10 penalty
        return "PASS"