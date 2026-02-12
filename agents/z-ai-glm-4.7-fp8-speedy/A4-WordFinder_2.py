"""
Agent Code: A4-WordFinder
Model: z-ai/glm-4.7@preset/fp8-speedy
Run: 2
Generated: 2026-02-12 09:24:15
"""



import random

class WordFinderAgent:
    """
    A strategic agent for the WordFinder game.
    """
    def __init__(self, name):
        """
        Initialize the agent and pre-compute lookup tables for efficiency.
        """
        self.name = name
        self.dictionary = load_words()
        
        # Map: character -> set of words containing that character
        self.char_map = {}
        
        # Map: word -> metadata (length, has_hyphen)
        self.word_meta = {}
        
        # Frequency map of letters at start/end positions for defensive strategy
        self.letter_freq = {}
        
        # Pre-process dictionary
        for word in self.dictionary:
            w = word.lower()
            length = len(w)
            has_hyphen = '-' in w
            first = w[0]
            last = w[-1]
            
            self.word_meta[w] = {
                'len': length,
                'hyphen': has_hyphen
            }
            
            # Update frequency for defensive heuristic (rare letters are better to leave opponent)
            self.letter_freq[first] = self.letter_freq.get(first, 0) + 1
            self.letter_freq[last] = self.letter_freq.get(last, 0) + 1
            
            # Index by unique characters
            unique_chars = set(w)
            for char in unique_chars:
                if char not in self.char_map:
                    self.char_map[char] = set()
                self.char_map[char].add(w)

    def make_move(self, current_word, word_history):
        """
        Determine the best move based on the current word and history.
        """
        current_word = current_word.lower()
        c1 = current_word[0]
        c2 = current_word[-1]
        prev_len = len(current_word)
        
        # 1. Try to find a Full Move (contains both c1 and c2)
        set1 = self.char_map.get(c1, set())
        set2 = self.char_map.get(c2, set())
        
        # Intersection of words containing c1 and words containing c2
        candidates = set1 & set2
        
        best_word = None
        best_score = float('-inf')
        
        for word in candidates:
            if word in word_history:
                continue
            
            meta = self.word_meta[word]
            w_len = meta['len']
            
            # Length Constraint
            if w_len == prev_len:
                continue
            
            # Position Constraint: c1/c2 cannot be at start/end of new word
            if word[0] in (c1, c2) or word[-1] in (c1, c2):
                continue
            
            # Calculate Score
            score = w_len
            if meta['hyphen']:
                score /= 2
            
            # Consecutive Letter Bonus
            if (c1 + c2 in word) or (c2 + c1 in word):
                score *= 2
            
            # Defensive Heuristic:
            # Add a small bonus based on the rarity of the new word's first/last letters.
            # This incentivizes leaving the opponent with difficult letters.
            rarity_bonus = 0
            if word[0] in self.letter_freq:
                rarity_bonus += (10000.0 / self.letter_freq[word[0]])
            if word[-1] in self.letter_freq:
                rarity_bonus += (10000.0 / self.letter_freq[word[-1]])
            
            score += (rarity_bonus / 10000.0)
            
            if score > best_score:
                best_score = score
                best_word = word
        
        if best_word:
            return best_word
            
        # 2. Fallback: Partial Move (contains only one of c1, c2)
        # Words with c1 but not c2
        p_set1 = set1 - set2
        # Words with c2 but not c1
        p_set2 = set2 - set1
        partial_candidates = p_set1 | p_set2
        
        best_partial = None
        min_len = float('inf')
        
        for word in partial_candidates:
            if word in word_history:
                continue
            
            meta = self.word_meta[word]
            w_len = meta['len']
            
            if w_len == prev_len:
                continue
            
            # Identify which letter we are using for the partial move
            has_c1 = c1 in word
            has_c2 = c2 in word
            target = c1 if has_c1 else c2
            
            # Position Constraint for the specific letter used
            if word[0] == target or word[-1] == target:
                continue
            
            # Strategy: Minimize penalty (shortest word)
            if w_len < min_len:
                min_len = w_len
                best_partial = word
                
        if best_partial:
            return best_partial
            
        # 3. Last Resort: No valid move found
        # Return any valid word not in history to avoid crashing/forfeit
        for word in self.dictionary:
            if word not in word_history:
                return word
        
        return "pass"
