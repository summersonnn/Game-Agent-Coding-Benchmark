"""
Agent Code: A4-WordFinder
Model: minimax/minimax-m2.1:nitro
Run: 2
Generated: 2026-02-12 09:52:34
"""



class WordFinderAgent:
    """
    WordFinderAgent: A strategic agent for the WordFinder word game.
    
    Strategy:
    - Precomputes lookup tables for efficient move selection
    - Prioritizes high-scoring words (long words, consecutive letter bonus)
    - Uses partial moves as a last resort when no valid word exists
    - Filters out used words and enforces all game constraints
    """
    
    def __init__(self, name):
        """
        Initialize the agent with precomputed data structures for efficient gameplay.
        
        Args:
            name: Agent's name
        """
        self.name = name
        self.dictionary = load_words()  # Load the full word dictionary (lowercase)
        
        # Precomputation for efficient move lookup
        self.all_words = []  # List of valid words (length >= 3)
        self.word_data = []  # Metadata: (length, has_hyphen) for each word
        self.lookup = {}     # Maps (A, B) to list of word indices
        self.partial_lookup = {}  # Maps letter to list of words containing it (not at start/end)
        
        all_letters = 'abcdefghijklmnopqrstuvwxyz'
        all_letters_set = set(all_letters)
        
        for word in self.dictionary:
            # Skip words too short for valid moves (need middle positions)
            if len(word) < 3:
                continue
                
            index = len(self.all_words)
            self.all_words.append(word)
            self.word_data.append((len(word), '-' in word))
            
            first_char = word[0]
            last_char = word[-1]
            allowed_letters = all_letters_set - {first_char, last_char}
            set_chars = set(word)
            S = set_chars & allowed_letters
            
            # Add to lookup for all valid (A, B) pairs
            for A in S:
                for B in S:
                    key = (A, B)
                    if key not in self.lookup:
                        self.lookup[key] = []
                    self.lookup[key].append(index)
            
            # Add to partial_lookup for letters not at start/end
            for L in set_chars:
                if L != first_char and L != last_char:
                    if L not in self.partial_lookup:
                        self.partial_lookup[L] = []
                    self.partial_lookup[L].append(word)
    
    def make_move(self, current_word, word_history):
        """
        Determine the best move given the current game state.
        
        Args:
            current_word: The word played by the opponent (or starting word)
            word_history: Set of all words used in the game so far
            
        Returns:
            The chosen word for this turn
        """
        A = current_word[0]
        B = current_word[-1]
        current_length = len(current_word)
        
        # Try to find the best valid word
        best_word = None
        best_score = -1
        
        candidate_indices = self.lookup.get((A, B), [])
        
        for index in candidate_indices:
            word = self.all_words[index]
            length, has_hyphen = self.word_data[index]
            
            # Skip if length constraint violated or word already used
            if length == current_length or word in word_history:
                continue
            
            # Check for consecutive letter bonus (A and B appear consecutively)
            consecutive = False
            for i in range(len(word) - 1):
                pair = word[i:i+2]
                if pair == A + B or pair == B + A:
                    consecutive = True
                    break
            
            # Calculate score
            base = length // 2 if has_hyphen else length
            if consecutive:
                base *= 2
            
            if base > best_score:
                best_score = base
                best_word = word
        
        if best_word is not None:
            return best_word
        
        # No valid word found - try partial move
        candidates = []
        
        # Words containing only A (not B)
        if A in self.partial_lookup:
            for word in self.partial_lookup[A]:
                if len(word) != current_length and word not in word_history and B not in word:
                    candidates.append(word)
        
        # Words containing only B (not A)
        if B in self.partial_lookup:
            for word in self.partial_lookup[B]:
                if len(word) != current_length and word not in word_history and A not in word:
                    candidates.append(word)
        
        if candidates:
            # Choose shortest word to minimize penalty
            min_length = min(len(word) for word in candidates)
            for word in candidates:
                if len(word) == min_length:
                    return word
        
        # Last resort: return any valid dictionary word (will be penalized)
        for word in self.dictionary:
            if word not in word_history and len(word) != current_length:
                return word
        
        # If all words used, return any word (will be penalized)
        return next(iter(self.dictionary))
