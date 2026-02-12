"""
Agent Code: A4-WordFinder
Model: z-ai/glm-5@preset/fp8
Run: 2
Generated: 2026-02-12 09:24:15
"""

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        # Load the full word dictionary
        self.dictionary = load_words()
        
        # Pre-compute an index for faster lookups
        # Maps a character to a set of words where that character appears internally (not at start or end)
        self.internal_char_index = defaultdict(set)
        
        for word in self.dictionary:
            # Words must have at least 3 letters to have valid internal characters
            if len(word) < 3:
                continue
            
            # Identify characters in the "internal" part of the word (indices 1 to -2)
            # Using a set to avoid duplicate processing for words with repeated internal letters
            internal_chars = set(word[1:-1])
            
            for char in internal_chars:
                self.internal_char_index[char].add(word)

    def make_move(self, current_word, word_history):
        # Ensure inputs are lowercase for consistency
        current_word = current_word.lower()
        
        req1 = current_word[0]
        req2 = current_word[-1]
        curr_len = len(current_word)
        
        # --- 1. Find Full Match Candidates ---
        # Candidates must contain both req1 and req2 internally
        set1 = self.internal_char_index.get(req1, set())
        set2 = self.internal_char_index.get(req2, set())
        
        if req1 == req2:
            candidates = set1
        else:
            candidates = set1.intersection(set2)
            
        best_word = None
        max_score = -1
        
        # Sort candidates to ensure deterministic behavior if scores are equal, 
        # and potentially process higher value targets first, though linear scan is safer for full evaluation.
        # We'll just iterate.
        
        for word in candidates:
            if word in word_history:
                continue
            if len(word) == curr_len:
                continue
            
            # Calculate Score
            score = len(word)
            
            # Hyphen Penalty
            if '-' in word:
                score = score // 2
            
            # Consecutive Bonus
            # Check if req1 and req2 appear together in the word
            # Since we know req1 and req2 are internal, the pair will be internal too.
            if req1 == req2:
                # Need two consecutive req1 letters (e.g., "ll")
                if req1 + req1 in word:
                    score *= 2
            else:
                if (req1 + req2 in word) or (req2 + req1 in word):
                    score *= 2
            
            # Heuristic: Small bonus for words ending in difficult letters (J, Q, X, Z, V, W, K)
            # to make it harder for the opponent.
            if word[-1] in "jqxzvwk":
                score += 5
            
            if score > max_score:
                max_score = score
                best_word = word
                
        if best_word:
            return best_word

        # --- 2. Partial Match Fallback ---
        # If no full match, find a word with at least one required letter internally
        # We want to minimize penalty (shortest word).
        
        partial_candidates = set1.union(set2)
        
        best_partial = None
        min_penalty = float('inf')
        
        for word in partial_candidates:
            if word in word_history:
                continue
            if len(word) == curr_len:
                continue
            
            # Calculate penalty (negative points)
            penalty = len(word)
            if '-' in word:
                penalty = penalty // 2
            
            if penalty < min_penalty:
                min_penalty = penalty
                best_partial = word
                
        if best_partial:
            return best_partial
            
        # --- 3. Panic Fallback ---
        # If even partial match fails (rare), return a random word from dictionary
        # that isn't in history. This avoids a crash/timeout.
        for word in self.dictionary:
            if word not in word_history:
                return word
                
        return "error" # Should not be reached