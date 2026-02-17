"""
Agent Code: A4-WordFinder
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 2
Generated: 2026-02-17 14:14:06
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.letter_to_words = defaultdict(set)
        self.word_details = {}
        
        # Precompute word details and letter mappings
        for word in self.dictionary:
            if len(word) < 3:
                continue
            first = word[0]
            last = word[-1]
            has_hyphen = '-' in word
            self.word_details[word] = (first, last, len(word), has_hyphen)
            for char in word:
                if 'a' <= char <= 'z':
                    self.letter_to_words[char].add(word)
    
    def make_move(self, current_word, word_history):
        c1 = current_word[0]
        c2 = current_word[-1]
        prev_len = len(current_word)
        
        # Step 1: Try full move (both required letters)
        candidate_set = set()
        if c1 == c2:
            candidate_set = self.letter_to_words.get(c1, set())
        else:
            set1 = self.letter_to_words.get(c1, set())
            set2 = self.letter_to_words.get(c2, set())
            candidate_set = set1 & set2
        
        valid_full = []
        for word in candidate_set:
            if word in word_history:
                continue
            first, last, length, has_hyphen = self.word_details[word]
            if length == prev_len:
                continue
            if first in (c1, c2) or last in (c1, c2):
                continue
            base = length
            if has_hyphen:
                base //= 2
            if c1 == c2:
                if c1 * 2 in word:
                    base *= 2
            else:
                if (c1 + c2) in word or (c2 + c1) in word:
                    base *= 2
            valid_full.append((word, base))
        
        if valid_full:
            valid_full.sort(key=lambda x: x[1], reverse=True)
            return valid_full[0][0]
        
        # Step 2: Try partial move (only one required letter)
        partial_candidates = []
        if c1 != c2:
            for letter in [c1, c2]:
                other_letter = c2 if letter == c1 else c1
                candidate_set_partial = self.letter_to_words.get(letter, set())
                for word in candidate_set_partial:
                    if word in word_history:
                        continue
                    if other_letter in word:
                        continue
                    first, last, length, has_hyphen = self.word_details[word]
                    if length == prev_len:
                        continue
                    if first in (c1, c2) or last in (c1, c2):
                        continue
                    base = length
                    if has_hyphen:
                        base //= 2
                    partial_candidates.append((word, base))
        
        if partial_candidates:
            partial_candidates.sort(key=lambda x: x[1])
            return partial_candidates[0][0]
        
        # Step 3: Return invalid word to trigger engine's random move
        while True:
            candidate = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))
            if candidate not in self.dictionary and candidate not in word_history:
                return candidate
