"""
Agent Code: A6-WordMatrixGame
Model: qwen-qwen3-max-thinking
Run: 2
Generated: 2026-02-12 19:13:59
"""

import random

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.word_set = load_words()

    def make_move(self, board, scores, total_passes):
        non_empty = []
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    non_empty.append((r, c))
        
        if len(non_empty) < 2:
            return "PASS"
        
        max_len = min(8, len(non_empty))
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        candidates = []
        
        for r in range(4):
            for c in range(4):
                if board[r][c] != "":
                    stack = [(r, c, [(r, c)], board[r][c], {(r, c)})]
                    while stack:
                        cr, cc, coords, s, visited = stack.pop()
                        L = len(coords)
                        if L >= 2:
                            candidates.append((coords, s, L))
                        if L < max_len:
                            for dr, dc in directions:
                                nr, nc = cr + dr, cc + dc
                                if 0 <= nr < 4 and 0 <= nc < 4:
                                    if board[nr][nc] != "" and (nr, nc) not in visited:
                                        new_coords = coords + [(nr, nc)]
                                        new_s = s + board[nr][nc]
                                        new_visited = visited | {(nr, nc)}
                                        stack.append((nr, nc, new_coords, new_s, new_visited))
        
        if not candidates:
            return "PASS"
        
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        best_score = -10**9
        best_move = None
        cache = {}
        letters = "abcdefghijklmnopqrstuvwxyz"
        
        for coords, s, L in candidates:
            max_possible = 10 + 10 * L
            if max_possible <= best_score:
                break
            
            if s in cache:
                result = cache[s]
                if result is not None:
                    word, W = result
                    score = 10 + 10 * (2 * L - W)
                    if score > best_score:
                        best_score = score
                        best_move = (coords, word)
                continue
            
            if s in self.word_set:
                cache[s] = (s, L)
                score = 10 + 10 * L
                if score > best_score:
                    best_score = score
                    best_move = (coords, s)
                continue
            
            found = False
            for pos in range(0, L + 1):
                for letter in letters:
                    candidate_word = s[:pos] + letter + s[pos:]
                    if candidate_word in self.word_set:
                        cache[s] = (candidate_word, L + 1)
                        score = 10 + 10 * (L - 1)
                        if score > best_score:
                            best_score = score
                            best_move = (coords, candidate_word)
                        found = True
                        break
                if found:
                    break
            
            if not found:
                cache[s] = None
        
        return best_move if best_move is not None else "PASS"