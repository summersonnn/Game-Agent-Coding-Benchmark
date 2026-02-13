"""
Agent Code: A6-WordMatrixGame
Model: google-gemini-3-pro-preview
Run: 2
Generated: 2026-02-12 18:13:26
"""

import random

# Placeholder for your actual dictionary loading mechanism
def load_words():
    # Example minimal set just to make the code instantly runnable.
    # Replace this with the logic that returns your 466k words.
    return {"cat", "cats", "coat", "coats", "dog", "dogs"}

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize the agent. 
        We pre-process the dictionary here to group words by length, 
        which will aggressively prune our search space later to avoid timeouts.
        """
        self.name = name
        raw_dict = load_words()
        
        # O(1) exact match lookups
        self.dict_set = set()
        # Grouping by length allows us to skip thousands of impossible words
        self.words_by_length = {}
        
        for word in raw_dict:
            word = word.strip().lower()
            # Ignore impossible words based on board constraints (min 2, max 16 * 2)
            if len(word) < 2 or len(word) > 32:
                continue 
                
            self.dict_set.add(word)
            w_len = len(word)
            if w_len not in self.words_by_length:
                self.words_by_length[w_len] = []
            self.words_by_length[w_len].append(word)

    def is_subsequence(self, path_str, word):
        """
        Blazing fast subsequence check using Python C-level iterators.
        Checks if letters of path_str appear in 'word' in order.
        """
        it = iter(word)
        return all(c in it for c in path_str)

    def _get_all_valid_paths(self, board):
        """
        Runs Depth-First Search (DFS) to find all valid paths on the 4x4 grid.
        Returns a dictionary mapping the path string to its coordinate list.
        """
        rows, cols = len(board), len(board[0])
        paths = {}
        
        def dfs(r, c, current_path, current_str):
            if len(current_path) >= 2:
                # Store the path. If multiple paths form the exact same string,
                # we only need one of them since scoring is purely based on lengths.
                if current_str not in paths:
                    paths[current_str] = current_path[:]
                    
            if len(current_path) == 16:
                return # Stop at max possible board size
                
            # Up, Down, Left, Right (No Diagonals)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: 
                nr, nc = r + dr, c + dc
                # Check grid bounds
                if 0 <= nr < rows and 0 <= nc < cols:
                    # Check unique visitation and no empty strings
                    if board[nr][nc] != "" and (nr, nc) not in current_path:
                        current_path.append((nr, nc))
                        dfs(nr, nc, current_path, current_str + board[nr][nc])
                        current_path.pop()

        # Start a DFS from every valid cell on the board
        for r in range(rows):
            for c in range(cols):
                if board[r][c] != "":
                    dfs(r, c, [(r, c)], board[r][c])
                    
        return paths

    def make_move(self, board, scores, total_passes):
        """
        Evaluate the board and return the highest scoring move.
        Score formula: 10 + 10 * Cleared Cells
        Cleared Cells = 2 * len(path) - len(word)
        """
        unique_paths = self._get_all_valid_paths(board)
        if not unique_paths:
            return "PASS"
            
        # Sort paths by length descending. 
        # Longest paths have the highest potential score.
        sorted_paths = sorted(unique_paths.items(), key=lambda x: len(x[0]), reverse=True)
        
        best_score = -1
        best_move = "PASS"

        # --- PASS 1: Exact Matches (Ultra-fast, O(1) lookups) ---
        # An exact match yields the highest possible score for a given path length.
        for path_str, path in sorted_paths:
            L = len(path_str)
            score = 10 + 10 * L
            
            if score > best_score and path_str in self.dict_set:
                best_score = score
                best_move = (path, path_str)

        # --- PASS 2: Subsequence Matches (Heavily Pruned) ---
        for path_str, path in sorted_paths:
            L = len(path_str)
            
            # The best possible score if we have to add 1 extra letter
            max_subsequence_score = 10 + 10 * (L - 1)
            
            # PRUNE: If even the best subsequence for this path can't beat our current best, skip it!
            if max_subsequence_score <= best_score:
                continue 
                
            # Calculate the maximum word length we should even bother checking.
            # We need: 10 + 10*(2L - w_len) > best_score
            max_w_len = 2 * L - (best_score - 10) // 10 - 1
            max_w_len = min(max_w_len, 2 * L)
            
            # Start checking from shortest possible words (L + 1) to maximize score
            for w_len in range(L + 1, max_w_len + 1):
                found_better = False
                for word in self.words_by_length.get(w_len, []):
                    if self.is_subsequence(path_str, word):
                        score = 10 + 10 * (2 * L - w_len)
                        if score > best_score:
                            best_score = score
                            best_move = (path, word)
                            found_better = True
                            break # Found the best scoring word for this specific length!
                            
                # If we found a match at this length, it is the optimal subsequence 
                # for this specific path_str, so we don't need to check longer (lower scoring) words.
                if found_better:
                    break 

        return best_move