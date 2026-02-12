"""
Agent Code: A4-WordFinder
Model: google/gemini-3-pro-preview
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

from collections import defaultdict
import random

class WordFinderAgent:
    """
    Agent that plays WordFinder by finding the highest scoring valid word.
    It uses pre-computed lookups for efficient filtering of the dictionary
    to satisfy letter and position constraints.
    """
    def __init__(self, name):
        """
        Initialize the agent and pre-process the dictionary.
        """
        self.name = name
        self.dictionary = load_words()  # Load the full word dictionary
        
        # Pre-compute a lookup table: char -> set of words containing that char in the MIDDLE.
        # This allows O(1) retrieval of candidate words for specific letter requirements.
        self.middle_char_map = defaultdict(set)
        
        for w in self.dictionary:
            # Words with length < 3 cannot contain letters that are NOT start/end.
            # e.g., "it" (len 2): 'i' is start, 't' is end. Middle is empty.
            if len(w) < 3:
                continue
                
            # Identify characters present in the "valid zone" (between first and last char)
            # w[1:-1] extracts the middle substring
            middle_chars = set(w[1:-1])
            
            for char in middle_chars:
                self.middle_char_map[char].add(w)

    def make_move(self, current_word, word_history):
        """
        Determine the best word to play based on constraints and scoring rules.
        """
        # 1. Identify Required Letters
        if not current_word:
            # Fallback for game start (though game engine usually handles this)
            req1, req2 = 'a', 'e'
            prev_len = 0
        else:
            req1 = current_word[0].lower()
            req2 = current_word[-1].lower()
            prev_len = len(current_word)

        # 2. Find Full Match Candidates
        # We need words that contain BOTH req1 and req2 in the middle.
        # Intersection of the pre-computed sets gives us these candidates efficiently.
        if req1 and req2:
            candidates = self.middle_char_map[req1].intersection(self.middle_char_map[req2])
        else:
            candidates = set()

        valid_moves = []
        
        # Prepare for consecutive bonus check
        bonus_seq_1 = req1 + req2
        bonus_seq_2 = req2 + req1
        same_req_chars = (req1 == req2)

        for w in candidates:
            # Constraint: Uniqueness
            if w in word_history:
                continue
            
            # Constraint: Length
            w_len = len(w)
            if w_len == prev_len:
                continue
            
            # Constraint: Position
            # The required letters cannot be the first or last letters of the NEW word.
            if w.startswith(req1) or w.startswith(req2):
                continue
            if w.endswith(req1) or w.endswith(req2):
                continue
            
            # Constraint: Same Letter Count
            # If req1 == req2 (e.g. 'e', 'e'), the word must contain at least two 'e's in the middle.
            # The set intersection only guarantees existence of at least one.
            if same_req_chars and w[1:-1].count(req1) < 2:
                continue

            # Scoring Calculation
            # 1. Base Points (Length)
            # 2. Hyphen Penalty
            if '-' in w:
                base_points = w_len / 2
            else:
                base_points = w_len
            
            # 3. Consecutive Bonus (2x)
            # Applied after hyphen penalty.
            # Letters must appear consecutively (e.g., "PH" or "HP").
            if (bonus_seq_1 in w) or (bonus_seq_2 in w):
                final_score = base_points * 2
            else:
                final_score = base_points
            
            valid_moves.append((final_score, w))

        # 3. Select Best Full Move
        if valid_moves:
            # Sort valid moves by score descending
            valid_moves.sort(key=lambda x: x[0], reverse=True)
            return valid_moves[0][1]

        # 4. Partial Move (Last Resort)
        # If no valid word exists, play a word containing ONE required letter.
        # Strategy: Minimize penalty (penalty based on length -> choose shortest word).
        partial_candidates = set()
        partial_candidates.update(self.middle_char_map[req1])
        partial_candidates.update(self.middle_char_map[req2])
        
        best_partial = None
        min_partial_len = float('inf')
        
        for w in partial_candidates:
            if w in word_history: continue
            if len(w) == prev_len: continue # Respect length constraint even for partials
            
            # Verify position constraints for the letters present
            # If the word contains req1, req1 must not be at start/end
            if req1 in w[1:-1]:
                if w.startswith(req1) or w.endswith(req1): continue
            
            # If the word contains req2, req2 must not be at start/end
            if req2 in w[1:-1]:
                if w.startswith(req2) or w.endswith(req2): continue
                
            # If we reached here, it's a valid partial move
            if len(w) < min_partial_len:
                min_partial_len = len(w)
                best_partial = w
                
        if best_partial:
            return best_partial

        # 5. Absolute Fallback
        # Return any unused word to avoid crashing (accepting invalid move penalty)
        for w in self.dictionary:
            if w not in word_history:
                return w
                
        return "giveup"
