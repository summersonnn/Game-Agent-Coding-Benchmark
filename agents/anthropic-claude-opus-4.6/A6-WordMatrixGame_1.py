"""
Agent Code: A6-WordMatrixGame
Model: anthropic-claude-opus-4.6
Run: 1
Generated: 2026-02-12 18:14:17
"""

import random


class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.trie = {}
        for word in self.dictionary:
            if len(word) < 2 or len(word) > 14:
                continue
            node = self.trie
            for ch in word:
                node = node.setdefault(ch, {})
            node['$'] = word

    def make_move(self, board, scores, total_passes):
        self.best_score = -1
        self.best_move = None

        for r in range(4):
            for c in range(4):
                if board[r][c]:
                    ch = board[r][c]
                    if ch in self.trie:
                        self._search(board, [(r, c)], {(r, c)}, self.trie[ch], 1, 0)
                    for pre, pnode in self.trie.items():
                        if pre != '$' and isinstance(pnode, dict) and ch in pnode:
                            self._search(board, [(r, c)], {(r, c)}, pnode[ch], 1, 1)

        return self.best_move if self.best_move else "PASS"

    def _search(self, board, path, visited, node, plen, extras):
        wlen = plen + extras
        if '$' in node and plen >= 2 and wlen <= 2 * plen:
            cleared = plen - extras
            score = 10 + 10 * cleared
            if score > self.best_score:
                self.best_score = score
                self.best_move = (list(path), node['$'])

        r, c = path[-1]

        if plen < 8:
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and board[nr][nc] and (nr, nc) not in visited:
                    ch = board[nr][nc]
                    if ch in node:
                        visited.add((nr, nc))
                        path.append((nr, nc))
                        self._search(board, path, visited, node[ch], plen + 1, extras)
                        path.pop()
                        visited.remove((nr, nc))

        if extras < min(plen, 2):
            for ch, child in node.items():
                if ch != '$':
                    self._search(board, path, visited, child, plen, extras + 1)