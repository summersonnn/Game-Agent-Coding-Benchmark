"""
Agent Code: A4-WordFinder
Model: z-ai/glm-5@preset/fp8
Run: 1
Generated: 2026-02-12 09:24:15
"""



class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        self.word_data = {}  # word -> (length, middle_letters, consecutive_pairs, has_hyphen)
        self.words_by_pair = {}  # (letter1, letter2) -> [(score, word), ...]
        self.words_by_single = {}  # letter -> [(length, word), ...]
        
        for word in self.dictionary:
            word_lower = word.lower()
            length = len(word_lower)
            
            if length < 3:
                continue
            
            middle = word_lower[1:-1]
            middle_letters = set(middle)
            
            # Find consecutive pairs in middle
            consecutive_pairs = set()
            for i in range(len(middle) - 1):
                pair = tuple(sorted([middle[i], middle[i+1]]))
                consecutive_pairs.add(pair)
            
            has_hyphen = '-' in word_lower
            self.word_data[word_lower] = (length, middle_letters, consecutive_pairs, has_hyphen)
            
            # Index by letter pair with pre-computed score
            for l1 in middle_letters:
                for l2 in middle_letters:
                    if l1 <= l2:
                        key = (l1, l2)
                        if key not in self.words_by_pair:
                            self.words_by_pair[key] = []
                        
                        has_consecutive = key in consecutive_pairs
                        score = length
                        if has_hyphen:
                            score = length // 2
                        if has_consecutive:
                            score *= 2
                        
                        self.words_by_pair[key].append((score, word_lower))
            
            # Index by single letter for partial moves
            for letter in middle_letters:
                if letter not in self.words_by_single:
                    self.words_by_single[letter] = []
                self.words_by_single[letter].append((length, word_lower))
        
        # Sort by score descending (best first)
        for key in self.words_by_pair:
            self.words_by_pair[key].sort(reverse=True)
        
        # Sort by length ascending (shorter = less penalty for partial)
        for key in self.words_by_single:
            self.words_by_single[key].sort()
    
    def make_move(self, current_word, word_history):
        current_word = current_word.lower()
        required_first = current_word[0]
        required_last = current_word[-1]
        prev_length = len(current_word)
        
        key = tuple(sorted([required_first, required_last]))
        
        # Find best valid word with both required letters
        if key in self.words_by_pair:
            for score, word in self.words_by_pair[key]:
                if word in word_history:
                    continue
                
                length = self.word_data[word][0]
                if length == prev_length:
                    continue
                
                return word
        
        # Partial move fallback
        return self._partial_move(required_first, required_last, word_history, prev_length)
    
    def _partial_move(self, required_first, required_last, word_history, prev_length):
        best_word = None
        best_length = float('inf')
        
        for letter in [required_first, required_last]:
            if letter not in self.words_by_single:
                continue
            for length, word in self.words_by_single[letter]:
                if word in word_history:
                    continue
                if length == prev_length:
                    continue
                # Shorter = less negative penalty
                if length < best_length:
                    best_length = length
                    best_word = word
        
        if best_word:
            return best_word
        
        # Absolute fallback
        for word in self.dictionary:
            word_lower = word.lower()
            if word_lower not in word_history:
                return word_lower
        
        return list(self.dictionary)[0]
