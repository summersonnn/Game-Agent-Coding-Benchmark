"""
Agent Code: A6-WordMatrixGame
Model: qwen-qwen3-max-thinking
Run: 1
Generated: 2026-02-12 19:13:59
"""

from collections import defaultdict
from typing import List, Tuple, Dict, Optional

class WordMatrixAgent:
    def __init__(self, name: str):
        self.name = name
        self.dictionary = load_words()  # Provided function returning ~466k words
        self.words_by_length = defaultdict(list)
        for word in self.dictionary:
            self.words_by_length[len(word)].append(word)
        self.max_word_length = max((len(w) for w in self.dictionary), default=0)
        # Precompute small-word cache for common short sequences (optimization)
        self._short_word_cache = {}
        for wl in range(2, 7):  # Cache for paths of length 2-6
            if wl in self.words_by_length:
                self._short_word_cache[wl] = self.words_by_length[wl][:]  # Copy for safety

    def is_subsequence(self, subseq: str, word: str) -> bool:
        """Check if subseq is a subsequence of word (order-preserving)."""
        word_iter = iter(word)
        return all(char in word_iter for char in subseq)
    
    def has_adjacent_nonempty(self, board: List[List[str]]) -> bool:
        """Quick check: are there any adjacent non-empty cells?"""
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for r in range(4):
            for c in range(4):
                if board[r][c]:
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 4 and 0 <= nc < 4 and board[nr][nc]:
                            return True
        return False

    def _generate_paths(self, board: List[List[str]], max_len: int = 8) -> List[Tuple[List[Tuple[int, int]], str]]:
        """Generate all valid paths (length 2 to max_len) with their letter sequences."""
        paths = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        def dfs(r: int, c: int, path: List[Tuple[int, int]], letters: List[str], visited: List[List[bool]]):
            if len(path) >= max_len:
                return
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and not visited[nr][nc] and board[nr][nc]:
                    visited[nr][nc] = True
                    new_path = path + [(nr, nc)]
                    new_letters = letters + [board[nr][nc]]
                    
                    if len(new_path) >= 2:
                        paths.append((new_path, ''.join(new_letters)))
                    
                    dfs(nr, nc, new_path, new_letters, visited)
                    visited[nr][nc] = False
        
        for r in range(4):
            for c in range(4):
                if board[r][c]:
                    visited = [[False] * 4 for _ in range(4)]
                    visited[r][c] = True
                    dfs(r, c, [(r, c)], [board[r][c]], visited)
        
        return paths

    def _find_best_word(self, letters: str, path_len: int) -> Optional[Tuple[str, int]]:
        """
        Find best word for letter sequence: minimal extra letters (wl - path_len).
        Returns (word, extra_letters) or None if no match.
        """
        cache_key = (letters, path_len)
        if cache_key in self._short_word_cache and path_len <= 6:
            # Use pre-filtered short words for speed
            candidates = self._short_word_cache[path_len]
            for wl_offset in range(0, path_len + 1):  # Check exact match first, then +1, +2...
                wl = path_len + wl_offset
                if wl > min(2 * path_len, self.max_word_length):
                    break
                for word in candidates if wl == path_len else self.words_by_length.get(wl, []):
                    if self.is_subsequence(letters, word):
                        return (word, wl_offset)
            return None
        
        # General case: check lengths from path_len to 2*path_len
        for extra in range(0, path_len + 1):  # extra = wl - path_len
            wl = path_len + extra
            if wl > self.max_word_length:
                break
            if wl not in self.words_by_length:
                continue
            for word in self.words_by_length[wl]:
                if self.is_subsequence(letters, word):
                    return (word, extra)
        return None

    def make_move(self, board: List[List[str]], scores: Dict[str, int], total_passes: int) -> Tuple[List[Tuple[int, int]], str] | str:
        # Immediate PASS if no adjacent non-empty cells exist
        if not self.has_adjacent_nonempty(board):
            return "PASS"
        
        # Safety: near game-end (5+ passes), only play exact-match moves to avoid -10 risk
        require_exact_match = (total_passes >= 5)
        
        # Generate candidate paths (length 2-8), sorted by potential max score (longer = higher potential)
        candidate_paths = self._generate_paths(board, max_len=8)
        candidate_paths.sort(key=lambda x: len(x[0]), reverse=True)  # Prioritize longer paths
        
        best_score = -1
        best_move = None
        
        for path, letters in candidate_paths:
            L = len(path)
            result = self._find_best_word(letters, L)
            if not result:
                continue
            
            word, extra = result
            if require_exact_match and extra > 0:
                continue  # Skip non-exact matches when passes are critical
            
            cleared_cells = L - extra  # = 2L - (L + extra)
            score = 10 + 10 * cleared_cells
            
            # Prefer moves with higher score; break early if perfect max-length path found
            if score > best_score:
                best_score = score
                best_move = (path, word)
                # Early termination: perfect score for longest possible path (8 cells)
                if score == 90 and L == 8:  # 10 + 10*8 = 90
                    break
        
        return best_move if best_move is not None else "PASS"