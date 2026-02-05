"""
Agent Code: A4-WordFinder
Model: x-ai/grok-4.1-fast
Run: 1
Generated: 2026-02-05 21:09:40
"""

from collections import defaultdict

from collections import defaultdict
import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.pair_to_candidates = defaultdict(list)
        self._build_indexes()

    def _build_indexes(self):
        for word in self.dictionary:
            if len(word) < 3:
                continue
            start_let = word[0]
            end_let = word[-1]
            interior = word[1:-1]
            interior_set = set(interior)
            has_hyphen = '-' in word
            wlen = len(word)
            for r1 in interior_set:
                for r2 in interior_set:
                    if start_let not in (r1, r2) and end_let not in (r1, r2):
                        bonus = ((r1 + r2) in word) or ((r2 + r1) in word)
                        base = wlen / 2.0 if has_hyphen else float(wlen)
                        sc = base * (2.0 if bonus else 1.0)
                        self.pair_to_candidates[(r1, r2)].append((sc, wlen, word))
        
        # Sort each list: highest score first, then longest
        for key in self.pair_to_candidates:
            self.pair_to_candidates[key].sort(key=lambda x: (x[0], x[1]), reverse=True)

    def make_move(self, current_word, word_history):
        if len(current_word) < 1:
            # Fallback for invalid input
            return self._get_shortest_unused(word_history, 0)
        
        r1 = current_word[0]
        r2 = current_word[-1]
        prev_len = len(current_word)
        
        cands = self.pair_to_candidates.get((r1, r2), [])
        
        valid_cands = []
        for sc, clen, word in cands:
            if word not in word_history and clen != prev_len:
                valid_cands.append((sc, clen, word))
                if len(valid_cands) >= 10:
                    break
        
        if valid_cands:
            # Pick best: max score, then min opponent options, then max len
            def opp_hardness(tup):
                _, _, w = tup
                opp_pair = (w[0], w[-1])
                opp_count = len(self.pair_to_candidates.get(opp_pair, []))
                return (-tup[0], opp_count, -tup[1])  # min key for sort, but max uses neg
            
            best = max(valid_cands, key=lambda tup: (-opp_hardness(tup)[0], opp_hardness(tup)[1], -opp_hardness(tup)[2]))
            return best[2]
        
        # Partial move: scan dictionary for best (shortest) partial
        best_partial = None
        min_plen = float('inf')
        for word in self.dictionary:
            if word in word_history:
                continue
            clen = len(word)
            if clen == prev_len or clen < 3:
                continue
            # Partial r1
            is_r1_partial = (r1 in word and r2 not in word and word[0] != r1 and word[-1] != r1)
            # Partial r2
            is_r2_partial = (r2 in word and r1 not in word and word[0] != r2 and word[-1] != r2)
            if is_r1_partial or is_r2_partial:
                if clen < min_plen:
                    min_plen = clen
                    best_partial = word
                elif clen == min_plen:
                    # Tie: prefer rarer opp pair
                    opp_pair = (word[0], word[-1])
                    opp_count = len(self.pair_to_candidates.get(opp_pair, []))
                    if best_partial is None or opp_count < len(self.pair_to_candidates.get((best_partial[0], best_partial[-1]), [])):
                        best_partial = word
        
        if best_partial:
            return best_partial
        
        # Desperate: shortest unused different length word
        return self._get_shortest_unused(word_history, prev_len)
    
    def _get_shortest_unused(self, word_history, prev_len):
        min_len = float('inf')
        best = None
        for word in self.dictionary:
            if word in word_history:
                continue
            clen = len(word)
            if clen != prev_len and clen < min_len:
                min_len = clen
                best = word
        return best if best else "a"  # ultimate fallback
