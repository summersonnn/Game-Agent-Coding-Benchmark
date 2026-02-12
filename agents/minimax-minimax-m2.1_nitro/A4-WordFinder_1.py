"""
Agent Code: A4-WordFinder
Model: minimax/minimax-m2.1:nitro
Run: 1
Generated: 2026-02-12 11:23:23
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    """
    WordFinder Agent Implementation
    
    This agent uses precomputed data structures to efficiently find valid words
    that maximize points while following all game rules.
    """
    
    def __init__(self, name):
        """
        Initialize the agent with the provided name and load the word dictionary.
        Precompute data structures for efficient move selection.
        """
        self.name = name
        self.dictionary = load_words()  # Load the full word dictionary
        
        # Precompute data structures for efficient move selection
        self.word_db = {}  # key: (a,b) with a<=b, value: list of (word, consecutive_bonus)
        self.partial_db = {}  # key: letter c, value: list of words containing c (not at start/end)
        
        self._precompute_data()
    
    def _precompute_data(self):
        """
        Precompute data structures for efficient move selection.
        This runs once during initialization.
        """
        for word in self.dictionary:
            # Precompute for word_db: for every unordered pair (a,b) that the word satisfies
            distinct_letters = sorted(set(word))
            
            for i in range(len(distinct_letters)):
                for j in range(i, len(distinct_letters)):
                    a = distinct_letters[i]
                    b = distinct_letters[j]
                    
                    # Check count for a==b
                    if a == b:
                        if word.count(a) < 2:
                            continue
                    
                    # Check start and end condition
                    if word[0] in [a, b] or word[-1] in [a, b]:
                        continue
                    
                    # Check consecutive bonus
                    consecutive = False
                    if a != b:
                        if "ab" in word or "ba" in word:
                            consecutive = True
                    else:
                        if "aa" in word:
                            consecutive = True
                    
                    # Add to word_db
                    key = (a, b)
                    if key not in self.word_db:
                        self.word_db[key] = []
                    self.word_db[key].append((word, consecutive))
            
            # Precompute for partial_db: for every letter c in the word
            for c in set(word):
                if word[0] != c and word[-1] != c:
                    if c not in self.partial_db:
                        self.partial_db[c] = []
                    self.partial_db[c].append(word)
    
    def make_move(self, current_word, word_history):
        """
        Called when it's your turn to make a move.
        
        Parameters:
        -----------
        current_word : str
            The word played by the opponent (or the starting word).
        word_history : set
            A set of all words that have been used so far in the game.
        
        Returns:
        --------
        str
            Your word choice.
        """
        # Get required letters from current word
        a = current_word[0]
        b = current_word[-1]
        
        # Try to find a valid word first
        move = self._find_valid_move(a, b, current_word, word_history)
        if move:
            return move
        
        # If no valid move, try partial move
        move = self._find_partial_move(a, b, word_history)
        if move:
            return move
        
        # Last resort: return any word from dictionary not in history
        return self._find_any_word(word_history)
    
    def _find_valid_move(self, a, b, current_word, word_history):
        """
        Find a valid word that contains both required letters.
        """
        # Create key for lookup (unordered pair)
        key = (min(a, b), max(a, b))
        candidates = self.word_db.get(key, [])
        
        # Filter candidates
        valid_candidates = []
        for word, consecutive in candidates:
            if word in word_history:
                continue
            if len(word) == len(current_word):
                continue
            
            # Compute score
            base = len(word)
            if '-' in word:
                base = base // 2
            if consecutive:
                base = base * 2
            
            valid_candidates.append((base, word))
        
        if valid_candidates:
            # Sort by base points descending, then by length descending for tie-breaking
            valid_candidates.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
            return valid_candidates[0][1]
        
        return None
    
    def _find_partial_move(self, a, b, word_history):
        """
        Find a partial move containing only one required letter.
        """
        # Try to find words containing a but not b
        candidate_a = []
        if a in self.partial_db:
            for word in self.partial_db[a]:
                if word in word_history:
                    continue
                if b in word:  # Avoid words containing both letters
                    continue
                candidate_a.append(word)
        
        # Try to find words containing b but not a
        candidate_b = []
        if b in self.partial_db:
            for word in self.partial_db[b]:
                if word in word_history:
                    continue
                if a in word:  # Avoid words containing both letters
                    continue
                candidate_b.append(word)
        
        # Combine and find shortest word to minimize penalty
        all_candidates = candidate_a + candidate_b
        if all_candidates:
            min_length = min(len(word) for word in all_candidates)
            for word in all_candidates:
                if len(word) == min_length:
                    return word
        
        return None
    
    def _find_any_word(self, word_history):
        """
        Find any word from the dictionary not in word_history.
        """
        for word in self.dictionary:
            if word not in word_history:
                return word
        
        # If entire dictionary is used, return first word (will be invalid)
        return next(iter(self.dictionary))
