"""
Agent Code: A6-WordMatrixGame
Model: anthropic-claude-opus-4.6
Run: 2
Generated: 2026-02-12 18:14:17
"""

import time
from game_engine import load_words


class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        words = load_words()
        self.word_set = words if isinstance(words, set) else set(words)
        self.words_by_len = {}
        for w in self.word_set:
            l = len(w)
            if 2 <= l <= 16:
                self.words_by_len.setdefault(l, []).append(w)

    def make_move(self, board, scores, total_passes):
        start = time.time()

        letter_to_path = {}
        for r in range(4):
            for c in range(4):
                if board[r][c]:
                    self._enum(board, [(r, c)], {(r, c)}, letter_to_path)

        if not letter_to_path:
            return "PASS"

        candidates = sorted(letter_to_path.items(), key=lambda x: len(x[0]), reverse=True)

        best_score = 0
        best_move = None

        for letters, path in candidates:
            plen = len(letters)
            max_possible = 10 + 10 * plen
            if max_possible <= best_score:
                break

            word_str = ''.join(letters)

            if word_str in self.word_set:
                best_score = max_possible
                best_move = (path, word_str)
                continue

            score1 = 10 + 10 * (plen - 1)
            if score1 > best_score:
                found = self._try_insert1(word_str, plen)
                if found:
                    best_score = score1
                    best_move = (path, found)
                    continue

            if plen >= 3 and time.time() - start < 1.5:
                score2 = 10 + 10 * (plen - 2)
                if score2 > best_score:
                    found = self._try_insert2(word_str, plen)
                    if found:
                        best_score = score2
                        best_move = (path, found)
                        continue

            if plen >= 3 and time.time() - start < 2.5:
                score3 = 10 + 10 * (plen - 3)
                if score3 > best_score:
                    found = self._try_subseq_search(letters, plen, plen + 3)
                    if found:
                        best_score = score3
                        best_move = (path, found)

            if time.time() - start > 3.0:
                break

        if best_move and best_score > 0:
            return best_move
        return "PASS"

    def _enum(self, board, path, visited, result):
        if len(path) >= 2:
            key = tuple(board[r][c] for r, c in path)
            if key not in result:
                result[key] = list(path)
        if len(path) >= 8:
            return
        r, c = path[-1]
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in visited and board[nr][nc]:
                visited.add((nr, nc))
                path.append((nr, nc))
                self._enum(board, path, visited, result)
                path.pop()
                visited.discard((nr, nc))

    def _try_insert1(self, base, plen):
        for pos in range(plen + 1):
            for ch in 'etaoinsrhldcumfpgwybvkxjqz':
                candidate = base[:pos] + ch + base[pos:]
                if candidate in self.word_set:
                    return candidate
        return None

    def _try_insert2(self, base, plen):
        for pos1 in range(plen + 1):
            for ch1 in 'etaoinsrhldcumfpgwybvkxjqz':
                s1 = base[:pos1] + ch1 + base[pos1:]
                for pos2 in range(plen + 2):
                    for ch2 in 'etaoinsr':
                        candidate = s1[:pos2] + ch2 + s1[pos2:]
                        if candidate in self.word_set:
                            return candidate
        return None

    def _is_subsequence(self, subseq, word):
        it = iter(word)
        return all(c in it for c in subseq)

    def _try_subseq_search(self, letters, plen, target_len):
        if target_len not in self.words_by_len:
            return None
        for w in self.words_by_len[target_len]:
            if self._is_subsequence(letters, w):
                return w
        return None