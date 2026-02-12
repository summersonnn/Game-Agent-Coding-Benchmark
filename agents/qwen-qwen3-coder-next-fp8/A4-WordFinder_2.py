"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-coder-next
Run: 2
Generated: 2026-02-12 09:31:57
"""



import random


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # Returns a set of lowercase words
        
        # Precompute word lengths for efficient lookup
        self.words_by_length = {}
        for word in self.dictionary:
            length = len(word)
            if length not in self.words_by_length:
                self.words_by_length[length] = set()
            self.words_by_length[length].add(word)
        
        # Precompute first and last letters for quick filtering
        self.word_info = {}
        for word in self.dictionary:
            self.word_info[word] = (word[0], word[-1])
    
    def make_move(self, current_word, word_history):
        """
        Called when it's your turn.
        
        Parameters:
        -----------
        current_word : str
            The word played by the opponent (or the starting word).
        word_history : set
            A set of all words that have been used so far in the game (by both players).
            
        Returns:
        --------
        str
            Your word choice.
        """
        try:
            # Get required letters (first and last of current_word)
            req_first = current_word[0].lower()
            req_last = current_word[-1].lower()
            current_length = len(current_word)
            
            # Filter out words in history
            available_words = [w for w in self.dictionary if w not in word_history]
            
            # Separate valid words (both letters, not at ends, different length)
            valid_candidates = []
            for word in available_words:
                # Skip if same length as current word
                if len(word) == current_length:
                    continue
                    
                # Skip if word is too short to contain required letters in middle
                if len(word) < 3:
                    continue
                
                # Check if word contains both required letters
                if req_first not in word or req_last not in word:
                    continue
                
                # Check positions - required letters must not be at start or end
                word_first = word[0].lower()
                word_last = word[-1].lower()
                
                if word_first == req_first or word_last == req_first:
                    continue
                if word_first == req_last or word_last == req_last:
                    continue
                
                # This is a valid word
                valid_candidates.append(word)
            
            # If we found valid candidates, pick the best one
            if valid_candidates:
                # Score candidates by points (with bonuses) and potential to challenge opponent
                best_score = -1
                best_word = None
                
                for word in valid_candidates:
                    # Calculate base points
                    base_points = len(word)
                    
                    # Apply hyphen penalty
                    if '-' in word:
                        base_points = base_points / 2
                    
                    # Check for consecutive letter bonus
                    word_lower = word.lower()
                    # Check for "PH" or "HP" pattern
                    if req_first + req_last in word_lower or req_last + req_first in word_lower:
                        points = base_points * 2
                    else:
                        points = base_points
                    
                    # Prefer longer words and words with consecutive letters
                    if points > best_score or (points == best_score and 
                                               (best_word is None or 
                                                len(word) > len(best_word))):
                        best_score = points
                        best_word = word
                
                if best_word:
                    return best_word
            
            # If no valid word found, try partial move (one required letter)
            partial_candidates = []
            for word in available_words:
                # Skip if same length as current word
                if len(word) == current_length:
                    continue
                
                # Skip if word is too short
                if len(word) < 3:
                    continue
                
                word_lower = word.lower()
                word_first = word_lower[0]
                word_last = word_lower[-1]
                
                # Check for first required letter in middle
                if req_first in word_lower:
                    idx = word_lower.find(req_first)
                    if idx != 0 and idx != len(word_lower) - 1:
                        partial_candidates.append(word)
                        continue
                
                # Check for last required letter in middle
                if req_last in word_lower:
                    idx = word_lower.find(req_last)
                    if idx != 0 and idx != len(word_lower) - 1:
                        partial_candidates.append(word)
                        continue
            
            # Pick the best partial candidate (longest word to minimize negative points)
            if partial_candidates:
                # Choose longest partial word to minimize penalty
                return max(partial_candidates, key=len)
            
            # If no partial move possible either, return a random valid dictionary word
            # (will result in invalid move penalty, but that's unavoidable)
            if available_words:
                return random.choice(available_words)
            
            # Last resort: return empty string (will crash or be invalid)
            return current_word + "x"
        
        except Exception:
            # On error, try to return something to avoid crash penalty
            return current_word + "x"
