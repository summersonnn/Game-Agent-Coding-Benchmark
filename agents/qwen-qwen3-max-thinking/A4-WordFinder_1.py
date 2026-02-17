"""
Agent Code: A4-WordFinder
Model: qwen-qwen3-max-thinking
Run: 1
Generated: 2026-02-12 09:31:57
"""

import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.words_containing = {}
        for word in self.dictionary:
            unique_letters = set()
            for char in word:
                if 'a' <= char <= 'z':
                    unique_letters.add(char)
            for char in unique_letters:
                if char not in self.words_containing:
                    self.words_containing[char] = set()
                self.words_containing[char].add(word)
    
    def make_move(self, current_word, word_history):
        current_word_lower = current_word.lower().strip()
        if not current_word_lower or len(current_word_lower) == 0:
            unused = [w for w in self.dictionary if w not in word_history]
            return random.choice(unused) if unused else "a"
        
        req1 = current_word_lower[0]
        req2 = current_word_lower[-1]
        current_len = len(current_word_lower)
        
        # Search for full moves (contain both required letters)
        set1 = self.words_containing.get(req1, set())
        set2 = self.words_containing.get(req2, set())
        candidates_full = set1 & set2
        candidates_full = candidates_full - word_history
        
        valid_full = []
        for word in candidates_full:
            if len(word) == current_len:
                continue
            if word[0] == req1 or word[0] == req2 or word[-1] == req1 or word[-1] == req2:
                continue
            valid_full.append(word)
        
        if valid_full:
            best_word = None
            best_score = -10**18
            for word in valid_full:
                score = len(word)
                if '-' in word:
                    score /= 2.0
                if (req1 + req2) in word or (req2 + req1) in word:
                    score *= 2
                if score > best_score:
                    best_score = score
                    best_word = word
            return best_word
        
        # Search for partial moves (exactly one required letter)
        set_req1_only = set()
        if req1 in self.words_containing:
            set_req1_only = self.words_containing[req1] - word_history
            if req2 in self.words_containing:
                set_req1_only -= self.words_containing[req2]
        
        set_req2_only = set()
        if req2 in self.words_containing:
            set_req2_only = self.words_containing[req2] - word_history
            if req1 in self.words_containing:
                set_req2_only -= self.words_containing[req1]
        
        candidates_partial = set_req1_only | set_req2_only
        valid_partial = []
        
        for word in candidates_partial:
            if len(word) == current_len:
                continue
            if req1 in word:
                if word[0] != req1 and word[-1] != req1:
                    valid_partial.append(word)
            elif req2 in word:
                if word[0] != req2 and word[-1] != req2:
                    valid_partial.append(word)
        
        if valid_partial:
            return min(valid_partial, key=len)
        
        # Fallback: any unused word with different length
        for word in self.dictionary:
            if word not in word_history and len(word) != current_len:
                return word
        # Last resort: any unused word
        for word in self.dictionary:
            if word not in word_history:
                return word
        return "a"