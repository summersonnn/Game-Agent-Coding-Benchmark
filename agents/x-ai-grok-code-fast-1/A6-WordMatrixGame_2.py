"""
Agent Code: A6-WordMatrixGame
Model: x-ai/grok-code-fast-1
Run: 2
Generated: 2026-02-13 22:39:54
"""



import random

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize your agent.
        Pre-process the dictionary here for fast lookups.
        """
        self.name = name
        self.dictionary = load_words()  # Returns set of ~466k lowercase words

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
        # Generate all valid paths of length 2-8 where the joined letters form a word in the dictionary
        candidates = self._find_valid_paths(board)
        
        if candidates:
            # Choose the path with the longest length (to clear more cells), pick the first if ties
            candidates.sort(key=lambda x: len(x[0]), reverse=True)
            best_path, best_word = candidates[0]
            return (best_path, best_word)
        else:
            # No valid move found, pass
            return "PASS"
    
    def _find_valid_paths(self, board):
        """
        Find all paths of length 2-8 where:
        - Path is valid: adjacent (up/down/left/right), no repeats, no empty cells.
        - The joined letters form a word exactly (len(word) == len(path)), and it's in the dictionary.
        """
        paths = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        def dfs(current_path, visited):
            if 2 <= len(current_path) <= 8:
                letters = [board[r][c] for r, c in current_path]
                word = ''.join(letters)
                if word in self.dictionary:
                    paths.append((current_path[:], word))
            if len(current_path) >= 8:
                return
            last_r, last_c = current_path[-1]
            for dr, dc in directions:
                nr, nc = last_r + dr, last_c + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and board[nr][nc] != "":
                    visited.add((nr, nc))
                    current_path.append((nr, nc))
                    dfs(current_path, visited)
                    current_path.pop()
                    visited.remove((nr, nc))
        
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    visited = set([(r, c)])
                    dfs([(r, c)], visited)
        
        return paths
