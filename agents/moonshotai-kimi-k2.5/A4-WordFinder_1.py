"""
Agent Code: A4-WordFinder
Model: moonshotai/kimi-k2.5
Run: 1
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.words_by_internal_letter = defaultdict(set)
        self.word_data = {}
        
        # Letter rarity scores for defensive play (higher = rarer/harder for opponent)
        self.rarity = {
            'e': 1, 't': 2, 'a': 3, 'o': 4, 'i': 5, 'n': 6, 's': 7, 'h': 8, 'r': 9,
            'd': 10, 'l': 11, 'u': 12, 'c': 13, 'm': 14, 'w': 15, 'f': 16, 'g': 17,
            'y': 18, 'p': 19, 'b': 20, 'v': 21, 'k': 22, 'j': 23, 'x': 24, 'q': 25, 'z': 26
        }
        
        # Preprocess dictionary
        for word in self.dictionary:
            if len(word) < 3:
                continue
            
            length = len(word)
            has_hyphen = '-' in word
            base_score = length / 2 if has_hyphen else length
            
            # Characters at positions 1 to len-2 (internal positions)
            internal_chars = set(word[1:-1])
            
            # Consecutive pairs where both characters are internal (positions 1..len-2)
            internal_pairs = set()
            for i in range(1, length - 2):
                internal_pairs.add((word[i], word[i+1]))
            
            self.word_data[word] = {
                'length': length,
                'base_score': base_score,
                'internal_chars': internal_chars,
                'internal_pairs': internal_pairs,
                'first': word[0],
                'last': word[-1]
            }
            
            for char in internal_chars:
                self.words_by_internal_letter[char].add(word)
    
    def make_move(self, current_word, word_history):
        first_req = current_word[0].lower()
        last_req = current_word[-1].lower()
        prev_len = len(current_word)
        
        # Find words containing both required letters internally
        candidates = self.words_by_internal_letter[first_req] & self.words_by_internal_letter[last_req]
        
        best_word = None
        best_score = float('-inf')
        
        for word in candidates:
            if word in word_history:
                continue
            
            data = self.word_data[word]
            
            # Length constraint
            if data['length'] == prev_len:
                continue
            
            # Position constraint: required letters cannot be at start or end of new word
            if data['first'] in (first_req, last_req) or data['last'] in (first_req, last_req):
                continue
            
            # Calculate points
            points = data['base_score']
            
            # Consecutive letter bonus (2x multiplier)
            if (first_req, last_req) in data['internal_pairs'] or (last_req, first_req) in data['internal_pairs']:
                points *= 2
            
            # Defensive bonus: prefer leaving opponent with rare letters
            defense = self.rarity.get(data['first'], 0) + self.rarity.get(data['last'], 0)
            total_score = points + defense * 0.1
            
            if total_score > best_score:
                best_score = total_score
                best_word = word
        
        if best_word:
            return best_word
        
        # Partial move fallback: word with only ONE required letter
        best_partial = None
        best_partial_score = float('-inf')  # Higher is better (less negative)
        
        # Candidates with first_req but not last_req
        candidates_first = self.words_by_internal_letter[first_req] - self.words_by_internal_letter[last_req]
        for word in candidates_first:
            if word in word_history:
                continue
            data = self.word_data[word]
            if data['length'] == prev_len:
                continue
            # Check the one required letter is not at start or end
            if data['first'] == first_req or data['last'] == first_req:
                continue
            
            score = -data['base_score']  # Negative points for partial move
            if score > best_partial_score:
                best_partial_score = score
                best_partial = word
        
        # Candidates with last_req but not first_req
        candidates_last = self.words_by_internal_letter[last_req] - self.words_by_internal_letter[first_req]
        for word in candidates_last:
            if word in word_history:
                continue
            data = self.word_data[word]
            if data['length'] == prev_len:
                continue
            if data['first'] == last_req or data['last'] == last_req:
                continue
            
            score = -data['base_score']
            if score > best_partial_score:
                best_partial_score = score
                best_partial = word
        
        if best_partial:
            return best_partial
        
        # Last resort: return any valid dictionary word not in history with different length
        # This will likely be an invalid move but prevents crashing
        for word in self.dictionary:
            if word not in word_history and len(word) != prev_len:
                return word
        
        return "error"
