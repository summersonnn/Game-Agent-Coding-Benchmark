"""
Agent Code: A4-WordFinder
Model: google/gemini-3-pro-preview
Run: 2
Generated: 2026-02-12 09:24:15
"""

import random

class WordFinderAgent:
    """
    A strategic agent for WordFinder that maximizes points through consecutive 
    letter bonuses, avoids hyphen penalties, and plays defensively by evaluating 
    the opponent's future move options.
    """
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Pre-compute internal characters for rapid set intersections during gameplay
        self.char_to_words = {}
        for w in self.dictionary:
            if len(w) >= 3:
                # We only care about internal characters
                internal_chars = set(w[1:-1])
                for c in internal_chars:
                    if c not in self.char_to_words:
                        self.char_to_words[c] = set()
                    self.char_to_words[c].add(w)
        
        # Pre-compute an approximation of how many options a pair of letters yields.
        # This is used as a defensive tie-breaker to leave the opponent with difficult letters.
        self.pair_abundance = {}
        chars = [chr(i) for i in range(97, 123)]
        chars.append('-')
        for c1 in chars:
            for c2 in chars:
                s1 = self.char_to_words.get(c1, set())
                s2 = self.char_to_words.get(c2, set())
                # For defensive play, fewer intersecting words = harder for opponent
                self.pair_abundance[(c1, c2)] = len(s1 & s2)

    def make_move(self, current_word, word_history):
        # Fallback for the very first turn if we start
        if not current_word:
            available = list(self.dictionary - word_history)
            return random.choice(available) if available else "example"
            
        c1 = current_word[0].lower()
        c2 = current_word[-1].lower()
        
        s1 = self.char_to_words.get(c1, set())
        s2 = self.char_to_words.get(c2, set())
        
        # O(1) intersection finds all words containing both letters internally
        candidates = s1 & s2
        
        valid_candidates = []
        for w in candidates:
            if w in word_history:
                continue
            if len(w) == len(current_word):
                continue
            if w[0] in (c1, c2) or w[-1] in (c1, c2):
                continue
            # If the required letters are the same (e.g., 'stats'), we need >= 2 instances internally
            if c1 == c2 and w[1:-1].count(c1) < 2:
                continue
            valid_candidates.append(w)
            
        if valid_candidates:
            best_word = None
            best_score = -float('inf')
            
            for w in valid_candidates:
                # 1. Base Score calculation
                base = len(w)
                
                # 2. Hyphen Penalty
                if '-' in w:
                    base = base / 2.0
                    
                # 3. Consecutive Letter Bonus
                if c1 + c2 in w or c2 + c1 in w:
                    base *= 2
                    
                # 4. Defensive tie-breaker (leaving fewer options for the opponent)
                nc1, nc2 = w[0].lower(), w[-1].lower()
                options = self.pair_abundance.get((nc1, nc2), 0)
                
                # Subtract a tiny fraction so length dominates, but defensively breaks ties
                final_score = base - (options / 1000000.0)
                
                if final_score > best_score:
                    best_score = final_score
                    best_word = w
                    
            return best_word
        
        else:
            # FALLBACK: Partial Move
            # No valid word with both letters exists, try words with AT LEAST ONE letter
            partial_cands = s1 | s2
            valid_partials = []
            
            for w in partial_cands:
                if w in word_history:
                    continue
                if len(w) == len(current_word):
                    continue
                if w[0] in (c1, c2) or w[-1] in (c1, c2):
                    continue
                valid_partials.append(w)
                
            if valid_partials:
                best_partial = None
                best_p_score = float('inf') # We want to MINIMIZE the penalty (length)
                
                for w in valid_partials:
                    base_penalty = len(w)
                    
                    nc1, nc2 = w[0].lower(), w[-1].lower()
                    options = self.pair_abundance.get((nc1, nc2), 0)
                    
                    # Tie-breaker: Add fraction to penalty, so smaller options win ties
                    score = base_penalty + (options / 1000000.0)
                    
                    if score < best_p_score:
                        best_p_score = score
                        best_partial = w
                        
                return best_partial
        
        # Absolute last resort to avoid crash/forfeit
        available = list(self.dictionary - word_history)
        return available[0] if available else "example"