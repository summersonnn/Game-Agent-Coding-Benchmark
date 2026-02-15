"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-coder-next@preset/fp8
Run: 1
Generated: 2026-02-14 18:23:39
"""



import random


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Pre-process dictionary for efficient lookup
        # Group words by length and by (first_char, last_char) pairs
        self.words_by_length = {}
        self.words_by_ends = {}  # key: (first_char, last_char), value: set of words
        
        for word in self.dictionary:
            # Store by length
            length = len(word)
            if length not in self.words_by_length:
                self.words_by_length[length] = set()
            self.words_by_length[length].add(word)
            
            # Store by first and last characters
            first_char = word[0]
            last_char = word[-1]
            ends_key = (first_char, last_char)
            if ends_key not in self.words_by_ends:
                self.words_by_ends[ends_key] = set()
            self.words_by_ends[ends_key].add(word)
    
    def make_move(self, current_word, word_history):
        # Get required characters (first and last of current word)
        first_char = current_word[0].lower()
        last_char = current_word[-1].lower()
        required_chars = (first_char, last_char)
        
        # Get current word length
        current_length = len(current_word)
        
        # Find valid words that meet all criteria
        valid_moves = []
        
        # Try to find words containing both required letters (not at start/end)
        for word in self.dictionary:
            # Skip if word is already used
            if word in word_history:
                continue
            
            # Skip words of same length as current word
            if len(word) == current_length:
                continue
            
            # Check if word contains both required letters
            if first_char not in word or last_char not in word:
                continue
            
            # Check positions: required letters cannot be at start or end
            if word[0] == first_char or word[-1] == first_char:
                continue
            if word[0] == last_char or word[-1] == last_char:
                continue
            
            # Word passes all checks
            valid_moves.append(word)
        
        # If no valid moves found, try partial moves (only one required letter)
        if not valid_moves:
            partial_moves = []
            
            # Try to find words containing only the first required letter
            for word in self.dictionary:
                if word in word_history:
                    continue
                if len(word) == current_length:
                    continue
                if first_char not in word:
                    continue
                if word[0] == first_char or word[-1] == first_char:
                    continue
                # Must not contain the other required letter
                if last_char in word:
                    continue
                    
                partial_moves.append(word)
            
            # Try to find words containing only the last required letter
            for word in self.dictionary:
                if word in word_history:
                    continue
                if len(word) == current_length:
                    continue
                if last_char not in word:
                    continue
                if word[0] == last_char or word[-1] == last_char:
                    continue
                # Must not contain the other required letter
                if first_char in word:
                    continue
                    
                partial_moves.append(word)
            
            if partial_moves:
                # Return the longest partial move to minimize penalty
                return max(partial_moves, key=len)
            
            # If no partial moves either, return a random word from dictionary (will be treated as invalid)
            return random.choice(list(self.dictionary))
        
        # Score valid moves to find the best one
        best_move = None
        best_score = -1
        
        for word in valid_moves:
            # Base score = word length
            score = len(word)
            
            # Apply hyphen penalty
            if '-' in word:
                score = score / 2
            
            # Check for consecutive letters bonus
            # Look for first_char+last_char or last_char+first_char as consecutive pairs
            consecutive_found = False
            for i in range(len(word) - 1):
                if (word[i] == first_char and word[i+1] == last_char) or \
                   (word[i] == last_char and word[i+1] == first_char):
                    consecutive_found = True
                    break
            
            if consecutive_found:
                score *= 2
            
            # Prefer longer words (after scoring) to maximize points
            if score > best_score:
                best_score = score
                best_move = word
        
        return best_move if best_move else random.choice(list(self.dictionary))
