"""
Agent Code: A4-WordFinder
Model: x-ai-grok-4
Run: 1
Generated: 2026-02-12 09:24:15
"""

import random
from collections import defaultdict


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.pair_to_words = defaultdict(list)
        for w in self.dictionary:
            if len(w) < 2:
                continue
            letter_set = set(w)
            start, end = w[0], w[-1]
            forbidden = {start, end}
            possible_req = letter_set - forbidden
            for s in possible_req:
                for e in possible_req:
                    self.pair_to_words[(s, e)].append(w)
        self.hardness = {pair: len(self.pair_to_words[pair]) for pair in self.pair_to_words}
        self.partial_words = defaultdict(list)
        for w in self.dictionary:
            if len(w) < 2:
                continue
            letter_set = set(w)
            forbidden = {w[0], w[-1]}
            possible = letter_set - forbidden
            for c in possible:
                self.partial_words[c].append(w)

    def make_move(self, current_word, word_history):
        req_s = current_word[0]
        req_e = current_word[-1]
        prev_len = len(current_word)
        key = (req_s, req_e)
        candidates = [w for w in self.pair_to_words[key] if w not in word_history and len(w) != prev_len]
        if candidates:
            def get_score(w):
                has_hyphen = '-' in w
                base = len(w) // 2 if has_hyphen else len(w)
                has_bonus = (req_s + req_e in w) or (req_e + req_s in w)
                return base * 2 if has_bonus else base
            score_to_ws = defaultdict(list)
            for w in candidates:
                score_to_ws[get_score(w)].append(w)
            max_score = max(score_to_ws.keys())
            best_ws = score_to_ws[max_score]
            def get_hard(w):
                p = (w[0], w[-1])
                return self.hardness.get(p, 0)
            hard_to_ws = defaultdict(list)
            for w in best_ws:
                hard_to_ws[get_hard(w)].append(w)
            min_hard = min(hard_to_ws.keys())
            best_best = hard_to_ws[min_hard]
            return random.choice(best_best)
        else:
            partial_cands = []
            if req_s != req_e:
                cands_s = [w for w in self.partial_words[req_s] if req_e not in w and w not in word_history and len(w) != prev_len]
                cands_e = [w for w in self.partial_words[req_e] if req_s not in w and w not in word_history and len(w) != prev_len]
                partial_cands = cands_s + cands_e
            if partial_cands:
                def get_base(w):
                    has_hyphen = '-' in w
                    return len(w) // 2 if has_hyphen else len(w)
                base_to_ws = defaultdict(list)
                for w in partial_cands:
                    base_to_ws[get_base(w)].append(w)
                min_base = min(base_to_ws.keys())
                best_p = base_to_ws[min_base]
                def get_hard(w):
                    return self.hardness.get((w[0], w[-1]), 0)
                hard_to_ws = defaultdict(list)
                for w in best_p:
                    hard_to_ws[get_hard(w)].append(w)
                min_hard = min(hard_to_ws.keys())
                best_best_p = hard_to_ws[min_hard]
                return random.choice(best_best_p)
            else:
                possible = sorted([w for w in self.dictionary if w not in word_history and len(w) != prev_len], key=len)
                if possible:
                    return possible[0]
                else:
                    return "word"