"""
Agent Code: A6-WordMatrixGame
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-12 19:13:59
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
        self.words = sorted(list(self.dictionary), key=len)  # Sort words by length for efficient searching

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
        # Get all possible valid paths on the board
        all_paths = self.get_all_paths(board)
        
        # List to hold possible moves: (path, word, score)
        possible_moves = []
        
        for path, string in all_paths:
            path_len = len(path)
            max_word_len = 2 * path_len
            
            # Case 1: If the path string is directly a word, it's the best (clears all path cells)
            if string in self.dictionary:
                cleared = path_len
                score = 10 + 10 * cleared
                possible_moves.append((path, string, score))
                continue
            
            # Case 2: Find the shortest word that has the path string as a subsequence, within length limits
            min_word = None
            for word in self.words:
                if len(word) > max_word_len:
                    break  # No need to check longer words
                if self.is_subseq(string, word):
                    min_word = word
                    break  # Found the shortest one
            
            if min_word is not None:
                cleared = 2 * path_len - len(min_word)
                score = 10 + 10 * cleared
                possible_moves.append((path, min_word, score))
        
        # If no valid moves, pass
        if not possible_moves:
            return "PASS"
        
        # Choose the move with the highest score (if ties, pick the first one)
        best_move = max(possible_moves, key=lambda x: x[2])
        return (best_move[0], best_move[1])

    def get_all_paths(self, board):
        """
        Collect all valid paths on the board.
        """
        paths = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        def dfs(row, col, visited, path, string):
            path.append((row, col))
            string += board[row][col]
            visited.add((row, col))
            
            # Only add paths of length 2 or more
            if len(path) >= 2:
                paths.append((path[:], string[:]))
            
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and board[nr][nc]:
                    dfs(nr, nc, visited, path, string)
            
            path.pop()
            visited.remove((row, col))
        
        for r in range(4):
            for c in range(4):
                if board[r][c]:  # Only start from non-empty cells
                    dfs(r, c, set(), [], "")
        
        return paths

    def is_subseq(self, s, w):
        """
        Check if s is a subsequence of w.
        """
        i = 0
        for c in w:
            if i < len(s) and c == s[i]:
                i += 1
        return i == len(s)
