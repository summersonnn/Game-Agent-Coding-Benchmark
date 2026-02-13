"""
Agent Code: A6-WordMatrixGame
Model: anthropic-claude-sonnet-4.5
Run: 2
Generated: 2026-02-12 18:14:17
"""

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = self._load_words()
        self.words_by_length = self._index_by_length()
    
    def _load_words(self):
        try:
            with open('/usr/share/dict/words', 'r') as f:
                words = {line.strip().lower() for line in f 
                        if line.strip().isalpha()}
            return words
        except:
            return set()
    
    def _index_by_length(self):
        index = {}
        for word in self.dictionary:
            length = len(word)
            if length not in index:
                index[length] = set()
            index[length].add(word)
        return index
    
    def make_move(self, board, scores, total_passes):
        try:
            best_move = None
            best_score = -11
            
            all_paths = self._find_all_paths(board)
            
            for path in all_paths:
                path_letters = [board[r][c] for r, c in path]
                path_len = len(path)
                
                for word_len in range(path_len, min(2 * path_len + 1, 20)):
                    if word_len not in self.words_by_length:
                        continue
                    
                    for word in self.words_by_length[word_len]:
                        if self._is_subsequence(path_letters, word):
                            cleared_cells = path_len - (word_len - path_len)
                            move_score = 10 + 10 * cleared_cells
                            
                            if move_score > best_score:
                                best_score = move_score
                                best_move = (path, word)
                                
                                if cleared_cells == path_len:
                                    return best_move
            
            return best_move if best_move else "PASS"
        except:
            return "PASS"
    
    def _find_all_paths(self, board):
        all_paths = []
        
        for r in range(4):
            for c in range(4):
                if board[r][c]:
                    self._dfs(board, r, c, [], set(), all_paths)
        
        return all_paths
    
    def _dfs(self, board, r, c, path, visited, all_paths):
        if r < 0 or r >= 4 or c < 0 or c >= 4:
            return
        if (r, c) in visited or not board[r][c]:
            return
        
        path.append((r, c))
        visited.add((r, c))
        
        if len(path) >= 2:
            all_paths.append(path[:])
        
        if len(path) < 8:
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                self._dfs(board, r + dr, c + dc, path, visited, all_paths)
        
        path.pop()
        visited.remove((r, c))
    
    def _is_subsequence(self, path_letters, word):
        path_idx = 0
        for char in word:
            if path_idx < len(path_letters) and char == path_letters[path_idx]:
                path_idx += 1
        return path_idx == len(path_letters)