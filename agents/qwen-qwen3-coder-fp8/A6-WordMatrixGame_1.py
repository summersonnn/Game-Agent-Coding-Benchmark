"""
Agent Code: A6-WordMatrixGame
Model: qwen/qwen3-coder@preset/fp8
Run: 1
Generated: 2026-02-13 22:39:54
"""

from collections import deque

import random
from collections import deque

class WordMatrixAgent:
    def __init__(self, name):
        """
        Initialize your agent.
        Pre-process the dictionary here for fast lookups.
        """
        self.name = name
        self.dictionary = self.load_words()
        # Precompute word patterns for faster subsequence matching
        self.word_patterns = {}
        for word in self.dictionary:
            if len(word) <= 8:  # Max path length is 16, max word length is 32
                pattern = self.get_pattern_key(word)
                if pattern not in self.word_patterns:
                    self.word_patterns[pattern] = []
                self.word_patterns[pattern].append(word)
        
        # Define directions for adjacent cells (no diagonals)
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def load_words(self):
        """
        Load dictionary words. In a real implementation, this would load from a file.
        For this example, we'll return a representative set.
        """
        # This is a placeholder - in practice, this would load a real dictionary
        common_words = {
            'cat', 'dog', 'bat', 'rat', 'hat', 'mat', 'fat', 'sat', 'pat', 'vat',
            'car', 'bar', 'far', 'jar', 'tar', 'war', 'star', 'part', 'cart', 'care',
            'team', 'mean', 'bean', 'dean', 'lean', 'sean', 'tear', 'dear', 'bear', 'pear',
            'read', 'lead', 'head', 'dead', 'bread', 'ready', 'reader', 'leader', 'headed',
            'coat', 'boat', 'goat', 'float', 'throat', 'throaty', 'chart', 'charter',
            'start', 'smart', 'part', 'party', 'partly', 'garden', 'guard', 'danger',
            'water', 'later', 'maker', 'taken', 'token', 'broken', 'spoken', 'woken',
            'light', 'fight', 'night', 'right', 'sight', 'tight', 'flight', 'bright',
            'house', 'mouse', 'louse', 'spouse', 'course', 'source', 'force', 'horse',
            'place', 'face', 'case', 'base', 'race', 'pace', 'lace', 'mace', 'ace',
            'game', 'name', 'same', 'frame', 'flame', 'blame', 'claim', 'aim',
            'time', 'lime', 'crime', 'prime', 'grime', 'chime', 'rhyme', 'scheme',
            'love', 'move', 'glove', 'above', 'cover', 'rover', 'lover', 'driver',
            'tree', 'free', 'three', 'wheel', 'sweet', 'sheet', 'street', 'fleet',
            'word', 'sword', 'floor', 'door', 'poor', 'floor', 'root', 'boot', 'foot',
            'hand', 'land', 'sand', 'band', 'stand', 'under', 'number', 'wonder',
            'work', 'fork', 'pork', 'park', 'dark', 'mark', 'bark', 'lark',
            'fire', 'wire', 'tire', 'hire', 'sire', 'dire', 'fire', 'figure',
            'card', 'hard', 'yard', 'lard', 'bard', 'ward', 'award', 'warden',
            'fish', 'dish', 'wish', 'dish', 'shot', 'spot', 'stop', 'top',
            'book', 'look', 'took', 'hook', 'cook', 'foot', 'boot', 'root',
            'blue', 'true', 'clue', 'glue', 'flew', 'grew', 'threw', 'shoe',
            'red', 'bed', 'fed', 'led', 'head', 'dead', 'read', 'bread',
            'green', 'seen', 'been', 'ween', 'keen', 'mean', 'lean', 'bean',
            'black', 'back', 'lack', 'pack', 'track', 'crack', 'stack', 'attack',
            'white', 'light', 'night', 'right', 'sight', 'tight', 'flight', 'bright',
            'small', 'wall', 'call', 'fall', 'ball', 'hall', 'tall', 'mall',
            'large', 'charge', 'barge', 'marge', 'target', 'garter', 'starter',
            'sound', 'round', 'ground', 'pound', 'wound', 'found', 'hound',
            'young', 'strong', 'wrong', 'song', 'long', 'along', 'belong',
            'good', 'wood', 'stood', 'understood', 'food', 'mood', 'flood',
            'great', 'seat', 'meat', 'heat', 'beat', 'neat', 'eat', 'wheat',
            'world', 'word', 'sword', 'floor', 'door', 'poor', 'floor'
        }
        return common_words

    def get_pattern_key(self, word):
        """Generate a pattern key for a word to group similar words."""
        # Sort characters to create a pattern for quick lookup
        return ''.join(sorted(set(word)))

    def is_valid_path(self, path, board):
        """Check if a path is valid according to game rules."""
        if len(path) < 2:
            return False
        
        # Check if all cells are within bounds and not empty
        for r, c in path:
            if not (0 <= r < 4 and 0 <= c < 4) or board[r][c] == "":
                return False
        
        # Check if consecutive cells are adjacent and no cell is visited twice
        visited = set()
        for i, (r, c) in enumerate(path):
            if (r, c) in visited:
                return False
            visited.add((r, c))
            
            if i > 0:
                prev_r, prev_c = path[i-1]
                # Check if adjacent (horizontal or vertical only)
                if not ((abs(r - prev_r) == 1 and c == prev_c) or 
                        (abs(c - prev_c) == 1 and r == prev_r)):
                    return False
        
        return True

    def get_path_letters(self, path, board):
        """Extract letters from a path."""
        return [board[r][c] for r, c in path]

    def is_subsequence(self, sub, word):
        """Check if sub is a subsequence of word."""
        i = 0  # pointer for sub
        for char in word:
            if i < len(sub) and sub[i] == char:
                i += 1
        return i == len(sub)

    def find_words_for_path(self, path_letters):
        """Find valid words that match the path letters as a subsequence."""
        path_str = ''.join(path_letters)
        path_pattern = self.get_pattern_key(path_str)
        
        valid_words = []
        
        # Check words with patterns that match or contain our path pattern
        for pattern, words in self.word_patterns.items():
            # If path pattern is a subset of word pattern
            if all(c in pattern for c in path_pattern):
                for word in words:
                    if (len(word) >= len(path_letters) and 
                        len(word) <= 2 * len(path_letters) and
                        self.is_subsequence(path_letters, word)):
                        valid_words.append(word)
        
        return valid_words

    def dfs_paths(self, board, start_r, start_c, max_length=8):
        """Find all valid paths starting from a given cell using DFS."""
        paths = []
        stack = [([(start_r, start_c)], board[start_r][start_c])]  # (path, word_so_far)
        
        while stack:
            path, word = stack.pop()
            
            if len(path) >= 2:
                paths.append(list(path))
                
            if len(path) >= max_length:
                continue
                
            r, c = path[-1]
            for dr, dc in self.directions:
                nr, nc = r + dr, c + dc
                
                # Check bounds and if cell is already in path
                if (0 <= nr < 4 and 0 <= nc < 4 and 
                    board[nr][nc] != "" and 
                    (nr, nc) not in path):
                    
                    new_path = list(path) + [(nr, nc)]
                    stack.append((new_path, word + board[nr][nc]))
        
        return paths

    def find_all_valid_moves(self, board):
        """Find all possible valid moves on the board."""
        moves = []
        
        # For each non-empty cell, try to find paths starting from it
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    # Find all paths starting from this cell
                    paths = self.dfs_paths(board, r, c)
                    
                    for path in paths:
                        if self.is_valid_path(path, board):
                            path_letters = self.get_path_letters(path, board)
                            valid_words = self.find_words_for_path(path_letters)
                            
                            for word in valid_words:
                                moves.append((path, word))
        
        return moves

    def evaluate_move(self, path, word, board):
        """Evaluate a move based on potential score and strategy."""
        # Calculate how many cells will be cleared
        path_letters = self.get_path_letters(path, board)
        extra_letters = len(word) - len(path_letters)
        cleared_cells = len(path) - extra_letters if extra_letters <= len(path) else 0
        
        # Prefer moves that clear more cells (higher score)
        # Also prefer shorter words when possible to maximize clearing
        return cleared_cells * 10 + (len(path) - extra_letters) - len(word) / 10

    def make_move(self, board, scores, total_passes):
        """
        Called when it's your turn. Single attempt only.
        """
        # If too many passes, be more conservative
        if total_passes >= 4:
            # Try to find any valid move, even if not optimal
            pass
        
        # Find all valid moves
        valid_moves = self.find_all_valid_moves(board)
        
        if not valid_moves:
            return "PASS"
        
        # Evaluate and rank moves
        ranked_moves = []
        for path, word in valid_moves:
            score = self.evaluate_move(path, word, board)
            ranked_moves.append((score, path, word))
        
        # Sort by score (descending)
        ranked_moves.sort(reverse=True)
        
        # If we have good moves, take the best one
        if ranked_moves and ranked_moves[0][0] > 0:
            _, best_path, best_word = ranked_moves[0]
            return (best_path, best_word)
        
        # If all moves have negative evaluation, pass
        return "PASS"
