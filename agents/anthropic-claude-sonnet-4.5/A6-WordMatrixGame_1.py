"""
Agent Code: A6-WordMatrixGame
Model: anthropic-claude-sonnet-4.5
Run: 1
Generated: 2026-02-12 18:14:17
"""

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.words_by_len = {}
        for word in self.dictionary:
            l = len(word)
            if l not in self.words_by_len:
                self.words_by_len[l] = []
            self.words_by_len[l].append(word)
    
    def make_move(self, board, scores, total_passes):
        paths = self._find_all_paths(board)
        
        if not paths:
            return "PASS"
        
        best_move = None
        best_score = -11
        
        for path in paths:
            letters = [board[r][c] for r, c in path]
            path_len = len(path)
            
            for word_len in range(path_len, 2 * path_len + 1):
                if word_len not in self.words_by_len:
                    continue
                
                for word in self.words_by_len[word_len]:
                    if self._is_subsequence(letters, word):
                        cleared = 2 * path_len - word_len
                        score = 10 + 10 * cleared
                        
                        if score > best_score:
                            best_score = score
                            best_move = (path, word)
        
        return best_move if best_move else "PASS"
    
    def _find_all_paths(self, board):
        all_paths = []
        
        for r in range(4):
            for c in range(4):
                if board[r][c]:
                    self._dfs(board, r, c, [(r, c)], {(r, c)}, all_paths)
        
        return all_paths
    
    def _dfs(self, board, r, c, path, visited, results):
        if len(path) >= 2:
            results.append(list(path))
        
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            
            if (0 <= nr < 4 and 0 <= nc < 4 and 
                (nr, nc) not in visited and board[nr][nc]):
                
                visited.add((nr, nc))
                path.append((nr, nc))
                self._dfs(board, nr, nc, path, visited, results)
                path.pop()
                visited.remove((nr, nc))
    
    def _is_subsequence(self, letters, word):
        i = 0
        for letter in letters:
            while i < len(word) and word[i] != letter:
                i += 1
            if i >= len(word):
                return False
            i += 1
        return True