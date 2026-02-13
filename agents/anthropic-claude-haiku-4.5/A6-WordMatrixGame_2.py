"""
Agent Code: A6-WordMatrixGame
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-13 22:39:54
"""

from collections import deque
from typing import Set, List, Tuple, Optional

import random
from collections import deque
from typing import Set, List, Tuple, Optional

class WordMatrixAgent:
    def __init__(self, name: str):
        """Initialize the agent with dictionary preprocessing."""
        self.name = name
        self.dictionary = self._load_words()  # ~466k words
        # Create suffix lookup for faster subsequence matching
        self.word_by_length = self._organize_by_length()

    def _load_words(self) -> Set[str]:
        """Load dictionary (replace with actual dictionary source)."""
        # Example: load from file or external source
        return set()  # Placeholder

    def _organize_by_length(self) -> dict:
        """Group words by length for efficient lookup."""
        by_length = {}
        for word in self.dictionary:
            length = len(word)
            if length not in by_length:
                by_length[length] = []
            by_length[length].append(word)
        return by_length

    def make_move(self, board: List[List[str]], scores: dict, total_passes: int) -> Tuple | str:
        """
        Main decision-making function. One shot per turn.
        """
        # Extract non-empty cells for pathfinding
        non_empty_cells = self._get_non_empty_cells(board)
        
        # Check if game is still playable
        if not self._has_valid_move(board):
            return "PASS"
        
        # Find best path with associated word
        best_move = self._find_best_move(board, non_empty_cells)
        
        if best_move:
            return best_move
        else:
            return "PASS"

    def _get_non_empty_cells(self, board: List[List[str]]) -> Set[Tuple[int, int]]:
        """Get all (row, col) coordinates with letters."""
        cells = set()
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    cells.add((r, c))
        return cells

    def _has_valid_move(self, board: List[List[str]]) -> bool:
        """Check if any two adjacent non-empty cells exist."""
        non_empty = self._get_non_empty_cells(board)
        for r, c in non_empty:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in non_empty:
                    return True
        return False

    def _find_best_move(self, board: List[List[str]], non_empty: Set) -> Optional[Tuple]:
        """
        Find the highest-scoring valid move.
        Strategy: Prioritize moves that clear more cells (fewer extras).
        """
        best_score = -10  # Worse than PASS
        best_move = None
        
        # Try all possible paths of increasing efficiency
        for path in self._generate_paths(board, non_empty):
            path_letters = [board[r][c] for r, c in path]
            
            # Find words matching this path
            candidate_words = self._find_words_for_path(path_letters)
            
            for word in candidate_words:
                if self._is_valid_move(path_letters, word):
                    score = self._calculate_score(path, path_letters, word)
                    if score > best_score:
                        best_score = score
                        best_move = (path, word)
        
        return best_move

    def _generate_paths(self, board: List[List[str]], non_empty: Set, max_depth: int = 5) -> List[List[Tuple[int, int]]]:
        """
        Generate all valid paths of length 2 to max_depth using BFS/DFS.
        Keep iteration shallow to avoid timeout.
        """
        paths = []
        
        for start in non_empty:
            visited = {start}
            stack = [(start, [start])]
            
            while stack:
                (r, c), current_path = stack.pop()
                
                if len(current_path) >= 2:
                    paths.append(current_path[:])
                
                # Limit depth to avoid timeout
                if len(current_path) >= max_depth:
                    continue
                
                # Explore neighbors
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) not in visited and (nr, nc) in non_empty:
                        visited.add((nr, nc))
                        stack.append(((nr, nc), current_path + [(nr, nc)]))
                        visited.remove((nr, nc))
        
        return paths

    def _find_words_for_path(self, path_letters: List[str]) -> Set[str]:
        """
        Find all dictionary words of valid length for this path.
        Valid length: len(path) <= len(word) <= 2 * len(path)
        """
        path_len = len(path_letters)
        min_len = path_len
        max_len = 2 * path_len
        
        candidates = set()
        for length in range(min_len, max_len + 1):
            if length in self.word_by_length:
                candidates.update(self.word_by_length[length])
        
        return candidates

    def _is_valid_move(self, path_letters: List[str], word: str) -> bool:
        """Check if word is a valid subsequence of path_letters."""
        word_idx = 0
        for letter in path_letters:
            if word_idx < len(word) and word[word_idx] == letter:
                word_idx += 1
        
        # All letters in word must be matched
        return word_idx == len(word)

    def _calculate_score(self, path: List[Tuple[int, int]], path_letters: List[str], word: str) -> int:
        """
        Score = 10 + (10 × cleared cells)
        Cleared cells = len(path) - extras
        Extras = len(word) - len(path)
        """
        extras = len(word) - len(path)
        cleared_cells = len(path) - extras
        score = 10 + (10 * cleared_cells)
        return score
