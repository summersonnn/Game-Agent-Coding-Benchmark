"""
Agent Code: A4-WordFinder
Model: anthropic/claude-haiku-4.5
Run: 1
Generated: 2026-02-12 09:24:15
"""



class WordFinderAgent:
    def __init__(self, name):
        """Initialize the agent with a dictionary and indices for fast lookup."""
        self.name = name
        raw_dictionary = load_words()
        self.dictionary = {word.lower() for word in raw_dictionary}
        
        # Build index mapping characters to words containing them (for fast lookup)
        self.words_containing = {}
        for word in self.dictionary:
            for char in set(word):
                if char not in self.words_containing:
                    self.words_containing[char] = set()
                self.words_containing[char].add(word)
        
        # Letters that are difficult for opponent to work with (defensive strategy)
        self.difficult_letters = {'q', 'x', 'z', 'j', 'k', 'v', 'w'}
    
    def make_move(self, current_word, word_history):
        """
        Find and return the next word based on the previous word.
        
        Strategy:
        1. Find all valid words containing both required letters (first & last of current_word)
        2. Score each word (length, with hyphen penalty and consecutive bonus)
        3. Return the highest-scoring word, using difficult letters as tie-breaker
        4. Fallback to partial moves if no valid word exists
        """
        current_word = current_word.lower()
        word_history = {w.lower() for w in word_history}
        
        first_char = current_word[0]
        last_char = current_word[-1]
        prev_length = len(current_word)
        
        # Get candidate words that contain both required characters
        if first_char in self.words_containing and last_char in self.words_containing:
            candidates = self.words_containing[first_char] & self.words_containing[last_char]
        else:
            candidates = set()
        
        # Find valid words that satisfy all constraints
        valid_words = []
        
        for word in candidates:
            # Skip if already used
            if word in word_history:
                continue
            
            # Skip if same length as previous word
            if len(word) == prev_length:
                continue
            
            # Skip if required letters are at start or end positions
            if word[0] == first_char or word[-1] == first_char:
                continue
            if word[0] == last_char or word[-1] == last_char:
                continue
            
            # Valid word - calculate score and add to candidates
            score = self._calculate_score(word, first_char, last_char)
            is_difficult = word[-1] in self.difficult_letters  # Tie-breaker: difficult last letter
            valid_words.append((score, is_difficult, word))
        
        if valid_words:
            # Sort by score (descending), then by difficulty (prefer difficult letters)
            valid_words.sort(reverse=True)
            return valid_words[0][2]
        
        # Fallback 1: Partial move (one required letter only)
        partial_words = []
        for word in self.dictionary:
            if word in word_history or len(word) == prev_length:
                continue
            
            # Must contain at least one required letter in valid position (not at start/end)
            has_valid_first = (first_char in word and 
                              word[0] != first_char and 
                              word[-1] != first_char)
            has_valid_last = (last_char in word and 
                             word[0] != last_char and 
                             word[-1] != last_char)
            
            if has_valid_first or has_valid_last:
                is_difficult = word[-1] in self.difficult_letters
                partial_words.append((len(word), is_difficult, word))
        
        if partial_words:
            # Sort by length (to minimize penalty), then by difficulty
            partial_words.sort(reverse=True)
            return partial_words[0][2]
        
        # Fallback 2: Any valid unused word of different length (should rarely happen)
        for word in sorted(self.dictionary, key=len, reverse=True):
            if word not in word_history and len(word) != prev_length:
                return word
        
        return "a"
    
    def _calculate_score(self, word, first_char, last_char):
        """
        Calculate the score for a word according to game rules:
        - Base: word length
        - Hyphen penalty: ÷2 if contains "-"
        - Consecutive bonus: ×2 if required letters appear consecutively (in either order)
        """
        base_score = float(len(word))
        
        # Apply hyphen penalty
        if '-' in word:
            base_score /= 2.0
        
        # Apply consecutive letter bonus
        for i in range(len(word) - 1):
            if ((word[i] == first_char and word[i+1] == last_char) or
                (word[i] == last_char and word[i+1] == first_char)):
                base_score *= 2.0
                break
        
        return base_score
