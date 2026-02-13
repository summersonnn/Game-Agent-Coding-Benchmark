"""
Agent Code: A6-WordMatrixGame
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-13 22:39:54
"""

from collections import defaultdict
from typing import List, Tuple, Set, Dict, Union

import random
from collections import defaultdict
from typing import List, Tuple, Set, Dict, Union

class WordMatrixAgent:
    def __init__(self, name: str, dictionary: Set[str] = None):
        """
        Initialize the agent with a name and optional dictionary.
        If dictionary is None, it should be loaded via the game environment.
        """
        self.name = name
        
        # Load dictionary (in actual game, this is provided)
        if dictionary is None:
            self.words = self._load_default_dictionary()
        else:
            self.words = list(dictionary)
        
        self.word_set = set(self.words)
        
        # Map word length to list of indices for quick length filtering
        self.words_by_length = defaultdict(list)
        for idx, word in enumerate(self.words):
            self.words_by_length[len(word)].append(idx)
        
        # Build bigram index: map (char1, char2) -> set of word indices
        # where char1 appears before char2 in the word
        self.bigram_index = defaultdict(set)
        for idx, word in enumerate(self.words):
            # For each word, record all ordered pairs of characters
            word_len = len(word)
            for i in range(word_len):
                for j in range(i + 1, word_len):
                    self.bigram_index[(word[i], word[j])].add(idx)
    
    def _load_default_dictionary(self) -> List[str]:
        """Placeholder for dictionary loading. In the actual game environment, 
        the dictionary is provided to the constructor."""
        return []
    
    def _get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Return orthogonal neighbors (up, down, left, right) within 4x4 grid."""
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4:
                neighbors.append((nr, nc))
        return neighbors
    
    def _find_best_word(self, path_letters: List[str]) -> Union[str, None]:
        """
        Find the shortest dictionary word that contains path_letters as a subsequence.
        Returns None if no valid word exists.
        """
        path_str = ''.join(path_letters)
        path_len = len(path_str)
        
        # Quick check: is the path itself a word? (Best case - clears all cells)
        if path_str in self.word_set:
            return path_str
        
        if path_len < 2:
            return None
        
        # Build consecutive pairs from the path
        pairs = [(path_str[i], path_str[i+1]) for i in range(path_len - 1)]
        
        # Find intersection of all bigram sets
        # Start with the smallest set to minimize intersection work
        candidate_sets = [self.bigram_index[pair] for pair in pairs if pair in self.bigram_index]
        if len(candidate_sets) < len(pairs):
            return None  # Some pair doesn't exist in any word
        
        # Start with the smallest set for efficiency
        candidates = min(candidate_sets, key=len).copy()
        for s in candidate_sets:
            if s is not candidates:
                candidates &= s
                if not candidates:
                    return None
        
        # Filter candidates by length constraint and find shortest
        # Valid word length: path_len <= word_len <= 2*path_len
        min_wlen = path_len
        max_wlen = min(2 * path_len, 16)  # Cap at 16 for practicality
        
        best_word = None
        best_len = float('inf')
        
        # Check words by increasing length to find shortest faster
        for wlen in range(min_wlen, max_wlen + 1):
            for idx in self.words_by_length[wlen]:
                if idx in candidates:
                    word = self.words[idx]
                    # Verify subsequence (bigram check is necessary but not sufficient 
                    # for non-consecutive path letters, though usually sufficient)
                    # Do full check to be safe
                    if self._is_subsequence(path_str, word):
                        return word  # Return immediately since we check shortest lengths first
        
        return best_word
    
    def _is_subsequence(self, sub: str, word: str) -> bool:
        """Check if sub is a subsequence of word using two-pointer technique."""
        if len(sub) > len(word):
            return False
        sub_idx = 0
        word_idx = 0
        sub_len = len(sub)
        word_len = len(word)
        
        while sub_idx < sub_len and word_idx < word_len:
            if sub[sub_idx] == word[word_idx]:
                sub_idx += 1
            word_idx += 1
        
        return sub_idx == sub_len
    
    def make_move(self, board: List[List[str]], scores: Dict[str, int], total_passes: int):
        """
        Determine the best move given the current board state.
        
        Returns:
            tuple: (path, word) where path is list of (row, col) tuples
            str: "PASS" if no valid move found
        """
        best_path = None
        best_word = None
        best_score = -float('inf')
        
        # DFS from each starting cell
        # We use a stack to avoid recursion limits and allow early termination
        for r in range(4):
            for c in range(4):
                if board[r][c] == "":
                    continue
                
                # Stack items: (current_row, current_col, path_list, visited_set)
                stack = [(r, c, [(r, c)], {(r, c)})]
                
                while stack:
                    cr, cc, path, visited = stack.pop()
                    path_len = len(path)
                    
                    # Evaluate path if length >= 2
                    if path_len >= 2:
                        letters = [board[pr][pc] for pr, pc in path]
                        word = self._find_best_word(letters)
                        
                        if word:
                            word_len = len(word)
                            # Calculate score: 10 + 10 * (2*path_len - word_len)
                            cleared_cells = 2 * path_len - word_len
                            score = 10 + 10 * cleared_cells
                            
                            if score > best_score:
                                best_score = score
                                best_path = path[:]
                                best_word = word
                                
                                # If we found a perfect match (clears all cells) with good length,
                                # we can potentially return early, but let's search a bit more
                                # for longer perfect matches
                                if word_len == path_len and path_len >= 6:
                                    # This is already excellent (score >= 70), return immediately
                                    return (best_path, best_word)
                    
                    # Extend path (limit depth to 8 for performance)
                    if path_len < 8:
                        for nr, nc in self._get_neighbors(cr, cc):
                            if (nr, nc) not in visited and board[nr][nc] != "":
                                new_visited = set(visited)
                                new_visited.add((nr, nc))
                                stack.append((nr, nc, path + [(nr, nc)], new_visited))
        
        if best_path and best_word:
            return (best_path, best_word)
        else:
            return "PASS"
