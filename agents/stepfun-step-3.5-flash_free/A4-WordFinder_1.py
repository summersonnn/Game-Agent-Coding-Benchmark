"""
Agent Code: A4-WordFinder
Model: stepfun/step-3.5-flash:free
Run: 1
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.word_data = {}
        self.words_by_letter = defaultdict(set)
        self.words_by_first = defaultdict(set)
        self.words_by_last = defaultdict(set)
        
        # Precompute word metadata and indexes
        for word in self.dictionary:
            self.word_data[word] = (len(word), word[0], word[-1], set(word))
            for letter in set(word):
                self.words_by_letter[letter].add(word)
            self.words_by_first[word[0]].add(word)
            self.words_by_last[word[-1]].add(word)

    def has_consecutive(self, word, a, b):
        """Check if letters a and b appear consecutively in word (in either order)."""
        for i in range(len(word) - 1):
            if (word[i] == a and word[i+1] == b) or (word[i] == b and word[i+1] == a):
                return True
        return False

    def make_move(self, current_word, word_history):
        current_word = current_word.lower()
        req1 = current_word[0]
        req2 = current_word[-1]
        curr_len = len(current_word)

        # Step 1: Find valid words (contain both required letters, not at start/end, different length)
        candidate_valid = self.words_by_letter[req1] & self.words_by_letter[req2]
        candidate_valid = {
            word for word in candidate_valid 
            if self.word_data[word][0] != curr_len 
            and word[0] not in (req1, req2) 
            and word[-1] not in (req1, req2)
            and word not in word_history
        }

        if candidate_valid:
            best_word = None
            best_score = -float('inf')
            best_opponent_options = float('inf')
            
            for word in candidate_valid:
                # Calculate base points
                base = len(word)
                if '-' in word:
                    base = len(word) // 2
                if self.has_consecutive(word, req1, req2):
                    base *= 2
                
                # Estimate opponent's options (defensive metric)
                opp_req1, opp_req2 = word[0], word[-1]
                opp_candidates = self.words_by_letter[opp_req1] & self.words_by_letter[opp_req2]
                opp_candidates = {
                    w for w in opp_candidates 
                    if self.word_data[w][0] != len(word)
                    and w[0] not in (opp_req1, opp_req2)
                    and w[-1] not in (opp_req1, opp_req2)
                    and w not in word_history
                    and w != word
                }
                opp_count = len(opp_candidates)
                
                # Choose word with highest score, then fewest opponent options
                if base > best_score:
                    best_score = base
                    best_word = word
                    best_opponent_options = opp_count
                elif base == best_score and opp_count < best_opponent_options:
                    best_word = word
                    best_opponent_options = opp_count
            
            return best_word

        # Step 2: Partial move (only one required letter, not at start/end)
        candidate_partial = set()
        
        # Words containing req1 but not req2
        for word in self.words_by_letter[req1]:
            if (word in word_history or 
                len(word) == curr_len or 
                req2 in self.word_data[word][3] or 
                word[0] == req1 or word[-1] == req1):
                continue
            candidate_partial.add(word)
        
        # Words containing req2 but not req1
        for word in self.words_by_letter[req2]:
            if (word in word_history or 
                len(word) == curr_len or 
                req1 in self.word_data[word][3] or 
                word[0] == req2 or word[-1] == req2):
                continue
            candidate_partial.add(word)
        
        if candidate_partial:
            # Choose partial word with smallest penalty (shortest effective length)
            best_word = min(candidate_partial, 
                           key=lambda w: len(w) // 2 if '-' in w else len(w))
            return best_word

        # Step 3: Fallback - return any unused word with different length if possible
        for word in sorted(self.dictionary, key=lambda w: (len(w), w)):
            if word not in word_history and len(word) != curr_len:
                return word
        # If none with different length, return any unused word
        for word in self.dictionary:
            if word not in word_history:
                return word
        # Absolute fallback (should rarely happen)
        return current_word
