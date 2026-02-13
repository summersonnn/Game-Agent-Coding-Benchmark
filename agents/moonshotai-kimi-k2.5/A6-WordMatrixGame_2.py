"""
Agent Code: A6-WordMatrixGame
Model: moonshotai/kimi-k2.5
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
        
        # Index words by length for faster lookup
        self.words_by_length = {}
        self.max_word_len = 0
        for word in self.dictionary:
            l = len(word)
            if l > self.max_word_len:
                self.max_word_len = l
            if l not in self.words_by_length:
                self.words_by_length[l] = []
            self.words_by_length[l].append(word)
    
    def _is_subsequence(self, sub, word):
        """
        Check if sub is a subsequence of word.
        Returns True if all characters of sub appear in word in order.
        """
        if len(sub) > len(word):
            return False
        it = iter(word)
        return all(char in it for char in sub)
    
    def _get_paths(self, board):
        """
        Generate valid paths on the board using DFS.
        Returns list of (path_coords, path_string) sorted by length descending.
        Limits search depth and total paths to avoid timeouts.
        """
        rows, cols = 4, 4
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # No diagonals
        paths = []
        
        def dfs(r, c, visited, coords, s):
            # Add path if length >= 2
            if len(coords) >= 2:
                paths.append((list(coords), s))
            
            # Limit depth to prevent exponential explosion (max 16, but 8-10 is safe)
            if len(coords) >= 9:
                return
            
            # Explore neighbors
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                    cell = board[nr][nc]
                    if cell != "":  # Must contain a letter
                        visited.add((nr, nc))
                        dfs(nr, nc, visited, coords + [(nr, nc)], s + cell)
                        visited.remove((nr, nc))
        
        # Start DFS from each non-empty cell
        for r in range(rows):
            for c in range(cols):
                cell = board[r][c]
                if cell != "":
                    dfs(r, c, {(r, c)}, [(r, c)], cell)
        
        # Sort by length descending (prioritize longer paths for higher scores)
        paths.sort(key=lambda x: -len(x[0]))
        
        # Limit total paths to check (top 200 should be sufficient)
        return paths[:200]
    
    def make_move(self, board, scores, total_passes):
        """
        Called when it's your turn. Single attempt only.
        
        Strategy:
        1. Generate candidate paths (longer is better)
        2. For each path, find the shortest valid word that contains the path as subsequence
           (shorter word = more cells cleared = higher score)
        3. Return the first good move found (prioritizes longer paths with shorter words)
        """
        # Get candidate paths
        paths = self._get_paths(board)
        
        for coords, path_str in paths:
            k = len(coords)
            # Word must be at least length k and at most 2*k
            min_len = k
            max_len = min(2 * k, self.max_word_len)
            
            # Search for words from shortest to longest to maximize cleared cells
            for word_len in range(min_len, max_len + 1):
                if word_len not in self.words_by_length:
                    continue
                
                candidates = self.words_by_length[word_len]
                for word in candidates:
                    if self._is_subsequence(path_str, word):
                        # Valid move found: path_str is subsequence of word
                        # Score = 10 + 10 * (2*k - word_len)
                        return (coords, word)
        
        # No valid move found
        return "PASS"
