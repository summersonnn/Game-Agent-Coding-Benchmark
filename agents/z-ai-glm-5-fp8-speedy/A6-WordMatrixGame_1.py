"""
Agent Code: A6-WordMatrixGame
Model: z-ai-glm-5-fp8-speedy
Run: 1
Generated: 2026-02-13 22:39:54
"""

import sys

# Increase recursion depth just in case for deep DFS on board
sys.setrecursionlimit(2000)

# Define the TrieNode structure for efficient prefix and subsequence checking
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        # The game environment provides a load_words function, 
        # but we assume standard set is loaded or mock it for standalone logic.
        # In the context of the game engine, we use the provided dictionary.
        try:
            # Attempt to load words if running standalone or if provided
            self.dictionary = load_words() 
        except NameError:
            # Fallback if load_words is not defined in the scope (e.g. testing snippet)
            # A small dummy dictionary for syntax checking
            self.dictionary = {"cat", "cats", "cart", "meow", "dog", "dogs", "god", "dot", "cot", "coat"}

        self.root = self._build_trie()

    def _build_trie(self):
        root = TrieNode()
        for word in self.dictionary:
            node = root
            for char in word:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.is_end_of_word = True
        return root

    def make_move(self, board, scores, total_passes):
        """
        Determines the best move for the current turn.
        Strategy:
        1. Try to find a path that exactly spells a word (k=0). 
           This yields the maximum score: 10 + 10 * len(path).
           We prioritize longer paths.
        2. If no exact match, try to find a path that forms a word with 
           a small number of extra letters (k > 0). 
           We search for small k (1, then 2, etc.) because score penalty 
           increases with k.
        3. If no valid move is found, return "PASS".
        """
        # 1. Search for exact matches (k=0)
        best_move = self._search_board(board, k=0)
        if best_move:
            return best_move

        # 2. Search for matches with extra letters (k=1, k=2)
        # We stop at k=2 because higher k yields low scores and search becomes expensive.
        # Score for k=1: 10 + 10*(L-1) = 10*L. Still decent for longer paths.
        # Score for k=2: 10 + 10*(L-2).
        for k in [1, 2]:
            best_move = self._search_board(board, k=k)
            if best_move:
                return best_move

        # 3. No move found
        return "PASS"

    def _search_board(self, board, k):
        """
        Performs a DFS on the board to find the highest scoring move 
        that requires exactly k extra letters.
        """
        rows, cols = 4, 4
        best_score = -1
        best_move = None
        
        # Directions: Up, Down, Left, Right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        def dfs(r, c, path, path_chars, visited, node):
            nonlocal best_score, best_move
            
            char = board[r][c]
            if char not in node.children:
                return

            # Move forward in Trie
            next_node = node.children[char]
            
            current_path = path + [(r, c)]
            current_path_chars = path_chars + char
            
            # Optimization: If current path length is small, but we need k extra letters,
            # we might be forming a word soon.
            
            # Check if we found a word that uses exactly k extra letters.
            # Word length W must be = Path length P + k.
            # Here, we have constructed P letters on the board.
            # We need to find if there exists a word in the Trie that:
            #   - Ends at current node (or deeper with k extra letters)
            #   - Length constraint: W = len(current_path) + k
            
            # Logic for k extra letters:
            # We are at depth `P` in the board path.
            # We are at depth `d` in the Trie.
            # Note: `d` can be >= P if we already inserted extra letters? 
            # Wait, the logic below for k > 0 is handled by the recursive step `consume_skip`.
            # BUT for k=0, `d` must equal `P`.
            
            # --- Case k = 0 (Path chars = Word chars) ---
            if k == 0:
                # If we are here, the path chars exactly match the Trie path so far.
                if next_node.is_end_of_word:
                    # Found a word of length len(current_path)
                    score = 10 + 10 * len(current_path)
                    if score > best_score:
                        best_score = score
                        best_move = (list(current_path), current_path_chars)
                
                # Continue DFS for longer paths
                # Pruning: if next_node has no children, stop.
                if not next_node.children:
                    return

                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        dfs(nr, nc, current_path, current_path_chars, visited, next_node)
                        visited.remove((nr, nc))

            # --- Case k > 0 (Need to insert extra letters) ---
            else:
                # We are at state (r,c) which just added a board char.
                # We need to check if we can complete a word with `k` remaining skips.
                # Pass `k` to the recursive search.
                # The `consume_skip` helper will handle inserting letters not on the board.
                
                # We pass `next_node` (Trie advanced by board char) and `k` remaining skips.
                self._search_with_skips(current_path, current_path_chars, next_node, k, best_score)
                # Note: _search_with_skips will update the outer `best_score` and `best_move`
                
                # Continue DFS on board (consuming 0 skips here)
                # The remaining skips must be used later.
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        dfs(nr, nc, current_path, current_path_chars, visited, next_node, k) # pass k to keep track?
                        # Actually, the `dfs` signature in the closure doesn't take k.
                        # We need to adapt.
                        visited.remove((nr, nc))

        # Re-defining DFS for cleaner integration of k
        # We use a unified DFS that tracks `skips_remaining`.
        
        def unified_dfs(r, c, path, path_chars, visited, node, skips_left):
            nonlocal best_score, best_move
            
            char = board[r][c]
            
            # Option 1: Consume the board character
            if char in node.children:
                next_node = node.children[char]
                current_path = path + [(r, c)]
                current_path_chars = path_chars + char
                
                # Check for word completion
                # The word length W = len(current_path) + (initial_k - skips_left)
                # But here we haven't used a skip for this char.
                # Total skips used = initial_k - skips_left.
                # Current Word Length estimate in Trie = depth.
                # Path Length = len(current_path).
                # Let's check if the word ends here.
                
                if next_node.is_end_of_word:
                    # Valid word found.
                    # Total extra letters = initial_k - skips_left (which is fixed in this scope closure? No)
                    # We need to calculate score based on cleared cells.
                    # Cleared = len(path) - (len(word) - len(path)) = 2*len(path) - len(word)
                    # Score = 10 + 10 * Cleared.
                    # Here, len(word) is not simply len(current_path).
                    # len(word) is the depth of the node in the Trie.
                    # Wait, Trie doesn't store depth.
                    # We need to track `word_len` explicitly.
                    pass 
                # This unified approach is getting complicated to track both path length and word length simultaneously without a full state tuple.
                # Let's stick to the previous working logic structure:
                # 1. Exact match DFS (k=0).
                # 2. Skip-search (k>0) which branches out from the current path prefix.

        # Re-implementing _search_board with clear separation.
        
        # Helper to check bounds and content
        def is_valid(r, c):
            return 0 <= r < rows and 0 <= c < cols and board[r][c] != ""

        if k == 0:
            # Standard DFS for exact match
            for r in range(rows):
                for c in range(cols):
                    if is_valid(r, c):
                        visited = {(r, c)}
                        dfs_exact(r, c, [], "", visited, self.root)
            return best_move
        else:
            # DFS + Skip Search
            # We iterate all possible path starts, then DFS to build paths.
            # For each path prefix found, we try to complete the word using `k` skips.
            for r in range(rows):
                for c in range(cols):
                    if is_valid(r, c):
                        visited = {(r, c)}
                        # We start a search that allows skips
                        # State: (r, c, path, word_so_far, trie_node, skips_used)
                        # We cap skips used at k.
                        dfs_skip(r, c, [(r, c)], board[r][c], visited, self.root.children.get(board[r][c]), 0)
            return best_move

    # Defined outside to be accessible by _search_board logic above?
    # Better to define them as methods or nested clearly.
    # Let's define them as methods to be cleaner.

    def dfs_exact(self, r, c, path, path_str, visited, node):
        char = self.board[r][c]
        if char not in node.children:
            return
        
        next_node = node.children[char]
        current_path = path + [(r, c)]
        current_str = path_str + char
        
        # Check score
        if next_node.is_end_of_word:
            score = 10 + 10 * len(current_path)
            if score > self.current_best_score:
                self.current_best_score = score
                self.current_best_move = (current_path, current_str)
        
        # Recurse
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and self.board[nr][nc] != "":
                visited.add((nr, nc))
                self.dfs_exact(nr, nc, current_path, current_str, visited, next_node)
                visited.remove((nr, nc))

    def dfs_skip(self, r, c, path, word, visited, node, skips_used):
        # This function performs DFS on board but ALSO allows branching into skips (non-board letters)
        
        if node is None: return
        
        # 1. Try to finish the word using remaining skips in the Trie (without moving on board)
        # We check if we can reach a word end from `node` within (self.target_k - skips_used) steps.
        # To optimize, we can pre-calculate distances or just DFS the Trie.
        # Since k is small (1 or 2), Trie DFS is cheap.
        
        remaining_skips = self.target_k - skips_used
        if remaining_skips >= 0:
            self.check_trie_completion(node, word, len(path), remaining_skips)
        
        if skips_used >= self.target_k:
            # No more skips allowed, must match board exactly
            # Continue standard DFS
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and self.board[nr][nc] != "":
                    char = self.board[nr][nc]
                    if char in node.children:
                        visited.add((nr, nc))
                        self.dfs_skip(nr, nc, path + [(nr, nc)], word + char, visited, node.children[char], skips_used)
                        visited.remove((nr, nc))
        else:
            # We are allowed more skips.
            # But skips must be "extra letters" -> letters NOT on the current path cell?
            # Rule: "Extra Letters are placed back into the shuffled path cells."
            # There is no restriction that extra letters cannot match board letters.
            # It just means the word contains the path as a subsequence.
            # So `skips` can be ANY letter in the Trie.
            
            # Option A: Consume board char (move to neighbor)
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and self.board[nr][nc] != "":
                    char = self.board[nr][nc]
                    if char in node.children:
                        visited.add((nr, nc))
                        self.dfs_skip(nr, nc, path + [(nr, nc)], word + char, visited, node.children[char], skips_used)
                        visited.remove((nr, nc))

            # Option B: Consume a skip (stay on board? No, path stays same, word grows)
            # We use a skip to add a letter to the word that is NOT the next step on the board.
            # This effectively branches into the Trie.
            # We do NOT move (r, c). We do NOT add to path.
            # We increase skips_used.
            # We iterate all children of current node in Trie.
            # Pruning: We shouldn't explore deep skip chains blindly. 
            # Since we call `check_trie_completion` at start of loop, we cover the "finish now" cases.
            # Here we just explore one step of skip to allow the recursion to continue?
            # Actually, we can combine Option B into the `check_trie_completion` logic by treating it as an exhaustive search of the remaining letters.
            
            # However, `check_trie_completion` only checks if a word EXISTS.
            # It doesn't allow us to resume board DFS after the skips.
            # e.g. Path "C-A", want word "COAT".
            # Board: C - A - T (neighbors)
            # 1. Start C.
            # 2. Move to A. Path "CA". Word "CA". Skips 0.
            #    Check completion: can we finish with 1 skip? 
            #    Node at 'A'. Can we find word 'CA?' ending at node? 
            #    'CAT' -> Node 'T' under 'A' is not end?
            #    Wait, "COAT". C-O-A-T.
            #    Path: C - A - T.
            #    Word: C - O - A - T.
            #    1. Take 'C' (Board).
            #    2. Take 'O' (Skip). Skips=1. Path still 'C'. Word 'CO'.
            #    3. Take 'A' (Board). Path 'CA'. Word 'COA'. Skips=1.
            #    4. Take 'T' (Board). Path 'CAT'. Word 'COAT'. Skips=1.
            
            # So the "Skip" step happens BETWEEN board moves.
            # We must allow recursion that uses skips WITHOUT moving on board.
            
            # But we must be careful not to loop or explore too much.
            # We can just explore ONE layer of skip deeply because k is small?
            # Or allow the recursion `dfs_skip` to call itself for skips?
            # Yes.
            for char, next_node in node.children.items():
                # We use a skip. We stay at (r,c). Path unchanged.
                # Word increases. Skips increase.
                self.dfs_skip(r, c, path, word + char, visited, next_node, skips_used + 1)

    def check_trie_completion(self, node, word, path_len, remaining_skips):
        # Checks if we can reach a word end from this node using exactly `remaining_skips` letters.
        # If so, calculate score.
        if remaining_skips == 0:
            if node.is_end_of_word:
                # Valid word found
                # Score = 10 + 10 * (2 * path_len - len(word))
                cleared = 2 * path_len - len(word)
                if cleared >= 0:
                    score = 10 + 10 * cleared
                    if score > self.current_best_score:
                        self.current_best_score = score
                        self.current_best_move = (list(self.current_path), word) # Need to track path correctly
            return
        
        # remaining_skips > 0
        for char, next_node in node.children.items():
            self.check_trie_completion(next_node, word + char, path_len, remaining_skips - 1)

    # Overwriting make_move with the corrected flow using instance variables for state tracking during search
    def make_move(self, board, scores, total_passes):
        self.board = board
        self.current_best_score = -1
        self.current_best_move = None
        self.current_path = [] # Helper to store path during recursive calls
        
        # 1. Exact match (k=0)
        self.target_k = 0
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    self.dfs_exact(r, c, [], "", {(r,c)}, self.root)
        
        if self.current_best_move:
            return self.current_best_move
            
        # 2. k=1
        self.target_k = 1
        self.current_best_score = -1 # Reset
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    # We need to pass the initial char
                    char = board[r][c]
                    if char in self.root.children:
                         self.dfs_skip(r, c, [(r,c)], char, {(r,c)}, self.root.children[char], 0)

        if self.current_best_move:
            return self.current_best_move

        # 3. k=2
        self.target_k = 2
        self.current_best_score = -1
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    char = board[r][c]
                    if char in self.root.children:
                         self.dfs_skip(r, c, [(r,c)], char, {(r,c)}, self.root.children[char], 0)

        if self.current_best_move:
            return self.current_best_move

        return "PASS"