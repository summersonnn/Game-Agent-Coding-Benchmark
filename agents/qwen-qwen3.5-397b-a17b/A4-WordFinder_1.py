"""
Agent Code: A4-WordFinder
Model: qwen/qwen3.5-397b-a17b
Run: 1
Generated: 2026-02-16 17:46:27
"""

import random

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Pre-compute index: char -> set of words containing char internally (index 1 to -1)
        self.char_index = {chr(c): set() for c in range(ord('a'), ord('z') + 1)}
        
        for word in self.dictionary:
            if len(word) < 3:
                continue
            internal_chars = set(word[1:-1])
            for char in internal_chars:
                if char in self.char_index:
                    self.char_index[char].add(word)

    def make_move(self, current_word, word_history):
        req1 = current_word[0].lower()
        req2 = current_word[-1].lower()
        prev_len = len(current_word)
        
        set1 = self.char_index.get(req1, set())
        set2 = self.char_index.get(req2, set())
        
        # Try Full Moves (Intersection: contains both req1 and req2 internally)
        candidates = set1.intersection(set2)
        valid_words = []
        is_partial = False
        
        for word in candidates:
            if word in word_history:
                continue
            if len(word) == prev_len:
                continue
            # Rule 2: Required letters cannot be first or last
            if word[0] in (req1, req2) or word[-1] in (req1, req2):
                continue
            valid_words.append(word)
            
        # Fallback to Partial Moves (Union: contains at least one) if no Full Moves
        if not valid_words:
            candidates = set1.union(set2)
            is_partial = True
            for word in candidates:
                if word in word_history:
                    continue
                if len(word) == prev_len:
                    continue
                if word[0] in (req1, req2) or word[-1] in (req1, req2):
                    continue
                valid_words.append(word)
        
        # Emergency Fallback if still no moves (to avoid crash/invalid penalty)
        if not valid_words:
            for word in self.dictionary:
                if word not in word_history and len(word) != prev_len:
                    return word
            return next(iter(self.dictionary))

        # Scoring
        scored_words = []
        for word in valid_words:
            length = len(word)
            if is_partial:
                score = -length
            else:
                score = length
                if '-' in word:
                    score /= 2
                # Check consecutive bonus
                if (req1 + req2) in word or (req2 + req1) in word:
                    score *= 2
            scored_words.append((score, word))
        
        # Sort by score descending
        scored_words.sort(key=lambda x: x[0], reverse=True)
        
        # Opponent Difficulty Analysis on Top Candidates
        # Limit to top 50 to ensure we stay within time limit
        top_candidates = scored_words[:50]
        
        best_move = None
        best_score = -float('inf')
        best_opponent_options = float('inf')
        
        for score, word in top_candidates:
            # Estimate opponent options using our precomputed index
            o_req1 = word[0]
            o_req2 = word[-1]
            o_set1 = self.char_index.get(o_req1, set())
            o_set2 = self.char_index.get(o_req2, set())
            opponent_options = len(o_set1.intersection(o_set2))
            
            # Select best: Max Score, Min Opponent Options
            if score > best_score:
                best_score = score
                best_move = word
                best_opponent_options = opponent_options
            elif score == best_score:
                if opponent_options < best_opponent_options:
                    best_opponent_options = opponent_options
                    best_move = word
                elif opponent_options == best_opponent_options:
                    if random.random() > 0.5:
                        best_move = word
        
        if best_move is None and scored_words:
            best_move = scored_words[0][1]
            
        return best_move