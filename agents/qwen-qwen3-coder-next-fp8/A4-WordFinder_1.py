"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-coder-next
Run: 1
Generated: 2026-02-12 09:31:57
"""



import random


class WordFinderAgent:
    """
    Your agent implementation goes here.
    """
    def __init__(self, name):
        """
        Initialize your agent.
        """
        self.name = name
        self.dictionary = load_words()  # Load the full word dictionary
        
        # Precompute word length index for faster lookups
        self.length_index = {}
        for word in self.dictionary:
            length = len(word)
            if length not in self.length_index:
                self.length_index[length] = set()
            self.length_index[length].add(word)
    
    def make_move(self, current_word, word_history):
        """
        Called when it's your turn.

        Parameters:
        -----------
        current_word : str
            The word played by the opponent (or the starting word).

        word_history : set
            A set of all words that have been used so far in the game (by both players).
            This includes the current_word and all previous words.
            You MUST NOT return a word that is in this set.

        Returns:
        --------
        str
            Your word choice.
        """
        # Get required characters (first and last of current word)
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        current_length = len(current_word)
        
        # Precompute candidates that are valid words
        # We'll look for words that:
        # 1. Contain both first_char and last_char
        # 2. first_char is NOT at position 0 and last_char is NOT at position -1
        # 3. Length != current_length
        # 4. Not in word_history
        # 5. In dictionary
        
        best_move = None
        best_score = -1
        
        # Try to find a full move (contains both required letters)
        for word in self.dictionary:
            # Skip if already used
            if word in word_history:
                continue
            
            # Skip if wrong length
            if len(word) == current_length:
                continue
            
            # Skip if word is too short to contain letters in middle positions
            if len(word) < 3:
                continue
                
            # Check if word contains both required letters
            if first_char not in word or last_char not in word:
                continue
                
            # Check positions of required letters
            first_pos = word.find(first_char)
            last_pos = word.rfind(last_char)
            
            # Make sure first_char is not at position 0
            if first_pos == 0:
                continue
                
            # Make sure last_char is not at position -1
            if last_pos == len(word) - 1:
                continue
                
            # Calculate score
            base_points = len(word)
            
            # Check for hyphen penalty
            if '-' in word:
                base_points = base_points / 2
                
            # Check for consecutive letters bonus (in either order)
            has_consecutive = False
            for i in range(len(word) - 1):
                if (word[i] == first_char and word[i+1] == last_char) or \
                   (word[i] == last_char and word[i+1] == first_char):
                    has_consecutive = True
                    break
                    
            if has_consecutive:
                base_points *= 2
                
            # Update best move if this is better
            if base_points > best_score:
                best_score = base_points
                best_move = word
        
        # If no full move found, try partial move (contains only one required letter)
        if best_move is None:
            for letter in [first_char, last_char]:
                for word in self.dictionary:
                    # Skip if already used
                    if word in word_history:
                        continue
                    
                    # Skip if wrong length
                    if len(word) == current_length:
                        continue
                    
                    # Skip if word is too short
                    if len(word) < 3:
                        continue
                        
                    # Check if word contains the required letter
                    if letter not in word:
                        continue
                        
                    # Check position of required letter
                    pos = word.find(letter)
                    # Make sure it's not at position 0
                    if pos == 0:
                        continue
                    # Make sure it's not at position -1
                    if pos == len(word) - 1:
                        continue
                        
                    # Calculate penalty (negative points)
                    base_points = -len(word) / 2 if '-' in word else -len(word)
                    
                    # Update best move if this is better (less negative)
                    if base_points > best_score:
                        best_score = base_points
                        best_move = word
                
                # If we found a partial move, break
                if best_move is not None:
                    break
        
        # If still no move, return empty string (will be treated as invalid move with -10 penalty)
        if best_move is None:
            return ""
        
        return best_move
