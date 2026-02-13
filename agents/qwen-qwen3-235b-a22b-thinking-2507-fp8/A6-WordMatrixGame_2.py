"""
Agent Code: A6-WordMatrixGame
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-13 22:39:54
"""

import sys

import sys

def load_words():
    with open('words.txt') as f:
        return set(word.strip().lower() for word in f if word.strip())

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
    
    def dfs(self, board, r, c, depth, L, visited, path, all_paths):
        visited.add((r, c))
        path.append((r, c))
        
        if depth == L - 1:
            all_paths.append(path[:])
        else:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4:
                    if board[nr][nc] != '' and (nr, nc) not in visited:
                        self.dfs(board, nr, nc, depth + 1, L, visited, path, all_paths)
        
        path.pop()
        visited.remove((r, c))
    
    def get_all_paths(self, board, L):
        all_paths = []
        for r in range(4):
            for c in range(4):
                if board[r][c] != '':
                    visited = set()
                    path = []
                    self.dfs(board, r, c, 0, L, visited, path, all_paths)
        return all_paths

    def make_move(self, board, scores, total_passes):
        best_move = None
        best_score = -10
        
        for L in range(16, 1, -1):
            paths = self.get_all_paths(board, L)
            for path in paths:
                s = ''.join(board[r][c] for (r, c) in path)
                if s in self.dictionary:
                    return (path, s)
            
            for path in paths:
                s = ''.join(board[r][c] for (r, c) in path)
                found = False
                for i in range(0, L + 1):
                    for c in 'abcdefghijklmnopqrstuvwxyz':
                        candidate_word = s[:i] + c + s[i:]
                        if candidate_word in self.dictionary:
                            score_val = 10 + 10 * (L - 1)
                            if score_val > best_score:
                                best_score = score_val
                                best_move = (path, candidate_word)
                            found = True
                            break
                    if found:
                        break
            
            if best_score >= 10 + 10 * L:
                return best_move
        
        if best_move is not None:
            return best_move
        else:
            return "PASS"
