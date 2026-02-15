"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-14 18:23:39
"""

from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.pair_richness = defaultdict(int)
        self.buckets = defaultdict(list)
        
        for word in self.dictionary:
            n = len(word)
            if n < 3:
                continue
            f = word[0]
            l = word[-1]
            S_valid = set(word) - {f, l}
            
            for x in S_valid:
                for y in S_valid:
                    key_ordered = (x, y)
                    self.pair_richness[key_ordered] += 1
            
            distinct_valid = sorted(S_valid)
            for i in range(len(distinct_valid)):
                x = distinct_valid[i]
                for j in range(i, len(distinct_valid)):
                    y = distinct_valid[j]
                    key_bucket = (x, y)
                    self.buckets[key_bucket].append(word)

    def make_move(self, current_word, word_history):
        current_word_lower = current_word.lower()
        a = current_word_lower[0]
        b = current_word_lower[-1]
        L = len(current_word_lower)
        
        key_bucket = (min(a, b), max(a, b))
        candidate_list = self.buckets.get(key_bucket, [])
        candidates = []
        
        for word in candidate_list:
            if word in word_history:
                continue
            if len(word) == L:
                continue
            base = len(word)
            if '-' in word:
                base = base // 2
            bigram1 = a + b
            bigram2 = b + a
            has_bonus = False
            for i in range(len(word) - 1):
                if word[i:i+2] == bigram1 or word[i:i+2] == bigram2:
                    has_bonus = True
                    break
            total_score = base * 2 if has_bonus else base
            opp_key = (word[0], word[-1])
            opp_rich = self.pair_richness.get(opp_key, 0)
            candidates.append((word, total_score, opp_rich))
        
        if candidates:
            candidates.sort(key=lambda x: (-x[1], x[2]))
            return candidates[0][0]
        
        partial_candidates = []
        for word in self.dictionary:
            if word in word_history:
                continue
            n = len(word)
            if n == L or n < 3:
                continue
            cond1 = (a in word) and (b not in word) and (word[0] != a) and (word[-1] != a)
            cond2 = (b in word) and (a not in word) and (word[0] != b) and (word[-1] != b)
            if cond1 or cond2:
                partial_candidates.append((word, n))
        
        if partial_candidates:
            partial_candidates.sort(key=lambda x: x[1])
            return partial_candidates[0][0]
        
        for word in self.dictionary:
            if word not in word_history and len(word) != L:
                return word
        return "a"
