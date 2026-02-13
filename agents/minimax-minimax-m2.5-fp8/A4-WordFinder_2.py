"""
Agent Code: A4-WordFinder
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:10:12
"""



import random


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Pre-compute words grouped by first and last letters for faster lookup
        self.words_by_fl = {}  # (first, last) -> set of words
        
        for word in self.dictionary:
            if len(word) >= 2:
                key = (word[0], word[-1])
                if key not in self.words_by_fl:
                    self.words_by_fl[key] = set()
                self.words_by_fl[key].add(word)
    
    def make_move(self, current_word, word_history):
        if current_word is None:
            # Starting word - choose a random long word
            valid_starters = [w for w in self.dictionary if len(w) >= 5 and '-' not in w]
            valid_starters = [w for w in valid_starters if w not in word_history]
            if valid_starters:
                return max(valid_starters, key=len)
            return "example"
        
        required_first = current_word[0]
        required_last = current_word[-1]
        current_len = len(current_word)
        
        # Try to find a valid word with BOTH required letters
        best_word = None
        best_score = -float('inf')
        
        # Search through dictionary for valid words
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == current_len:
                continue
            if '-' in word:
                continue
            
            # Check if word contains both required letters
            if required_first not in word or required_last not in word:
                continue
            
            # Check position constraint: required letters cannot be first or last
            if word[0] == required_first or word[-1] == required_first:
                continue
            if word[0] == required_last or word[-1] == required_last:
                continue
            
            # Calculate score
            base_score = len(word)
            
            # Check for consecutive bonus (2x multiplier)
            concat1 = required_first + required_last
            concat2 = required_last + required_first
            if concat1 in word or concat2 in word:
                base_score *= 2
            
            if base_score > best_score:
                best_score = base_score
                best_word = word
        
        if best_word:
            return best_word
        
        # If no valid word found, try partial move (one required letter only)
        # Prioritize the letter that might lead to better future positions
        for required_letter in [required_first, required_last]:
            for word in self.dictionary:
                if word in word_history:
                    continue
                if len(word) == current_len:
                    continue
                
                if required_letter not in word:
                    continue
                if word[0] == required_letter or word[-1] == required_letter:
                    continue
                
                # Valid partial move - return negative scoring word (shorter = less negative)
                return min([w for w in self.dictionary 
                           if w not in word_history 
                           and len(w) != current_len
                           and required_letter in w
                           and w[0] != required_letter
                           and w[-1] != required_letter], 
                          key=len, default=None) or word
        
        # Last resort: return any valid word that doesn't violate rules
        for word in self.dictionary:
            if word not in word_history and len(word) != current_len:
                return word
        
        return "the"
