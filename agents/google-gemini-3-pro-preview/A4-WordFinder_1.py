"""
Agent Code: A4-WordFinder
Model: google/gemini-3-pro-preview
Run: 1
Generated: 2026-02-12 09:24:15
"""

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        """
        Initialize the agent and precompute word lookups to guarantee 
        lightning-fast execution during the timed make_move phase.
        """
        self.name = name
        self.dictionary = load_words()
        
        # Maps a character to a set of words where that character appears strictly inside (not start/end)
        self.inner_char_map = defaultdict(set)
        
        # Maps a character to a set of words where that character appears strictly inside AT LEAST TWICE
        # (Crucial for when the opponent plays a word that starts and ends with the same letter)
        self.double_inner_char_map = defaultdict(set)
        
        for word in self.dictionary:
            if len(word) <= 2:
                continue
                
            inner = word[1:-1]
            inner_chars = set(inner)
            
            for char in inner_chars:
                self.inner_char_map[char].add(word)
                if inner.count(char) >= 2:
                    self.double_inner_char_map[char].add(word)

    def score_word(self, word, req1, req2):
        """
        Evaluates the potential value of a word based on rules and strategy.
        """
        base_score = float(len(word))
        
        # Apply the hyphen penalty
        if '-' in word:
            base_score /= 2.0
            
        # Check for the consecutive 2x bonus
        if (req1 + req2) in word or (req2 + req1) in word:
            base_score *= 2.0
            
        # Tie-breaker: Offensive play
        # Prioritize words that start or end with difficult letters to restrict the opponent's options.
        diff_score = 0.0
        hard_letters = set("qzjxvwk")
        easy_letters = set("esart")
        
        if word[0] in hard_letters: diff_score += 0.5
        if word[-1] in hard_letters: diff_score += 0.5
        if word[0] in easy_letters: diff_score -= 0.5
        if word[-1] in easy_letters: diff_score -= 0.5
        
        return base_score + diff_score

    def make_move(self, current_word, word_history):
        """
        Calculates and returns the optimal next word.
        """
        if not current_word:
            return random.choice(list(self.dictionary))
            
        req1 = current_word[0].lower()
        req2 = current_word[-1].lower()
        forbidden_len = len(current_word)
        
        # 1. Fetch Candidates efficiently using precomputed sets
        if req1 == req2:
            candidates = self.double_inner_char_map.get(req1, set())
        else:
            candidates = self.inner_char_map.get(req1, set()).intersection(self.inner_char_map.get(req2, set()))
            
        # 2. Filter for valid words
        valid_words = []
        for w in candidates:
            if len(w) == forbidden_len:
                continue
            if w in word_history:
                continue
            # Ensure the required letters aren't at the start or end of OUR new word
            if w[0] == req1 or w[0] == req2 or w[-1] == req1 or w[-1] == req2:
                continue
            valid_words.append(w)
            
        # 3. Primary Strategy: Play highest scoring valid word
        if valid_words:
            return max(valid_words, key=lambda w: self.score_word(w, req1, req2))
            
        # 4. Fallback Strategy: Partial Move (Last Resort)
        # Find words containing at least one of the required letters
        partial_candidates = self.inner_char_map.get(req1, set()).union(self.inner_char_map.get(req2, set()))
        valid_partials = []
        
        for w in partial_candidates:
            if len(w) == forbidden_len:
                continue
            if w in word_history:
                continue
            if w[0] == req1 or w[0] == req2 or w[-1] == req1 or w[-1] == req2:
                continue
            valid_partials.append(w)
            
        if valid_partials:
            # Since partial moves give negative points based on length, minimize the penalty by picking the shortest word.
            return min(valid_partials, key=len)
            
        # 5. Extreme Fallback: Avoid match forfeit crash if dictionary completely exhausted
        remaining = list(self.dictionary - word_history)
        return random.choice(remaining) if remaining else "exhausted"