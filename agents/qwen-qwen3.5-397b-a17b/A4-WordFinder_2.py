"""
Agent Code: A4-WordFinder
Model: qwen/qwen3.5-397b-a17b
Run: 2
Generated: 2026-02-16 18:11:06
"""


import random
import collections


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        # Load the dictionary provided by the environment
        self.dictionary = load_words()
        
        # Pre-process dictionary for faster lookups during make_move
        # We group words by length to allow iterating from longest to shortest
        # We only care about words with length >= 3 (need internal characters)
        self.words_by_length = collections.defaultdict(list)
        self.max_len = 0
        self.all_words_list = []
        
        for word in self.dictionary:
            l = len(word)
            if l >= 3:
                self.words_by_length[l].append(word)
                if l > self.max_len:
                    self.max_len = l
            self.all_words_list.append(word)
            
    def make_move(self, current_word, word_history):
        # Normalize current_word to lowercase to match dictionary
        current_word = current_word.lower()
        
        # Identify required characters
        c1 = current_word[0]
        c2 = current_word[-1]
        current_len = len(current_word)
        same_char = (c1 == c2)
        
        best_word = None
        best_score = -1
        
        # --- Phase 1: Search for Valid Full Move (Contains BOTH c1 and c2 internally) ---
        # Iterate lengths descending to find high scoring words first
        for length in range(self.max_len, 2, -1):
            # Pruning: If max possible score for this length (length * 2) is not better 
            # than current best_score, we can stop searching entirely.
            if best_score > 0 and length * 2 <= best_score:
                break
                
            if length == current_len:
                continue
                
            candidates = self.words_by_length.get(length, [])
            for word in candidates:
                if word in word_history:
                    continue
                
                # Check internal containment
                # Slicing word[1:-1] creates a new string, but is fast enough
                mid = word[1:-1]
                
                if same_char:
                    # Need at least 2 occurrences of c1 in mid
                    if mid.count(c1) < 2:
                        continue
                else:
                    # Need at least 1 of c1 AND 1 of c2 in mid
                    if c1 not in mid or c2 not in mid:
                        continue
                
                # Calculate Score
                score = length
                if '-' in word:
                    score = score // 2
                
                # Check Consecutive Bonus
                # Bonus applies if c1+c2 or c2+c1 appears in mid
                if (c1 + c2) in mid or (c2 + c1) in mid:
                    score *= 2
                
                if score > best_score:
                    best_score = score
                    best_word = word
        
        if best_word:
            return best_word
            
        # --- Phase 2: Partial Move Fallback (Contains ONLY ONE internally) ---
        # Only reached if no valid full move exists.
        # We want to minimize penalty, so prefer shorter words.
        # Penalty is negative length.
        
        for length in range(3, self.max_len + 1):
            if length == current_len:
                continue
            
            candidates = self.words_by_length.get(length, [])
            for word in candidates:
                if word in word_history:
                    continue
                
                mid = word[1:-1]
                # Check if at least one required char is present internally
                # Since Full Move search failed, we know we can't have both (or valid combo)
                # So we just check for existence of either.
                # For same_char case: Full required count>=2. Partial requires count>=1.
                
                valid_partial = False
                if same_char:
                    if mid.count(c1) >= 1:
                        valid_partial = True
                else:
                    if (c1 in mid) or (c2 in mid):
                        valid_partial = True
                
                if valid_partial:
                    return word
        
        # --- Phase 3: Last Resort ---
        # If absolutely no partial move found (extremely unlikely), pick any valid word
        # to avoid invalid move penalty (engine plays random valid move on invalid).
        # We try to pick one not in history.
        for word in self.all_words_list:
            if word not in word_history and len(word) != current_len:
                return word
                
        # If history contains everything (game end), return first dict word
        return self.all_words_list[0] if self.all_words_list else "error"