"""
Agent Code: A4-WordFinder
Model: qwen/qwen3.5-397b-a17b
Run: 2
Generated: 2026-02-16 18:11:06
"""


import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        # Load the dictionary provided by the environment
        # load_words() is a global function available in the game environment
        self.dictionary = load_words()
        self.all_words = list(self.dictionary)
        
        # Precompute index of words by internal characters
        # internal_index[char] = set of words containing char in word[1:-1]
        # This allows O(1) retrieval of words containing specific internal letters
        self.internal_index = defaultdict(set)
        
        for word in self.dictionary:
            # Words must be at least length 3 to have internal characters
            if len(word) < 3:
                continue
            internal_chars = set(word[1:-1])
            for char in internal_chars:
                self.internal_index[char].add(word)
        
        # Letter rarity for tie-breaking (higher is rarer/harder for opponent)
        # Based on approximate English letter frequency (inverse)
        self.rarity = {
            'z': 26, 'q': 25, 'x': 24, 'j': 23, 'k': 22, 'v': 21, 'b': 20,
            'f': 19, 'y': 18, 'w': 17, 'g': 16, 'p': 15, 'm': 14, 'h': 13,
            'd': 12, 'c': 11, 'u': 10, 'l': 9, 'o': 8, 'n': 7, 'r': 6,
            't': 5, 'a': 4, 'i': 3, 's': 2, 'e': 1
        }

    def _calculate_score(self, word, c1, c2):
        """Calculate potential score for a word."""
        base = len(word)
        if '-' in word:
            base = base // 2
        
        # Check consecutive bonus
        # The letters can appear in either order: "PH" or "HP"
        # Must be inside the word (not start/end)
        internal = word[1:-1]
        if (c1 + c2) in internal or (c2 + c1) in internal:
            base *= 2
            
        return base

    def _get_rarity_score(self, word):
        """Calculate defensive score based on start/end letters."""
        return self.rarity.get(word[0], 0) + self.rarity.get(word[-1], 0)

    def make_move(self, current_word, word_history):
        c1 = current_word[0].lower()
        c2 = current_word[-1].lower()
        prev_len = len(current_word)
        
        # --- Phase 1: Full Move (Contains BOTH c1 and c2 internally) ---
        candidates = []
        
        set1 = self.internal_index.get(c1, set())
        set2 = self.internal_index.get(c2, set())
        
        if c1 == c2:
            # If required letters are the same, we need at least 2 occurrences internally
            # to strictly satisfy "contains first AND last" as distinct requirements.
            pool = set1
            for w in pool:
                if w[1:-1].count(c1) >= 2:
                    candidates.append(w)
        else:
            # Intersection of words containing c1 internally AND c2 internally
            pool = set1.intersection(set2)
            for w in pool:
                candidates.append(w)
        
        # Filter candidates by constraints
        valid_moves = []
        for w in candidates:
            # Position Constraint: Required letters cannot be at start or end
            # Even if char is internal, it might ALSO be at start/end.
            if w[0] == c1 or w[-1] == c1:
                continue
            if w[0] == c2 or w[-1] == c2:
                continue
            
            # Length Constraint
            if len(w) == prev_len:
                continue
            
            # Uniqueness
            if w in word_history:
                continue
            
            valid_moves.append(w)
        
        if valid_moves:
            # Sort by Score (Desc), then Rarity (Desc)
            valid_moves.sort(key=lambda w: (self._calculate_score(w, c1, c2), self._get_rarity_score(w)), reverse=True)
            return valid_moves[0]
            
        # --- Phase 2: Partial Move (Contains ONE of c1 or c2 internally) ---
        # Only if no Full Move is available
        partial_candidates = []
        
        if c1 == c2:
            # Words with exactly 1 internal occurrence of c1
            for w in set1:
                if w[1:-1].count(c1) == 1:
                    partial_candidates.append(w)
        else:
            # Union minus Intersection (Structurally partial)
            # Words that have c1 OR c2 internally, but NOT both.
            union = set1.union(set2)
            intersection = set1.intersection(set2)
            pool = union - intersection
            
            for w in pool:
                partial_candidates.append(w)
        
        # Filter partial candidates
        valid_partial = []
        for w in partial_candidates:
            # Position Constraint for the letter that IS present
            # Since w comes from internal_index, the char is guaranteed internal.
            # We must ensure it is not ALSO at start/end.
            if w in set1:
                if w[0] == c1 or w[-1] == c1:
                    continue
            else: # w in set2
                if w[0] == c2 or w[-1] == c2:
                    continue
            
            if len(w) == prev_len:
                continue
            if w in word_history:
                continue
            
            valid_partial.append(w)
            
        if valid_partial:
            # Minimize penalty -> Shortest word (assuming penalty is proportional to length)
            # Tie break: Rarity
            valid_partial.sort(key=lambda w: (len(w), -self._get_rarity_score(w)))
            return valid_partial[0]
            
        # --- Phase 3: Fallback ---
        # If nothing works, return a random valid word not in history.
        # This will likely be flagged as Invalid Move by the engine, 
        # but returning a dictionary word is better than crashing.
        for w in self.all_words:
            if w not in word_history:
                return w
        
        # Absolute last resort
        return "a"