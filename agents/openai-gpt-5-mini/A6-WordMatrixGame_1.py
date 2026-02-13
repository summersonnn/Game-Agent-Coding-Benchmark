"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-12 19:13:59
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordMatrixAgent:
    def __init__(self, name):
        """
        Simple heuristic agent:
        - Limits path length to max_path_len (default 5) to keep per-move computation bounded.
        - Uses only dictionary words of length <= 2 * max_path_len.
        - Searches paths from longest to shortest and prefers words with minimal extras.
        """
        self.name = name
        # load_words() is expected to be provided by the environment (as in the interface)
        self.dictionary = load_words()  # set or iterable of lowercase words
        self.rng = random.Random()
        # Tunable limits (keeps runtime reasonable)
        self.max_path_len = 5
        self.max_word_len = 2 * self.max_path_len

        # Bucket words by length and store also letter sets for quick filtering
        self.words_by_len = defaultdict(list)  # length -> list of (word, set_of_letters)
        for w in self.dictionary:
            if not isinstance(w, str):
                continue
            if not w.isalpha():
                # keep only purely alphabetic words (lowercase typically)
                continue
            L = len(w)
            if 2 <= L <= self.max_word_len:
                self.words_by_len[L].append((w, set(w)))

        # Shuffle each bucket to avoid deterministic ordering
        for L in self.words_by_len:
            self.rng.shuffle(self.words_by_len[L])

    def make_move(self, board, scores, total_passes):
        """
        Return either:
         - "PASS"
         - (path, word) where path is list of (row, col) tuples (length >= 2)
        """
        try:
            R = len(board)
            C = len(board[0]) if R > 0 else 0

            # gather non-empty positions
            non_empty = [(r, c) for r in range(R) for c in range(C) if board[r][c] != ""]
            if len(non_empty) < 2:
                return "PASS"

            max_k = min(self.max_path_len, len(non_empty))

            # helper: subsequence check (path letters must appear in word in order)
            def is_subsequence(seq_letters, word):
                idx = 0
                n = len(seq_letters)
                for ch in word:
                    if ch == seq_letters[idx]:
                        idx += 1
                        if idx == n:
                            return True
                return False

            # neighbors (orthogonal only)
            def neighbors(r, c):
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < R and 0 <= nc < C:
                        yield (nr, nc)

            starts = non_empty[:]
            self.rng.shuffle(starts)

            best_score = -10**9
            best_move = None

            # cap how many full paths we evaluate to avoid pathological runtimes
            PATH_EVAL_LIMIT = 20000
            path_evals = 0

            # search path lengths from longest to shortest (prefer higher potential scores)
            for k in range(max_k, 1, -1):
                # If we've already got a move as good as the theoretical best for this k, skip.
                theoretical_best_for_k = 10 + 10 * k
                if best_score >= theoretical_best_for_k:
                    continue

                # For each starting cell, do iterative DFS to enumerate simple paths of length k
                for start in starts:
                    # quick skip if start is empty (shouldn't happen because starts from non_empty)
                    if board[start[0]][start[1]] == "":
                        continue

                    # stack items: (current_pos, path_list, used_set)
                    stack = [(start, [start], {start})]
                    while stack:
                        pos, path, used = stack.pop()
                        if len(path) == k:
                            path_evals += 1
                            if path_evals > PATH_EVAL_LIMIT:
                                # stop early and return best seen so far (or PASS)
                                return best_move if best_move else "PASS"

                            # collect path letters
                            seq = [board[r][c] for (r, c) in path]

                            # try candidate words with length from k (zero extras) up to min(2*k, max_word_len)
                            found_for_path = False
                            seq_set = set(seq)
                            for L in range(k, min(2 * k, self.max_word_len) + 1):
                                word_bucket = self.words_by_len.get(L, ())
                                if not word_bucket:
                                    continue
                                # check words in this bucket; word_bucket elements are (word, set_letters)
                                for w, wset in word_bucket:
                                    # quick letter presence filter
                                    if not seq_set.issubset(wset):
                                        continue
                                    # subsequence order check
                                    if is_subsequence(seq, w):
                                        extras = L - k
                                        cleared = k - extras  # cells cleared after move
                                        score = 10 + 10 * cleared
                                        if score > best_score:
                                            best_score = score
                                            best_move = (list(path), w)
                                            # if we achieved the best possible for this path (extras == 0)
                                            # and that equals the theoretical best for the current max length,
                                            # it's a good early exit candidate
                                            if score == theoretical_best_for_k:
                                                return best_move
                                        found_for_path = True
                                        break
                                if found_for_path:
                                    break
                            continue  # done with this path

                        # else extend path
                        r, c = pos
                        for (nr, nc) in neighbors(r, c):
                            if board[nr][nc] == "":
                                continue
                            if (nr, nc) in used:
                                continue
                            # append new state
                            new_path = path + [(nr, nc)]
                            new_used = used | {(nr, nc)}
                            stack.append(((nr, nc), new_path, new_used))

            if best_move:
                return best_move
            else:
                return "PASS"

        except Exception:
            # Avoid crashing the host; return PASS on error
            return "PASS"
