"""
Agent Code: A4-WordFinder
Model: xiaomi/mimo-v2-flash
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # Returns a set of lowercase words
        self.words_by_letter = defaultdict(set)
        self.letter_presence = defaultdict(int)
        self.pair_presence = defaultdict(int)
        
        # Precompute mappings for efficient lookups
        for word in self.dictionary:
            letters = set(word)
            for letter in letters:
                self.words_by_letter[letter].add(word)
                self.letter_presence[letter] += 1
            # Precompute distinct unordered pairs for difficulty estimation
            letters_list = sorted(letters)
            n = len(letters_list)
            for i in range(n):
                for j in range(i+1, n):
                    a = letters_list[i]
                    b = letters_list[j]
                    self.pair_presence[(a, b)] += 1

    def make_move(self, current_word, word_history):
        X = current_word[0]
        Y = current_word[-1]
        
        # Step 1: Find full moves (contain both X and Y, not at start/end, different length, not used)
        full_candidates = []
        if X in self.words_by_letter and Y in self.words_by_letter:
            candidate_words = self.words_by_letter[X] & self.words_by_letter[Y]
            for word in candidate_words:
                if word in word_history:
                    continue
                if len(word) == len(current_word):
                    continue
                if word[0] in (X, Y) or word[-1] in (X, Y):
                    continue
                
                # Check consecutive bonus
                if X == Y:
                    has_consecutive = (X*2 in word)
                else:
                    has_consecutive = (X+Y in word) or (Y+X in word)
                
                base = len(word)
                if '-' in word:
                    base //= 2
                if has_consecutive:
                    base *= 2
                
                # Compute difficulty for opponent
                if X == Y:
                    difficulty = self.letter_presence[X]
                else:
                    a, b = (X, Y) if X < Y else (Y, X)
                    difficulty = self.pair_presence.get((a, b), 0)
                
                full_candidates.append((word, base, difficulty))
        
        if full_candidates:
            # Sort by score descending, then by difficulty ascending (lower difficulty is harder for opponent)
            full_candidates.sort(key=lambda x: (-x[1], x[2]))
            return full_candidates[0][0]
        
        # Step 2: Partial move (only if X != Y)
        partial_candidates = []
        if X != Y:
            # Try words with X but not Y
            if X in self.words_by_letter:
                for word in self.words_by_letter[X]:
                    if word in word_history:
                        continue
                    if len(word) == len(current_word):
                        continue
                    if word[0] == X or word[-1] == X:
                        continue
                    if Y in word:
                        continue
                    base = len(word)
                    if '-' in word:
                        base //= 2
                    penalty = -base
                    # Compute difficulty for opponent
                    a, b = word[0], word[-1]
                    if a == b:
                        difficulty = self.letter_presence[a]
                    else:
                        if a > b:
                            a, b = b, a
                        difficulty = self.pair_presence.get((a, b), 0)
                    partial_candidates.append((word, penalty, difficulty))
            
            # Try words with Y but not X
            if Y in self.words_by_letter:
                for word in self.words_by_letter[Y]:
                    if word in word_history:
                        continue
                    if len(word) == len(current_word):
                        continue
                    if word[0] == Y or word[-1] == Y:
                        continue
                    if X in word:
                        continue
                    base = len(word)
                    if '-' in word:
                        base //= 2
                    penalty = -base
                    a, b = word[0], word[-1]
                    if a == b:
                        difficulty = self.letter_presence[a]
                    else:
                        if a > b:
                            a, b = b, a
                        difficulty = self.pair_presence.get((a, b), 0)
                    partial_candidates.append((word, penalty, difficulty))
        
        if partial_candidates:
            # Sort by penalty descending (least negative first), then difficulty ascending
            partial_candidates.sort(key=lambda x: (-x[1], x[2]))
            return partial_candidates[0][0]
        
        # Step 3: Fallback - any unused word with different length (will be invalid but avoids crash)
        for word in self.dictionary:
            if word not in word_history and len(word) != len(current_word):
                return word
        
        # Last resort: return any unused word (even same length, will be invalid)
        for word in self.dictionary:
            if word not in word_history:
                return word
        
        # If all words used, return "a" (should not happen in practice)
        return "a"
