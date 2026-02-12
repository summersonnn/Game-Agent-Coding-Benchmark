"""
Agent Code: A4-WordFinder
Model: google/gemini-3-flash-preview
Run: 2
Generated: 2026-02-12 09:24:15
"""



import random

class WordFinderAgent:
    """
    An agent for the WordFinder game that prioritizes scoring through length and multipliers,
    while efficiently managing dictionary lookups and rule constraints.
    """
    def __init__(self, name):
        """
        Initialize the agent and pre-process the dictionary for efficient searching.
        """
        self.name = name
        try:
            # load_words() is a global function provided by the game environment
            self.dictionary = load_words()
        except:
            # Fallback for unexpected initialization environments
            self.dictionary = set()
        
        # Pre-categorize words into a map where keys are characters and values 
        # are sets of words where that character appears anywhere EXCEPT the first or last position.
        self.char_map = {}
        for word in self.dictionary:
            w_lower = word.lower()
            if len(w_lower) < 3:
                continue
            
            # Identify characters that are valid for the "middle position" constraint
            middle_chars = set(w_lower[1:-1])
            for char in middle_chars:
                if char not in self.char_map:
                    self.char_map[char] = set()
                self.char_map[char].add(w_lower)

    def _get_score(self, word, c1, c2):
        """
        Calculates the score for a word based on game rules:
        - Base points: Word length
        - Hyphen penalty: Length // 2 if the word contains a hyphen
        - Consecutive bonus: Multiplier of 2x if the required letters appear adjacently
        """
        length = len(word)
        score = length
        
        # Apply hyphen penalty (integer division as per example)
        if '-' in word:
            score //= 2
            
        # Apply consecutive bonus (check for both orders of c1 and c2)
        if (c1 + c2 in word) or (c2 + c1 in word):
            score *= 2
            
        return score

    def make_move(self, current_word, word_history):
        """
        Called when it's this agent's turn. Returns a valid word choice.
        """
        # 0. Extract required letters and constraints from the previous word
        curr = current_word.lower()
        c1 = curr[0]
        c2 = curr[-1]
        prev_len = len(curr)

        # 1. PRIMARY MOVE SEARCH
        # Find words containing both required characters in valid (middle) positions
        set1 = self.char_map.get(c1, set())
        set2 = self.char_map.get(c2, set())
        
        # Intersection gives words containing both c1 and c2 in their middle portions
        potential_candidates = set1 & set2
        
        best_word = None
        max_score = -1

        for word in potential_candidates:
            # Rule 4: Uniqueness (not used before)
            if word in word_history:
                continue
            
            # Rule 3: Length constraint (cannot be same length as previous word)
            if len(word) == prev_len:
                continue
            
            # Rule 2: Position Constraint
            # Required letters cannot be at the first or last position of the new word.
            # (Note: char_map ensures they are in the middle, but they could also repeat at edges)
            if word[0] == c1 or word[-1] == c1 or word[0] == c2 or word[-1] == c2:
                continue
            
            # Calculate score to find the optimal move
            score = self._get_score(word, c1, c2)
            
            # Strategy: Maximize score, then length, then alphabetical tie-breaker
            if score > max_score:
                max_score = score
                best_word = word
            elif score == max_score and score != -1:
                if len(word) > len(best_word):
                    best_word = word
                elif len(word) == len(best_word):
                    if word < best_word:
                        best_word = word
        
        if best_word:
            return best_word

        # 2. PARTIAL MOVE FALLBACK (Last Resort)
        # Play a word containing only ONE of the required letters in a valid position.
        # This results in negative points but keeps the game going.
        best_partial = None
        min_penalty_len = 10**6 # Penalty is based on length; aim for shortest word

        # Partial moves are only applicable if c1 and c2 are different
        if c1 != c2:
            # Check candidates containing c1 (properly) but not c2
            for word in set1:
                if word in word_history or len(word) == prev_len:
                    continue
                if word[0] == c1 or word[-1] == c1:
                    continue
                if c2 in word: # Must contain only one
                    continue
                if len(word) < min_penalty_len:
                    min_penalty_len = len(word)
                    best_partial = word
            
            # Check candidates containing c2 (properly) but not c1
            for word in set2:
                if word in word_history or len(word) == prev_len:
                    continue
                if word[0] == c2 or word[-1] == c2:
                    continue
                if c1 in word: # Must contain only one
                    continue
                if len(word) < min_penalty_len:
                    min_penalty_len = len(word)
                    best_partial = word

        if best_partial:
            return best_partial

        # 3. EMERGENCY FALLBACK
        # If no valid or partial move is found, play any unused word to avoid 
        # the -10 point penalty for an invalid move/crash.
        for word in self.dictionary:
            if word not in word_history and len(word) != prev_len:
                return word
        
        # Final fallback string (unlikely to be reached)
        return "example"
