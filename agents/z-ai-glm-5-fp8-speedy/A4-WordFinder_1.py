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
        
        # Pre-compute: for each pair of letters, store words containing both
        self.words_by_pair = {}
        for word in self.dictionary:
            chars = set(word)
            for c1 in chars:
                for c2 in chars:
                    pair = (c1, c2)
                    if pair not in self.words_by_pair:
                        self.words_by_pair[pair] = set()
                    self.words_by_pair[pair].add(word)
        
        # Pre-compute: for each single letter, store words containing it
        self.words_by_letter = {}
        for word in self.dictionary:
            for c in set(word):
                if c not in self.words_by_letter:
                    self.words_by_letter[c] = set()
                self.words_by_letter[c].add(word)
        
        # Letter frequency for strategic scoring (lower = harder for opponent)
        self.letter_freq = {
            'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0,
            'n': 6.7, 's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3,
            'l': 4.0, 'c': 2.8, 'u': 2.8, 'm': 2.4, 'w': 2.4,
            'f': 2.2, 'g': 2.0, 'y': 2.0, 'p': 1.9, 'b': 1.5,
            'v': 1.0, 'k': 0.8, 'j': 0.15, 'x': 0.15, 'q': 0.10, 'z': 0.07
        }
    
    def calculate_score(self, word, first_char, last_char):
        base = len(word)
        if '-' in word:
            base = base // 2
        has_bonus = (first_char + last_char in word) or (last_char + first_char in word)
        if has_bonus:
            base *= 2
        return base
    
    def make_move(self, current_word, word_history):
        current_word = current_word.lower()
        first_char = current_word[0]
        last_char = current_word[-1]
        current_len = len(current_word)
        
        # Get candidates containing both required letters
        pair = (first_char, last_char)
        candidates = self.words_by_pair.get(pair, set())
        
        # Filter and score valid words
        valid_words = []
        for word in candidates:
            if word in word_history:
                continue
            if len(word) == current_len:
                continue
            if first_char not in word or last_char not in word:
                continue
            if word[0] == first_char or word[0] == last_char:
                continue
            if word[-1] == first_char or word[-1] == last_char:
                continue
            
            score = self.calculate_score(word, first_char, last_char)
            
            # Strategic scoring: prioritize leaving difficult letters for opponent
            my_first, my_last = word[0], word[-1]
            opponent_difficulty = (12.7 - self.letter_freq.get(my_first, 1)) + \
                                  (12.7 - self.letter_freq.get(my_last, 1))
            
            total = score * 10 + opponent_difficulty
            valid_words.append((word, total))
        
        if valid_words:
            valid_words.sort(key=lambda x: x[1], reverse=True)
            return valid_words[0][0]
        
        # Partial move: word with exactly one required letter
        partial_words = []
        
        if first_char in self.words_by_letter:
            for word in self.words_by_letter[first_char]:
                if word in word_history or len(word) == current_len:
                    continue
                if last_char in word or word[0] == first_char or word[-1] == first_char:
                    continue
                partial_words.append(word)
        
        if first_char != last_char and last_char in self.words_by_letter:
            for word in self.words_by_letter[last_char]:
                if word in word_history or len(word) == current_len:
                    continue
                if first_char in word or word[0] == last_char or word[-1] == last_char:
                    continue
                partial_words.append(word)
        
        if partial_words:
            return min(partial_words, key=len)
        
        # Fallback: any valid word
        for word in self.dictionary:
            if word not in word_history and len(word) != current_len:
                return word
        
        return None