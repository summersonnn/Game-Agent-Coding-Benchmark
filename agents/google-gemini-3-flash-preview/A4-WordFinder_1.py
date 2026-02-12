"""
Agent Code: A4-WordFinder
Model: google/gemini-3-flash-preview
Run: 1
Generated: 2026-02-12 09:24:15
"""



import random

class WordFinderAgent:
    """
    An optimized agent for the WordFinder game.
    It pre-processes the dictionary to find valid words quickly and 
    prioritizes high-scoring moves (long words and consecutive letter bonuses).
    """

    def __init__(self, name):
        """
        Initialize the WordFinder agent by pre-processing the dictionary.
        """
        self.name = name
        try:
            # load_words() is a global function provided by the game environment.
            full_dict = load_words()
        except NameError:
            # Fallback for environments where load_words is not defined.
            full_dict = set()
            
        # Store dictionary as lowercase for consistent processing.
        self.dictionary = {w.lower() for w in full_dict}
        
        # Pre-process the dictionary for high-speed lookups during turns.
        # We index words by the characters they contain in "middle" positions
        # (i.e., characters not at the very start or very end of the word).
        self.words_by_char = {}
        for word in self.dictionary:
            # Position Constraint implies words must be at least 3 letters long 
            # to have a middle character that isn't the first or last.
            if len(word) < 3:
                continue
            
            # Extract characters that appear anywhere except the first and last position.
            middle_chars = set(word[1:-1])
            for char in middle_chars:
                if char not in self.words_by_char:
                    self.words_by_char[char] = set()
                self.words_by_char[char].add(word)

    def _calculate_score(self, word, l1, l2):
        """
        Calculate the score for a word based on length, hyphens, and consecutive bonuses.
        """
        score = float(len(word))
        
        # Rule: Hyphen Penalty - Words containing a hyphen get half points.
        if '-' in word:
            score /= 2.0
            
        # Rule: Consecutive Letter Bonus - If the two required letters appear 
        # consecutively (in either order), base points are multiplied by 2.
        if (l1 + l2) in word or (l2 + l1) in word:
            score *= 2.0
            
        return score

    def make_move(self, current_word, word_history):
        """
        Called when it's the agent's turn to find a word based on the previous word.
        """
        # Normalize the input word and history.
        current_word = current_word.lower()
        history = {w.lower() for w in word_history}
        
        # Letter Constraint: New word must contain the first and last letters of the previous word.
        l1 = current_word[0]
        l2 = current_word[-1]
        
        # Search for words containing l1 and l2 in middle positions using our pre-processed index.
        set1 = self.words_by_char.get(l1, set())
        set2 = self.words_by_char.get(l2, set())
        
        # Intersection gives words containing both required letters in middle positions.
        candidates = set1 & set2
        
        # Apply Constraints:
        # 1. Position: Required letters (l1, l2) cannot be at the start or end of the new word.
        # 2. Length: New word length cannot equal the previous word's length.
        # 3. Uniqueness: Word cannot have been used already in the game history.
        valid_candidates = [
            w for w in candidates
            if w not in history
            and len(w) != len(current_word)
            and w[0] != l1 and w[0] != l2
            and w[-1] != l1 and w[-1] != l2
        ]
        
        if valid_candidates:
            # Strategy: Maximize score (primary) and length (secondary).
            # This prioritizes consecutive bonuses and long words.
            return max(valid_candidates, key=lambda w: (self._calculate_score(w, l1, l2), len(w)))
        
        # Partial Move Fallback (Last Resort):
        # If no word contains both required letters, find one that contains at least one.
        # This prevents the -10 invalid move penalty.
        partial_candidates = set1 | set2
        valid_partials = [
            w for w in partial_candidates
            if w not in history
            and len(w) != len(current_word)
            and w[0] != l1 and w[0] != l2
            and w[-1] != l1 and w[-1] != l2
        ]
        
        if valid_partials:
            # For partial moves, the score is negative based on length.
            # Minimize the penalty by choosing the shortest valid word.
            return min(valid_partials, key=len)
            
        # Absolute safety net: Return any unused word from the dictionary.
        # This ensures the agent returns a string and avoids a crash.
        for w in self.dictionary:
            if w not in history:
                return w
                
        return "fallback"
