"""
Agent Code: A4-WordFinder
Model: qwen-qwen3-max-thinking
Run: 1
Generated: 2026-02-12 09:31:57
"""

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.letter_set = defaultdict(set)
        self.start_freq = defaultdict(int)
        self.end_freq = defaultdict(int)
        for w in self.dictionary:
            if w:
                self.start_freq[w[0]] += 1
                self.end_freq[w[-1]] += 1
            for ch in set(w):
                if 'a' <= ch <= 'z':
                    self.letter_set[ch].add(w)
        self.all_words_list = list(self.dictionary)

    def _score_word(self, w, req1, req2=None):
        base = len(w)
        points = base / 2.0 if '-' in w else float(base)
        if req2 is not None and req1 != req2:
            if (req1 + req2) in w or (req2 + req1) in w:
                points *= 2.0
        return points

    def _difficulty(self, w):
        return self.start_freq.get(w[0], 0) + self.end_freq.get(w[-1], 0)

    def make_move(self, current_word, word_history):
        cw = current_word.lower()
        first = cw[0]
        last = cw[-1]
        prev_len = len(cw)
        used_lower = {w.lower() for w in word_history}

        if first != last:
            cand_set = self.letter_set[first] & self.letter_set[last]
            valid = []
            for w in cand_set:
                if w in used_lower or len(w) == prev_len:
                    continue
                if w[0] in (first, last) or w[-1] in (first, last):
                    continue
                if first not in w or last not in w:
                    continue
                valid.append(w)

            if valid:
                valid.sort(key=lambda w: (-self._score_word(w, first, last),
                                          self._difficulty(w),
                                          -len(w)))
                return valid[0]

            partial = []
            for w in self.letter_set[first]:
                if last in w:
                    continue
                if w in used_lower or len(w) == prev_len:
                    continue
                if w[0] == first or w[-1] == first:
                    continue
                partial.append(w)
            for w in self.letter_set[last]:
                if first in w:
                    continue
                if w in used_lower or len(w) == prev_len:
                    continue
                if w[0] == last or w[-1] == last:
                    continue
                partial.append(w)

            if partial:
                partial.sort(key=lambda w: (len(w), self._difficulty(w)))
                return partial[0]

            for w in self.all_words_list:
                if w not in used_lower:
                    return w
            return "a"

        else:
            req = first
            cand_set = self.letter_set[req]
            valid = []
            for w in cand_set:
                if w in used_lower or len(w) == prev_len:
                    continue
                if w[0] == req or w[-1] == req:
                    continue
                if req not in w:
                    continue
                valid.append(w)

            if valid:
                valid.sort(key=lambda w: (-self._score_word(w, req),
                                          self._difficulty(w),
                                          -len(w)))
                return valid[0]

            for w in self.all_words_list:
                if w not in used_lower:
                    return w
            return "a"