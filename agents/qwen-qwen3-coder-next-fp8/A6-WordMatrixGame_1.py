"""
Agent Code: A6-WordMatrixGame
Model: qwen/qwen3-coder-next@preset/fp8
Run: 1
Generated: 2026-02-13 22:39:54
"""

from collections import defaultdict
import itertools

import random
from collections import defaultdict
import itertools

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize your agent.
        Pre-process the dictionary here for fast lookups.
        """
        self.name = name
        self.dictionary = load_words()  # Returns set of ~466k lowercase words
        
        # Pre-process dictionary for efficient lookups
        # Group words by length for faster filtering
        self.words_by_length = defaultdict(list)
        for word in self.dictionary:
            self.words_by_length[len(word)].append(word)
        
        # Also store words by first letter for quick pruning
        self.words_by_first_letter = defaultdict(set)
        for word in self.dictionary:
            if word:  # Ensure non-empty
                self.words_by_first_letter[word[0]].add(word)
    
    def _is_valid_path(self, path, board):
        """Check if path follows all path rules"""
        if len(path) < 2:
            return False
        
        visited = set()
        for i, (r, c) in enumerate(path):
            # Check bounds
            if r < 0 or r >= 4 or c < 0 or c >= 4:
                return False
            
            # Check for duplicates
            if (r, c) in visited:
                return False
            visited.add((r, c))
            
            # Check cell is not empty
            if board[r][c] == "":
                return False
            
            # Check adjacency for consecutive cells
            if i > 0:
                prev_r, prev_c = path[i-1]
                if abs(r - prev_r) + abs(c - prev_c) != 1:  # Not adjacent
                    return False
        
        return True
    
    def _is_subsequence(self, path_letters, word):
        """Check if path_letters form a subsequence of word"""
        word_idx = 0
        for letter in path_letters:
            found = False
            while word_idx < len(word):
                if word[word_idx] == letter:
                    found = True
                    word_idx += 1
                    break
                word_idx += 1
            if not found:
                return False
        return True
    
    def _find_words_for_path(self, path, board):
        """Find valid words that have path letters as subsequence"""
        path_letters = [board[r][c] for (r, c) in path]
        path_len = len(path)
        min_word_len = path_len
        max_word_len = 2 * path_len
        
        # Try to find matching words efficiently
        # Prioritize words of exact path length (maximize cleared cells)
        for word_len in range(min_word_len, max_word_len + 1):
            if word_len not in self.words_by_length:
                continue
                
            # For small paths, check all words of that length
            if path_len <= 4:
                for word in self.words_by_length[word_len]:
                    if self._is_subsequence(path_letters, word):
                        return word
            
            # For longer paths, use more targeted approach
            else:
                # Try words starting with first path letter
                first_letter = path_letters[0]
                if first_letter in self.words_by_first_letter:
                    for word in self.words_by_first_letter[first_letter]:
                        if len(word) < min_word_len or len(word) > max_word_len:
                            continue
                        if word in self.words_by_length[len(word)] and self._is_subsequence(path_letters, word):
                            return word
        
        return None
    
    def _get_all_paths_from_cell(self, start_r, start_c, board, max_depth=6):
        """Generate all valid paths starting from a cell (BFS/DFS)"""
        paths = []
        stack = [(start_r, start_c, [(start_r, start_c)])]
        
        while stack:
            r, c, path = stack.pop()
            
            # Record this path if length >= 2
            if len(path) >= 2:
                paths.append(path)
            
            # Stop if we've reached max depth
            if len(path) >= max_depth:
                continue
            
            # Try all adjacent cells
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < 4 and 0 <= nc < 4 and 
                    (nr, nc) not in path and 
                    board[nr][nc] != ""):
                    stack.append((nr, nc, path + [(nr, nc)]))
        
        return paths
    
    def _get_all_paths(self, board):
        """Get all possible paths on the board"""
        all_paths = []
        
        # Try starting from each non-empty cell
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    paths = self._get_all_paths_from_cell(r, c, board)
                    all_paths.extend(paths)
        
        return all_paths
    
    def _score_move(self, path, word, board):
        """Calculate score for a valid move"""
        cleared_cells = len(path)
        return 10 + (10 * cleared_cells)
    
    def make_move(self, board, scores, total_passes):
        """
        Called when it's your turn. Single attempt only.
        """
        try:
            # Check if game should end due to too many passes
            if total_passes >= 6:
                return "PASS"
            
            # Get all possible paths
            all_paths = self._get_all_paths(board)
            
            if not all_paths:
                return "PASS"
            
            # Try to find the best valid move
            best_move = None
            best_score = -1
            
            # Shuffle paths to add variety and avoid predictable patterns
            random.shuffle(all_paths)
            
            for path in all_paths:
                word = self._find_words_for_path(path, board)
                if word:
                    score = self._score_move(path, word, board)
                    if score > best_score:
                        best_score = score
                        best_move = (path, word)
                        # Early exit if we found a perfect 10+10*path_len move
                        # (i.e., no extra letters) and path length >= 3
                        if best_score >= 40:  # 10 + 10*3 for path length 3
                            break
            
            if best_move:
                return best_move
            
            # If no valid moves found, pass
            return "PASS"
            
        except Exception:
            # On any error, return PASS (though technically should be invalid move)
            return "PASS"

# Helper function that should be provided by the environment
def load_words():
    """
    Should return a set of valid English words.
    For demonstration, here's a minimal example.
    In the real environment, this would load the full dictionary.
    """
    # This is a placeholder - real implementation would load full dictionary
    return {"cat", "coat", "dog", "code", "act", "at", "to", "go", "dad", "dad", 
            "add", "bad", "cab", "cad", "cog", "cot", "dot", "god", "oda", "act", 
            "cat", "tac", "tab", "bat", "hat", "hit", "hot", "hat", "had", "dad"}
