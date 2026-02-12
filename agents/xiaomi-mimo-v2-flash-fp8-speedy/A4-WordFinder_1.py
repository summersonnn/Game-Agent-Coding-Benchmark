"""
Agent Code: A4-WordFinder
Model: xiaomi/mimo-v2-flash
Run: 1
Generated: 2026-02-12 09:24:15
"""



class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.letter_words = {}
        self.interior_letter_words = {}
        self._precompute()
    
    def _precompute(self):
        for word in self.dictionary:
            n = len(word)
            if n < 3:
                continue
            for letter in set(word):
                if letter not in self.letter_words:
                    self.letter_words[letter] = set()
                self.letter_words[letter].add(word)
            interior_str = word[1:-1]
            for letter in set(interior_str):
                if letter not in self.interior_letter_words:
                    self.interior_letter_words[letter] = set()
                self.interior_letter_words[letter].add(word)
    
    def make_move(self, current_word, word_history):
        a = current_word[0]
        b = current_word[-1]
        
        candidates_full = []
        if a in self.interior_letter_words and b in self.interior_letter_words:
            candidate_set = self.interior_letter_words[a] & self.interior_letter_words[b]
            for word in candidate_set:
                if word in word_history:
                    continue
                if len(word) == len(current_word):
                    continue
                if word[0] in (a, b) or word[-1] in (a, b):
                    continue
                base = len(word)
                if '-' in word:
                    base //= 2
                consecutive = False
                for i in range(len(word) - 1):
                    if (word[i] == a and word[i+1] == b) or (word[i] == b and word[i+1] == a):
                        consecutive = True
                        break
                if consecutive:
                    base *= 2
                candidates_full.append((word, base))
        
        if candidates_full:
            candidates_full.sort(key=lambda x: x[1], reverse=True)
            return candidates_full[0][0]
        
        candidates_partial = []
        for (letter, other) in [(a, b), (b, a)]:
            if letter not in self.interior_letter_words:
                continue
            candidate_set = self.interior_letter_words[letter]
            if other in self.letter_words:
                candidate_set = candidate_set - self.letter_words[other]
            for word in candidate_set:
                if word in word_history:
                    continue
                if len(word) == len(current_word):
                    continue
                if word[0] == letter or word[-1] == letter:
                    continue
                base = len(word)
                if '-' in word:
                    base //= 2
                candidates_partial.append((word, base))
        
        if candidates_partial:
            candidates_partial.sort(key=lambda x: x[1])
            return candidates_partial[0][0]
        
        for word in self.dictionary:
            if word in word_history:
                continue
            if len(word) == len(current_word):
                continue
            return word
        
        return "a"
