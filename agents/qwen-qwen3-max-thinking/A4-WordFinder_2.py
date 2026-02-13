"""
Agent Code: A4-WordFinder
Model: qwen-qwen3-max-thinking
Run: 2
Generated: 2026-02-12 09:31:57
"""


import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.words_by_length_desc = sorted(self.dictionary, key=len, reverse=True)
    
    def _score_word(self, word, letter1, letter2):
        base = len(word)
        if '-' in word:
            base = base / 2.0
        if (letter1 + letter2) in word or (letter2 + letter1) in word:
            return base * 2
        return base

    def make_move(self, current_word, word_history):
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        current_len = len(current_word)
        
        best_word = None
        best_score = -1
        
        for candidate in self.words_by_length_desc:
            if candidate in word_history:
                continue
            if len(candidate) == current_len:
                continue
            if candidate[0] == first_char or candidate[0] == last_char or candidate[-1] == first_char or candidate[-1] == last_char:
                continue
            if first_char not in candidate or last_char not in candidate:
                continue
            
            score = self._score_word(candidate, first_char, last_char)
            if score > best_score:
                best_score = score
                best_word = candidate
        
        if best_word is not None:
            return best_word
        
        for candidate in self.words_by_length_desc:
            if candidate in word_history:
                continue
            if len(candidate) == current_len:
                continue
            has_first = first_char in candidate
            has_last = last_char in candidate
            if has_first == has_last:
                continue
            required = first_char if has_first else last_char
            if candidate[0] == required or candidate[-1] == required:
                continue
            return candidate
        
        for candidate in self.dictionary:
            if candidate not in word_history and len(candidate) != current_len:
                return candidate
        
        return random.choice(list(self.dictionary))