"""
Agent Code: A6-WordMatrixGame
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-13 22:39:54
"""

import itertools
from collections import deque

import random
import itertools

def load_words():
    # This function is provided by the game environment.
    # For the purpose of this solution, we assume it returns a set of lowercase words.
    pass

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        full_dict = load_words()
        words_list = list(full_dict)
        words_by_length = {}
        for word in words_list:
            L = len(word)
            if L not in words_by_length:
                words_by_length[L] = []
            words_by_length[L].append(word)
        
        self.min_M_for_subseq = {}
        self.word_for_subseq = {}
        
        for M in range(2, 17):
            if M not in words_by_length:
                continue
            for word in words_by_length[M]:
                L_min0 = (M + 1) // 2
                L_min = max(2, L_min0)
                L_max = min(M, 8)
                if L_min > L_max:
                    continue
                n = len(word)
                for L_val in range(L_min, L_max + 1):
                    for indices in itertools.combinations(range(n), L_val):
                        s = ''.join(word[i] for i in indices)
                        if s not in self.min_M_for_subseq or M < self.min_M_for_subseq[s]:
                            self.min_M_for_subseq[s] = M
                            self.word_for_subseq[s] = word

    def make_move(self, board, scores, total_passes):
        non_empty_count = 0
        for i in range(4):
            for j in range(4):
                if board[i][j] != "":
                    non_empty_count += 1
        
        if non_empty_count < 2:
            return "PASS"
        
        max_path_length = min(8, non_empty_count)
        paths = []
        from collections import deque
        
        for i in range(4):
            for j in range(4):
                if board[i][j] != "":
                    path = [(i, j)]
                    visited = set([(i, j)])
                    queue = deque()
                    queue.append((path, visited))
                    while queue:
                        path, visited = queue.popleft()
                        L = len(path)
                        if L >= 2 and L <= max_path_length:
                            s = ''.join(board[x][y] for (x, y) in path)
                            paths.append((path, L, s))
                        if L < max_path_length:
                            r, c = path[-1]
                            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                                nr, nc = r + dr, c + dc
                                if 0 <= nr < 4 and 0 <= nc < 4:
                                    if board[nr][nc] != "" and (nr, nc) not in visited:
                                        new_path = path + [(nr, nc)]
                                        new_visited = visited | {(nr, nc)}
                                        queue.append((new_path, new_visited))
        
        best_score = -1
        best_path = None
        best_word = None
        
        for (path, L, s) in paths:
            if s in self.min_M_for_subseq:
                M_val = self.min_M_for_subseq[s]
                word_val = self.word_for_subseq[s]
                score = 10 * (1 + 2 * L - M_val)
                if score > best_score:
                    best_score = score
                    best_path = path
                    best_word = word_val
        
        if best_path is not None:
            return (best_path, best_word)
        else:
            return "PASS"
