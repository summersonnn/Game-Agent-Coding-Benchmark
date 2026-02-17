"""
Agent Code: A4-WordFinder
Model: qwen/qwen3.5-plus-02-15
Run: 1
Generated: 2026-02-16 18:36:51
"""

import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.by_char_len = {}
        self.all_lengths = set()
        
        # Precompute index: char -> length -> set of words
        # Only index words with length >= 3 that have internal characters
        for word in self.dictionary:
            l = len(word)
            if l < 3:
                continue
            self.all_lengths.add(l)
            # Identify characters that appear internally (not at start or end)
            internal_chars = set(word[1:-1])
            for char in internal_chars:
                if char not in self.by_char_len:
                    self.by_char_len[char] = {}
                if l not in self.by_char_len[char]:
                    self.by_char_len[char][l] = set()
                self.by_char_len[char][l].add(word)
        
        self.sorted_lengths_desc = sorted(list(self.all_lengths), reverse=True)
        self.sorted_lengths_asc = sorted(list(self.all_lengths))

    def make_move(self, current_word, word_history):
        req1 = current_word[0].lower()
        req2 = current_word[-1].lower()
        current_len = len(current_word)
        
        best_word = None
        best_score = -1
        
        # 1. Try to find a valid move (contains BOTH required letters internally)
        for l in self.sorted_lengths_desc:
            # Pruning: If we already have a score, and the max possible score at this length
            # (which is 2*l with bonus) is not better, stop searching.
            if best_score > 0 and (l * 2) <= best_score:
                break
            
            if l == current_len:
                continue
            
            set1 = self.by_char_len.get(req1, {}).get(l, set())
            set2 = self.by_char_len.get(req2, {}).get(l, set())
            
            if not set1 or not set2:
                continue
            
            # Intersection gives words containing both chars internally at length l
            candidates = set1 & set2
            if not candidates:
                continue
            
            # Filter out used words
            valid_candidates = candidates - word_history
            if not valid_candidates:
                continue
            
            for w in valid_candidates:
                # Constraint: Required letters cannot be at start or end of new word
                if w[0] in (req1, req2) or w[-1] in (req1, req2):
                    continue
                
                score = l
                if '-' in w:
                    score //= 2
                
                # Check for consecutive bonus (PH or HP)
                if (req1 + req2) in w or (req2 + req1) in w:
                    score *= 2
                
                if score > best_score:
                    best_score = score
                    best_word = w
        
        if best_word:
            return best_word
            
        # 2. Partial Move (contains only ONE required letter internally)
        # Score is negative. We want to maximize score (minimize penalty magnitude).
        best_partial_word = None
        best_partial_score = -float('inf')
        
        for l in self.sorted_lengths_asc:
            # Pruning: Max possible score at length l is -(l // 2) (if hyphenated).
            # If this theoretical max is not better than what we found, stop.
            if best_partial_score != -float('inf'):
                if -(l // 2) <= best_partial_score:
                    break
            
            if l == current_len:
                continue
            
            cands1 = self.by_char_len.get(req1, {}).get(l, set()) - word_history
            cands2 = self.by_char_len.get(req2, {}).get(l, set()) - word_history
            
            all_partial = cands1 | cands2
            
            for w in all_partial:
                if w[0] in (req1, req2) or w[-1] in (req1, req2):
                    continue
                
                score = l
                if '-' in w:
                    score //= 2
                score = -score
                
                if score > best_partial_score:
                    best_partial_score = score
                    best_partial_word = w
        
        if best_partial_word:
            return best_partial_word
            
        # 3. Fallback (Random valid word to avoid invalid move penalty)
        remaining = self.dictionary - word_history
        if remaining:
            return random.sample(remaining, 1)[0]
            
        return "a"