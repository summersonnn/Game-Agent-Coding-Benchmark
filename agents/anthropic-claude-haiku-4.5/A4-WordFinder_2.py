"""
Agent Code: A4-WordFinder
Model: anthropic/claude-haiku-4.5
Run: 2
Generated: 2026-02-12 09:24:15
"""



class WordFinderAgent:
    def __init__(self, name):
        """
        Initialize the agent with the game dictionary.
        """
        self.name = name
        self.dictionary = load_words()
    
    def make_move(self, current_word, word_history):
        """
        Find the best word to play based on current_word constraints.
        
        Parameters:
        -----------
        current_word : str
            The word played by the opponent (or starting word)
        word_history : set
            All words used so far in the game
        
        Returns:
        --------
        str
            The word to play
        """
        # Extract constraints from current word
        current_upper = current_word.upper()
        req_first = current_upper[0]
        req_last = current_upper[-1]
        req_length = len(current_upper)
        
        # Try to find best valid word (containing both required letters)
        best_word = self._find_best_valid_word(
            req_first, req_last, req_length, word_history
        )
        
        if best_word:
            return best_word
        
        # Fallback: try partial move (one required letter only)
        partial_word = self._find_partial_move(
            req_first, req_last, req_length, word_history
        )
        
        return partial_word if partial_word else "example"
    
    def _find_best_valid_word(self, first, last, length, history):
        """
        Search for the best word containing both required letters.
        Optimizes for maximum score (prefers longer words and consecutive letters).
        """
        best_word = None
        best_score = -1.0
        
        for word in self.dictionary:
            # Skip already-used words
            if word in history:
                continue
            
            word_upper = word.upper()
            word_length = len(word_upper)
            
            # Length constraint: must differ from current word
            if word_length == length:
                continue
            
            # Must contain both required letters
            if first not in word_upper or last not in word_upper:
                continue
            
            # Position constraint: letters cannot be at start or end
            if word_upper[0] == first or word_upper[-1] == first:
                continue
            if word_upper[0] == last or word_upper[-1] == last:
                continue
            
            # Valid word found - calculate score and track best
            score = self._calculate_score(word_upper, first, last)
            if score > best_score:
                best_score = score
                best_word = word
        
        return best_word
    
    def _find_partial_move(self, first, last, length, history):
        """
        Search for a word with at least one required letter (fallback).
        Only used when no valid word with both letters exists.
        """
        best_word = None
        best_length = 0
        
        for word in self.dictionary:
            if word in history:
                continue
            
            word_upper = word.upper()
            
            if len(word_upper) == length:
                continue
            
            # Must have at least one required letter, not at start/end
            has_first = (first in word_upper and 
                        word_upper[0] != first and 
                        word_upper[-1] != first)
            has_last = (last in word_upper and 
                       word_upper[0] != last and 
                       word_upper[-1] != last)
            
            if (has_first or has_last) and len(word_upper) > best_length:
                best_length = len(word_upper)
                best_word = word
        
        return best_word
    
    def _calculate_score(self, word, first, last):
        """
        Calculate the score for a valid word.
        
        Scoring:
        - Base: word length
        - Hyphen penalty: divide by 2 if contains '-'
        - Consecutive bonus: multiply by 2 if required letters appear consecutively
        - Bonus applied AFTER penalty
        """
        score = float(len(word))
        
        # Apply hyphen penalty first
        if '-' in word:
            score /= 2.0
        
        # Check for consecutive required letters (bonus applied after penalty)
        for i in range(len(word) - 1):
            if (word[i] == first and word[i + 1] == last) or \
               (word[i] == last and word[i + 1] == first):
                score *= 2.0
                break
        
        return score
