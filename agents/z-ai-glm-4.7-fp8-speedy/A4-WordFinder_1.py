"""
Agent Code: A4-WordFinder
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 1
Generated: 2026-02-12 09:53:09
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    """
    An optimized agent for the WordFinder game.
    Pre-computes valid moves and partial moves in __init__ to ensure fast turn times.
    """
    def __init__(self, name):
        self.name = name
        # Load the dictionary
        self.dictionary = load_words()
        
        # Lookup structure: key=(c1, c2), value=list of (word, length, first, last, has_hyphen, bonus)
        self.lookup = defaultdict(list)
        
        # Partial move structure: key=char, value=list of (word, length, first, last, has_hyphen)
        self.partial_lookup = defaultdict(list)
        
        # Rarity weights for defensive play (giving opponent hard letters)
        self.rarity = {
            'z': 10, 'q': 10, 'x': 10, 'j': 10, 
            'k': 5, 'v': 5, 'f': 5, 'b': 5, 'p': 5, 'w': 5, 'y': 5,
            'g': 3, 'h': 3, 'm': 3, 'c': 3, 'd': 3
        }

        # Pre-compute valid moves for all possible character pairs
        self._precompute_moves()

    def _precompute_moves(self):
        """
        Builds the lookup tables. This runs once at initialization.
        """
        for w in self.dictionary:
            L = len(w)
            if L < 3: 
                continue # Words < 3 letters cannot satisfy position constraints for any pair
            
            first = w[0]
            last = w[-1]
            has_hyphen = '-' in w
            
            # Identify letters that are NOT at the start or end
            # These are the letters that can be the "required" letters from a previous word
            valid_inner_chars = set(w) - {first, last}
            
            # 1. Build Partial Move Lookup
            # A word is a candidate for a partial move on 'c' if it contains 'c' (not at edges)
            for c in valid_inner_chars:
                self.partial_lookup[c].append((w, L, first, last, has_hyphen))
            
            # 2. Build Full Move Lookup
            # For every pair of valid inner letters (c1, c2), this word is a valid response
            # if the previous word started with c1 and ended with c2 (or vice versa).
            chars_list = list(valid_inner_chars)
            for i in range(len(chars_list)):
                c1 = chars_list[i]
                for j in range(i, len(chars_list)):
                    c2 = chars_list[j]
                    
                    # Check for consecutive bonus
                    # Bonus applies if c1 and c2 are adjacent in the word (in either order)
                    bonus = False
                    if c1 != c2:
                        if (c1 + c2 in w) or (c2 + c1 in w):
                            bonus = True
                    else:
                        # If c1 == c2, we need "cc" or "CC" in the word
                        if (c1 + c1 in w):
                            bonus = True
                    
                    entry = (w, L, first, last, has_hyphen, bonus)
                    
                    # Store under (c1, c2)
                    self.lookup[(c1, c2)].append(entry)
                    
                    # Store under (c2, c1) as well because the requirement is symmetric
                    # (Previous word "AB" requires A and B; "BA" requires B and A)
                    if c1 != c2:
                        self.lookup[(c2, c1)].append(entry)

    def make_move(self, current_word, word_history):
        # 1. Analyze the current word
        c1 = current_word[0]
        c2 = current_word[-1]
        L_prev = len(current_word)
        
        # 2. Try to find a full valid move (contains both letters)
        candidates = self.lookup.get((c1, c2), [])
        
        best_word = None
        best_score = -float('inf')
        
        for w, L, first, last, hyphen, bonus in candidates:
            # Filter constraints
            if w in word_history:
                continue
            if L == L_prev:
                continue
            
            # Calculate Score
            # Base = Length
            score = L
            # Hyphen Penalty
            if hyphen:
                score //= 2
            # Consecutive Bonus
            if bonus:
                score *= 2
            
            # Defensive Heuristic:
            # Prefer words that start/end with rare letters to make opponent's turn hard.
            defense = self.rarity.get(first, 1) + self.rarity.get(last, 1)
            
            # Total value: Score + Defense Weight
            # We prioritize points, but defense breaks ties.
            total_val = score + (defense * 0.5)
            
            if total_val > best_score:
                best_score = total_val
                best_word = w
        
        if best_word:
            return best_word
            
        # 3. Fallback: Partial Move (Contains exactly one of the letters)
        # We want the shortest word to minimize the negative penalty.
        
        # Helper to filter candidate lists
        def get_filtered(c_list):
            res = []
            for item in c_list:
                w, L, first, last, hyphen = item
                if w not in word_history and L != L_prev:
                    res.append((w, L))
            return res

        p1 = get_filtered(self.partial_lookup.get(c1, []))
        p2 = get_filtered(self.partial_lookup.get(c2, []))
        
        # We need words that contain c1 but NOT c2, OR c2 but NOT c1.
        # Since 'p1' are words containing c1 (not at edges) and 'p2' are words containing c2 (not at edges),
        # valid partials are (p1 - p2) U (p2 - p1).
        
        # Convert to sets for fast difference operation
        p1_set = set(x[0] for x in p1)
        p2_set = set(x[0] for x in p2)
        
        valid_partials = []
        
        # Words with c1, not c2
        for w, L in p1:
            if w not in p2_set:
                valid_partials.append((w, L))
                
        # Words with c2, not c1
        for w, L in p2:
            if w not in p1_set:
                valid_partials.append((w, L))
                
        if valid_partials:
            # Sort by length to minimize penalty
            valid_partials.sort(key=lambda x: x[1])
            return valid_partials[0][0]
            
        # 4. Ultimate Fallback
        # If absolutely no move found (should be rare with large dictionaries),
        # return any valid word not in history to accept the -10 penalty gracefully.
        for w in self.dictionary:
            if w not in word_history:
                return w
                
        return "VOID" # Should never reach here unless dictionary exhausted
