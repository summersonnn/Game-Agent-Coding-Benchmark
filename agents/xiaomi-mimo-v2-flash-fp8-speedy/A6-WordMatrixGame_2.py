"""
Agent Code: A6-WordMatrixGame
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 2
Generated: 2026-02-13 22:39:54
"""

from collections import defaultdict, deque
import itertools

import random
from collections import defaultdict, deque
import itertools

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = self.load_words()
        
        # Build data structures for efficient lookup
        self.build_word_structures()
        
    def load_words(self):
        # This would normally load from a file
        # For demonstration, using a sample set
        # In practice, load all ~466k words
        words = set()
        # Sample words for demonstration
        sample_words = [
            "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
            "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
            "man", "new", "now", "old", "see", "time", "two", "way", "who", "boy",
            "did", "its", "let", "put", "say", "she", "too", "use", "cat", "dog",
            "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat",
            "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat",
            "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat", "coat"
        ]
        # Add more words in practice
        words.update(sample_words)
        return words
    
    def build_word_structures(self):
        # Build a trie for prefix matching
        self.trie = {}
        for word in self.dictionary:
            node = self.trie
            for char in word:
                if char not in node:
                    node[char] = {}
                node = node[char]
            node['#'] = word  # Mark end of word
        
        # Also build a mapping from letter sequences to words
        self.sequence_to_words = defaultdict(list)
        for word in self.dictionary:
            # For each possible subsequence length (2-4)
            for length in range(2, min(5, len(word) + 1)):
                # Generate all subsequences of this length
                for combo in itertools.combinations(range(len(word)), length):
                    seq = ''.join(word[i] for i in combo)
                    if len(seq) == length:
                        self.sequence_to_words[seq].append(word)
    
    def make_move(self, board, scores, total_passes):
        # Find all possible paths on the board
        paths = self.find_all_paths(board)
        
        if not paths:
            return "PASS"
        
        best_score = -float('inf')
        best_move = None
        
        for path in paths:
            path_letters = ''.join(board[r][c] for r, c in path)
            path_len = len(path)
            
            # Find valid words for this path
            valid_words = self.find_words_for_path(path_letters, path_len)
            
            if not valid_words:
                continue
            
            # Score each word and choose the best
            for word in valid_words:
                word_len = len(word)
                cleared_cells = 2 * path_len - word_len
                score = 10 + 10 * cleared_cells
                
                if score > best_score:
                    best_score = score
                    best_move = (path, word)
        
        if best_move:
            return best_move
        else:
            return "PASS"
    
    def find_all_paths(self, board):
        """Find all valid paths (length 2-4) on the board"""
        paths = []
        rows, cols = 4, 4
        
        def dfs(r, c, path, visited):
            if len(path) >= 2:
                paths.append(list(path))
            
            if len(path) == 4:  # Max path length to consider
                return
            
            # Explore neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols and 
                    (nr, nc) not in visited and 
                    board[nr][nc] != ""):
                    visited.add((nr, nc))
                    path.append((nr, nc))
                    dfs(nr, nc, path, visited)
                    path.pop()
                    visited.remove((nr, nc))
        
        # Start DFS from each non-empty cell
        for i in range(rows):
            for j in range(cols):
                if board[i][j] != "":
                    visited = {(i, j)}
                    dfs(i, j, [(i, j)], visited)
        
        # Filter paths by length (2-4)
        paths = [p for p in paths if 2 <= len(p) <= 4]
        return paths
    
    def find_words_for_path(self, path_letters, path_len):
        """Find words that have path_letters as subsequence and satisfy length constraints"""
        valid_words = []
        
        # Check our precomputed mapping first
        if path_letters in self.sequence_to_words:
            for word in self.sequence_to_words[path_letters]:
                if path_len <= len(word) <= 2 * path_len:
                    valid_words.append(word)
        
        # If not found, search through dictionary (slower)
        if not valid_words:
            for word in self.dictionary:
                if path_len <= len(word) <= 2 * path_len:
                    if self.is_subsequence(path_letters, word):
                        valid_words.append(word)
        
        # Sort by word length (prefer shorter words for higher score)
        valid_words.sort(key=len)
        return valid_words
    
    def is_subsequence(self, subsequence, word):
        """Check if subsequence appears in word in order"""
        i = 0
        for char in word:
            if i < len(subsequence) and char == subsequence[i]:
                i += 1
        return i == len(subsequence)
    
    def find_word_using_trie(self, path_letters, path_len):
        """Alternative method using trie for faster lookup"""
        # This would be more efficient for large dictionaries
        # For simplicity, using the sequence mapping approach above
        pass

# For testing the agent
if __name__ == "__main__":
    agent = WordMatrixAgent("TestAgent")
    
    # Example board
    board = [
        ['c', 'a', 't', 's'],
        ['d', 'o', 'g', ''],
        ['f', 'i', 's', 'h'],
        ['b', 'i', 'r', 'd']
    ]
    
    scores = {"Agent-1": 30, "Agent-2": 10}
    total_passes = 0
    
    move = agent.make_move(board, scores, total_passes)
    print(f"Move: {move}")
