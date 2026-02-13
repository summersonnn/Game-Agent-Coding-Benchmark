"""
Agent Code: A6-WordMatrixGame
Model: z-ai-glm-5-fp8-speedy
Run: 2
Generated: 2026-02-13 22:39:54
"""

import sys

# Increase recursion depth just in case, though DFS is limited by path length
sys.setrecursionlimit(2000)

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        # In a real environment, load_words() is provided. 
        # We define it here for standalone functionality if needed.
        self.dictionary = self.load_words()
        self.max_path_len = 9 # Limits search space to ensure fast turns

    def load_words(self):
        """
        Loads words from a file or returns a default set.
        The problem description implies a 'load_words' function is available
        in the environment returning ~466k words.
        """
        try:
            # Try to use the external function if available
            return load_words() 
        except NameError:
            # Fallback: simple loader for testing
            try:
                with open('words.txt', 'r') as f:
                    return set(line.strip().lower() for line in f)
            except FileNotFoundError:
                # Minimal set to prevent crash if no dict file
                return set(["cat", "dog", "coat", "word", "matrix", "game", "player", "board", "score", "path"])

    def get_neighbors(self, r, c):
        """Yields valid neighbor coordinates (up, down, left, right)."""
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4:
                yield nr, nc

    def make_move(self, board, scores, total_passes):
        """
        Determines the best move by searching for paths and matching words.
        """
        all_paths = []
        
        # 1. Generate Paths (DFS)
        # We search for paths of length 2 up to self.max_path_len
        for r in range(4):
            for c in range(4):
                if board[r][c] == "":
                    continue
                
                # Stack: (row, col, path_coords, current_string, visited_set)
                # Using a set for visited is efficient enough for depth 9
                stack = [(r, c, [(r, c)], board[r][c], {(r, c)})]
                
                while stack:
                    curr_r, curr_c, path, s, visited = stack.pop()
                    
                    # Store paths of valid length (>= 2)
                    if len(path) >= 2:
                        all_paths.append((path, s))
                    
                    # Stop if max length reached
                    if len(path) >= self.max_path_len:
                        continue
                    
                    # Expand neighbors
                    for nr, nc in self.get_neighbors(curr_r, curr_c):
                        if (nr, nc) not in visited and board[nr][nc] != "":
                            new_path = path + [(nr, nc)]
                            new_s = s + board[nr][nc]
                            new_visited = set(visited)
                            new_visited.add((nr, nc))
                            stack.append((nr, nc, new_path, new_s, new_visited))

        # 2. Evaluate Paths
        # Sort by length descending to find highest scoring opportunities first
        all_paths.sort(key=lambda x: len(x[1]), reverse=True)
        
        best_move = None
        best_score = -1

        for path, s in all_paths:
            L = len(s)
            
            # Pruning: If the theoretical max score for this path length 
            # is not better than what we've already found, we can stop.
            # Max score for path length L is 10 + 10*L (exact match).
            if 10 + 10 * L <= best_score:
                break

            # --- Strategy: Prefer Exact Matches ---
            # An exact match (word == path string) clears all cells (L cells).
            # Score = 10 + 10 * L
            if s in self.dictionary:
                score = 10 + 10 * L
                if score > best_score:
                    best_score = score
                    best_move = (path, s)
                # Since we process longest paths first and exact match is the 
                # best possible outcome for a specific path string, 
                # we can skip other checks for this path.
                continue
            
            # --- Strategy: Check for Subsequence Matches (+1 letter) ---
            # We try to form a word by inserting one letter into the path string.
            # Score = 10 + 10 * (L - 1) = 10 * L
            # We only do this if it can beat our current best_score.
            if 10 * L > best_score:
                # Generate candidates by inserting a-z at any position
                # This creates words of length L+1
                found_plus_one = False
                for i in range(L + 1):
                    # Optimization: We can limit char search if needed, but 26 is small
                    for char_code in range(26):
                        char = chr(ord('a') + char_code)
                        candidate = s[:i] + char + s[i:]
                        if candidate in self.dictionary:
                            # Found a valid word of length L+1
                            # Cleared cells = 2*L - (L+1) = L-1
                            # Score = 10 + 10*(L-1)
                            score = 10 * L
                            if score > best_score:
                                best_score = score
                                best_move = (path, candidate)
                                found_plus_one = True
                                break
                    if found_plus_one:
                        break
            
            # Note: We do not check +2 letters or more because:
            # 1. Computational cost is high (26^2 * L^2).
            # 2. Score drops significantly (10*L - 10, etc.).
            # 3. Longer paths found earlier likely offer better scores.

        if best_move:
            return best_move
        else:
            return "PASS"