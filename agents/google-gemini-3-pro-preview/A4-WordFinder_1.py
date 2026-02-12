"""
Agent Code: A4-WordFinder
Model: google/gemini-3-pro-preview
Run: 1
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    """
    Agent that plays WordFinder by pre-indexing the dictionary for efficient lookups.
    It prioritizes valid moves with consecutive letter bonuses and high base scores.
    """
    def __init__(self, name):
        """
        Initialize the agent and pre-compute word lookups.
        """
        self.name = name
        self.dictionary = load_words()
        
        # Map each character to a list of (word, base_points, length) tuples
        # This allows O(1) retrieval of words containing a specific character.
        self.char_map = defaultdict(list)
        
        for w in self.dictionary:
            w_len = len(w)
            
            # Calculate base points according to rules
            # Hyphenated words get half points (integer division based on example 13->6)
            if '-' in w:
                points = w_len // 2 
            else:
                points = w_len
            
            # Add word to the map for every unique character it contains.
            # We use set(w) to handle duplicates efficiently.
            for char in set(w):
                self.char_map[char].append((w, points, w_len))
        
        # Sort every list by points descending.
        # This acts as a greedy heuristic: we check the highest value words first.
        for char in self.char_map:
            self.char_map[char].sort(key=lambda x: x[1], reverse=True)

    def make_move(self, current_word, word_history):
        """
        Determines the best word to play based on constraints and scoring.
        """
        # 1. Parse Requirements
        req1 = current_word[0]
        req2 = current_word[-1]
        prev_len = len(current_word)
        
        # 2. Optimize Search Space
        # We need a word containing BOTH req1 and req2.
        # Strategy: Iterate through the list of the 'rarer' letter (shorter list)
        # to minimize the number of checks.
        list1 = self.char_map.get(req1, [])
        list2 = self.char_map.get(req2, [])
        
        if len(list1) < len(list2):
            search_list = list1
            must_have_char = req2
        else:
            search_list = list2
            must_have_char = req1
            
        best_word = None
        best_score = -1
        
        # 3. Search for a Valid Move
        for w, points, w_len in search_list:
            # Constraint: Uniqueness
            if w in word_history:
                continue
            
            # Constraint: Length
            if w_len == prev_len:
                continue
            
            # Constraint: Position (req chars cannot be start or end of new word)
            # This applies to BOTH required characters.
            if w.startswith(req1) or w.endswith(req1):
                continue
            if w.startswith(req2) or w.endswith(req2):
                continue
                
            # Constraint: Must contain the other required letter
            if must_have_char not in w:
                continue
            
            # Edge Case: If req1 == req2 (e.g. "LEVEL" -> L...L), we need two 'L's
            if req1 == req2 and w.count(req1) < 2:
                continue

            # Calculate Final Score (Base + Bonus)
            final_score = points
            
            # Bonus: Consecutive letters (req1+req2 OR req2+req1)
            # Example: needed 'P','H', found "SHEPHERD" (contains "PH")
            pattern1 = req1 + req2
            pattern2 = req2 + req1
            
            if pattern1 in w or pattern2 in w:
                final_score *= 2
            
            # Optimization: Track the best score found
            if final_score > best_score:
                best_score = final_score
                best_word = w
        
        # Return valid word if found
        if best_word:
            return best_word

        # 4. Partial Move (Last Resort)
        # If no valid word exists, play a word satisfying ONE constraint to minimize penalty.
        # Penalty is based on length, so we prefer the SHORTEST possible word here.
        
        candidates = []
        targets = [req1, req2] if req1 != req2 else [req1]
        
        for t_char in targets:
            s_list = self.char_map.get(t_char, [])
            for w, points, w_len in s_list:
                if w in word_history: continue
                if w_len == prev_len: continue
                
                # For partial move, the single required letter still cannot be at boundaries
                if w.startswith(t_char) or w.endswith(t_char):
                    continue
                    
                candidates.append(w)
        
        if candidates:
            # Sort by length ascending to minimize penalty
            candidates.sort(key=len)
            return candidates[0]

        # 5. Fail-safe (Should not happen with a standard dictionary)
        # Return a dummy string to avoid crashing, resulting in -10 penalty.
        return "skip"
