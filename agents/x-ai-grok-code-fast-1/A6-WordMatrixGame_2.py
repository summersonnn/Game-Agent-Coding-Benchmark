"""
Agent Code: A6-WordMatrixGame
Model: x-ai/grok-code-fast-1
Run: 2
Generated: 2026-02-12 19:13:59
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
        # Pre-process: filter and sort short words by length for efficiency
        self.short_words = [w for w in self.dictionary if len(w) <= 12]
        self.short_words.sort(key=len)

    def make_move(self, board, scores, total_passes):
        """
        Called when it's your turn. Single attempt only.

        Parameters:
        -----------
        board : list[list[str]]
            4x4 grid. Example: [['c','a','t','s'], ['d','o','g',''], ...]
        
        scores : dict
            Current scores. Example: {"Agent-1": 30, "Agent-2": 10}

        total_passes : int
            Number of consecutive passes/fails so far. Game ends at 6.

        Returns:
        --------
        tuple[list[tuple[int,int]], str] or str
            - A tuple (path, word) where path is a list of (row, col) coordinates.
            - OR the string "PASS" to skip turn.
        """
        def is_subsequence(sub, full):
            """Check if sub is a subsequence of full."""
            i = 0
            for char in full:
                if i < len(sub) and char == sub[i]:
                    i += 1
            return i == len(sub)

        def get_all_paths(board):
            """Generate all valid paths up to length 8."""
            paths = []
            def dfs(current_path, visited):
                if len(current_path) >= 2:
                    paths.append(current_path[:])
                if len(current_path) >= 8:
                    return
                last_r, last_c = current_path[-1]
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = last_r + dr, last_c + dc
                    if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and board[nr][nc] != "":
                        visited.add((nr, nc))
                        current_path.append((nr, nc))
                        dfs(current_path, visited)
                        current_path.pop()
                        visited.remove((nr, nc))
            for r in range(4):
                for c in range(4):
                    if board[r][c] != "":
                        dfs([(r, c)], set([(r, c)]))
            return paths

        paths = get_all_paths(board)
        best_score = -float('inf')  # Initialize to negative infinity
        best_move = "PASS"
        for path in paths:
            seq = [board[r][c] for r, c in path]
            for word in self.short_words:
                if len(word) < len(seq) or len(word) > 2 * len(seq):
                    continue
                if is_subsequence(seq, word):
                    cleared = 2 * len(seq) - len(word)
                    score = 10 + 10 * cleared
                    if score > best_score:
                        best_score = score
                        best_move = (path, word)
                    break  # Take the shortest valid word for this path
        return best_move
