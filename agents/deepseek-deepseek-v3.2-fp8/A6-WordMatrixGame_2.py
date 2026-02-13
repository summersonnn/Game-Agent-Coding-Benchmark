"""
Agent Code: A6-WordMatrixGame
Model: deepseek/deepseek-v3.2@preset/fp8
Run: 2
Generated: 2026-02-13 22:39:54
"""

from collections import defaultdict, deque
from typing import List, Tuple, Set, Dict, Optional
import math

import random
from collections import defaultdict, deque
from typing import List, Tuple, Set, Dict, Optional
import math

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        
        # Load dictionary
        self.dictionary = self.load_words()
        
        # Preprocess dictionary for faster lookups
        self.word_set = set(self.dictionary)
        self.words_by_length = defaultdict(set)
        for word in self.dictionary:
            self.words_by_length[len(word)].add(word)
            
        # Build prefix trie for faster word validation
        self.trie = {}
        for word in self.dictionary:
            node = self.trie
            for char in word:
                node = node.setdefault(char, {})
            node['#'] = True  # Mark end of word
            
        # Cache for found words on boards
        self.word_cache = {}
        
        # Game state tracking
        self.opponent_name = None
        
        # Strategy parameters
        self.min_path_length = 2
        self.max_path_length = 8  # Reasonable limit for 4x4 board
        self.timeout_threshold = 0.95  # Safety margin for timeout
        self.pass_threshold = 0  # Score below which we consider passing
        
    def load_words(self):
        """Load dictionary words"""
        # This would be replaced with the actual dictionary loading
        # For now, we'll use a subset of common words
        common_words = {
            'cat', 'dog', 'bat', 'rat', 'hat', 'mat', 'sat', 'pat', 'fat', 'vat',
            'car', 'bar', 'far', 'tar', 'jar', 'war', 'par', 'mar', 'star', 'cart',
            'dart', 'part', 'mart', 'tart', 'wart', 'barn', 'darn', 'yarn', 'warn',
            'turn', 'burn', 'churn', 'learn', 'earn', 'yearn', 'heart', 'hearth',
            'earth', 'dearth', 'pearl', 'world', 'sword', 'board', 'hoard', 'guard',
            'hard', 'yard', 'card', 'ward', 'bard', 'lard', 'nard', 'sard', 'tard',
            'word', 'cord', 'ford', 'lord', 'sord', 'bird', 'gird', 'third', 'first',
            'thirst', 'worst', 'burst', 'curst', 'durant', 'during', 'daring', 'caring',
            'paring', 'taring', 'waring', 'starring', 'starting', 'staring', 'storing',
            'storming', 'forming', 'warming', 'warning', 'earning', 'learning',
            'yearning', 'burning', 'turning', 'churning', 'heartening', 'hearkening',
            'boardroom', 'guardroom', 'hardwood', 'yardstick', 'cardboard', 'wardrobe',
            'barnyard', 'darned', 'yarned', 'warned', 'turned', 'burned', 'churned',
            'learned', 'earned', 'yearned', 'hearted', 'earthed', 'pearled', 'worded',
            'corded', 'forded', 'lorded', 'birded', 'girded', 'thirded', 'firsted'
        }
        return common_words
    
    def is_valid_word(self, word: str) -> bool:
        """Check if word exists in dictionary using trie"""
        node = self.trie
        for char in word:
            if char not in node:
                return False
            node = node[char]
        return '#' in node
    
    def get_all_neighbors(self, pos: Tuple[int, int], board: List[List[str]]) -> List[Tuple[int, int]]:
        """Get all valid adjacent positions"""
        r, c = pos
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4 and board[nr][nc]:
                neighbors.append((nr, nc))
        return neighbors
    
    def find_all_paths(self, board: List[List[str]], min_len: int = 2, max_len: int = 8) -> List[List[Tuple[int, int]]]:
        """Find all valid paths on the board using BFS"""
        paths = []
        non_empty_cells = [(r, c) for r in range(4) for c in range(4) if board[r][c]]
        
        for start in non_empty_cells:
            # BFS queue: (current_path, current_position, visited_set)
            queue = deque([([start], start, {start})])
            
            while queue:
                path, current_pos, visited = queue.popleft()
                
                # Add path if long enough
                if len(path) >= min_len:
                    paths.append(path.copy())
                
                # Stop if reached max length
                if len(path) >= max_len:
                    continue
                
                # Explore neighbors
                for neighbor in self.get_all_neighbors(current_pos, board):
                    if neighbor not in visited:
                        new_path = path + [neighbor]
                        new_visited = visited | {neighbor}
                        queue.append((new_path, neighbor, new_visited))
        
        return paths
    
    def path_to_string(self, path: List[Tuple[int, int]], board: List[List[str]]) -> str:
        """Convert path to string of letters"""
        return ''.join(board[r][c] for r, c in path)
    
    def is_subsequence(self, pattern: str, word: str) -> bool:
        """Check if pattern is a subsequence of word"""
        i = 0
        for char in word:
            if i < len(pattern) and char == pattern[i]:
                i += 1
        return i == len(pattern)
    
    def find_matching_words(self, pattern: str, max_len: int) -> List[str]:
        """Find words that contain pattern as subsequence"""
        matching_words = []
        pattern_len = len(pattern)
        
        # Check words of appropriate length
        for length in range(pattern_len, min(max_len, 12) + 1):  # 12 is 2*6
            for word in self.words_by_length.get(length, []):
                if self.is_subsequence(pattern, word):
                    matching_words.append(word)
        
        return matching_words
    
    def evaluate_move(self, path: List[Tuple[int, int]], word: str) -> int:
        """Calculate score for a move"""
        path_len = len(path)
        word_len = len(word)
        cleared_cells = max(0, 2 * path_len - word_len)
        return 10 + 10 * cleared_cells
    
    def get_board_key(self, board: List[List[str]]) -> str:
        """Create a string representation of the board for caching"""
        return ''.join(''.join(cell or '.' for cell in row) for row in board)
    
    def find_best_move(self, board: List[List[str]], scores: Dict[str, int], total_passes: int) -> Tuple[List[Tuple[int, int]], str]:
        """Find the best move for current board"""
        # Check if opponent is identified
        if not self.opponent_name:
            for name in scores:
                if name != self.name:
                    self.opponent_name = name
                    break
        
        # Get all valid paths
        all_paths = self.find_all_paths(board, self.min_path_length, self.max_path_length)
        
        if not all_paths:
            return None
        
        best_score = -float('inf')
        best_move = None
        
        # Evaluate each path
        for path in all_paths:
            pattern = self.path_to_string(path, board)
            max_word_len = min(2 * len(path), 12)  # Cap at reasonable length
            
            # Find matching words
            matching_words = self.find_matching_words(pattern, max_word_len)
            
            for word in matching_words:
                score = self.evaluate_move(path, word)
                
                # Bonus for clearing more cells
                cleared_cells = max(0, 2 * len(path) - len(word))
                score += cleared_cells * 2  # Bonus for efficiency
                
                # Penalty for long words (higher risk of not matching letters)
                if len(word) > len(path) + 2:
                    score -= (len(word) - len(path) - 2) * 3
                
                # Consider game state
                my_score = scores.get(self.name, 0)
                opponent_score = scores.get(self.opponent_name, 0)
                
                # If behind, take more risks
                if my_score < opponent_score:
                    score += (opponent_score - my_score) // 10
                
                # If ahead, play safer
                elif my_score > opponent_score + 20:
                    score -= 5
                
                # Update best move
                if score > best_score:
                    best_score = score
                    best_move = (path, word)
        
        return best_move
    
    def make_move(self, board: List[List[str]], scores: Dict[str, int], total_passes: int):
        """
        Main move-making function
        """
        try:
            # Check if we should pass
            if total_passes >= 5:  # Game might end soon
                # Try to make any move to avoid ending with pass
                move = self.find_best_move(board, scores, total_passes)
                if move:
                    return move
            
            # Check if board is sparse
            non_empty = sum(1 for r in range(4) for c in range(4) if board[r][c])
            if non_empty < 4:  # Very sparse board
                # Be more aggressive
                move = self.find_best_move(board, scores, total_passes)
                if move and self.evaluate_move(move[0], move[1]) > 20:
                    return move
                return "PASS"
            
            # Normal strategy
            move = self.find_best_move(board, scores, total_passes)
            
            if move:
                path, word = move
                # Verify move is valid
                if (2 <= len(path) <= 8 and 
                    len(path) <= len(word) <= 2 * len(path) and
                    self.is_valid_word(word) and
                    self.is_subsequence(self.path_to_string(path, board), word)):
                    
                    # Double-check path validity
                    for i in range(len(path) - 1):
                        r1, c1 = path[i]
                        r2, c2 = path[i + 1]
                        if abs(r1 - r2) + abs(c1 - c2) != 1:
                            return "PASS"  # Invalid adjacency
                    
                    return (path, word)
            
            # If no good move found, pass
            return "PASS"
            
        except Exception as e:
            # Safety fallback - pass to avoid crash penalty
            return "PASS"
