"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 1
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        self.by_letter_set = defaultdict(set)
        self.word_letters = {}
        for word in self.dictionary:
            if len(word) < 3:
                continue
            middle = word[1:-1]
            distinct_middle = set(middle)
            for char in distinct_middle:
                self.by_letter_set[char].add(word)
            self.word_letters[word] = set(word)
        
        self.opp_size = {}
        letters = 'abcdefghijklmnopqrstuvwxyz'
        for a in letters:
            set_a = self.by_letter_set.get(a, set())
            for b in letters:
                if a == b:
                    s = len(set_a)
                else:
                    set_b = self.by_letter_set.get(b, set())
                    s = len(set_a & set_b)
                self.opp_size[(a, b)] = s

    def make_move(self, current_word, word_history):
        current_word = current_word.lower()
        a = current_word[0]
        b = current_word[-1]
        L = len(current_word)
        
        if a == b:
            candidate_set_full = self.by_letter_set.get(a, set())
        else:
            set_a = self.by_letter_set.get(a, set())
            set_b = self.by_letter_set.get(b, set())
            candidate_set_full = set_a & set_b
        
        full_candidates = []
        for word in candidate_set_full:
            if word in word_history:
                continue
            if len(word) == L:
                continue
            if word[0] == a or word[0] == b or word[-1] == a or word[-1] == b:
                continue
            full_candidates.append(word)
        
        best_full = None
        for word in full_candidates:
            base = len(word)
            has_hyphen = '-' in word
            if has_hyphen:
                base //= 2
            consecutive = (a + b in word) or (b + a in word)
            if consecutive:
                base *= 2
            a_next = word[0].lower()
            b_next = word[-1].lower()
            opp_hardness = self.opp_size.get((a_next, b_next), 0)
            candidate_score = (base, -opp_hardness, word)
            if best_full is None or candidate_score > best_full:
                best_full = candidate_score
        
        if best_full is not None:
            return best_full[2]
        
        best_partial = None
        for x in (a, b):
            y = b if x == a else a
            for word in self.by_letter_set.get(x, set()):
                if word in word_history:
                    continue
                if len(word) == L:
                    continue
                if word[0] == x or word[-1] == x:
                    continue
                if y in self.word_letters.get(word, set()):
                    continue
                if best_partial is None or len(word) < len(best_partial):
                    best_partial = word
        
        if best_partial is not None:
            return best_partial
        
        for word in self.dictionary:
            if word not in word_history and len(word) != L:
                return word
        return "a"
