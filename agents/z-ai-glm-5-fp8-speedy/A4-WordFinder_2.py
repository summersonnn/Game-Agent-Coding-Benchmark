"""
Agent Code: A4-WordFinder
Model: z-ai/glm-5@preset/fp8
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # word_info: word -> (length, internal_letters_set, consecutive_pairs_set, has_hyphen)
        self.word_info = {}
        
        # letter_pair_to_words: (letter1, letter2) sorted -> [word1, word2, ...]
        self.letter_pair_to_words = defaultdict(list)
        
        # Difficulty scores for letters (higher = harder for opponent)
        self.difficulty_scores = {
            'q': 10, 'z': 10, 'j': 9, 'x': 9, 'v': 8, 'k': 8,
            'b': 5, 'w': 5, 'f': 5, 'g': 5, 'y': 5, 'p': 5,
            'm': 3, 'c': 3, 'u': 3, 'd': 3, 'l': 3,
            'n': 1, 'r': 1, 'h': 1, 's': 1, 'i': 1, 'o': 1, 'a': 1, 't': 1, 'e': 1
        }
        
        for word in self.dictionary:
            w = word.lower()
            length = len(w)
            
            if length < 3:
                continue
            
            has_hyphen = '-' in w
            
            # Count internal letters (positions 1 to length-2)
            internal_letter_counts = defaultdict(int)
            for i in range(1, length - 1):
                internal_letter_counts[w[i]] += 1
            
            internal_letters = set(internal_letter_counts.keys())
            
            # Consecutive pairs (within internal portion)
            consecutive_pairs = set()
            for i in range(1, length - 2):
                pair = (w[i], w[i + 1])
                consecutive_pairs.add(pair)
                consecutive_pairs.add((pair[1], pair[0]))
            
            self.word_info[w] = (length, internal_letters, consecutive_pairs, has_hyphen)
            
            # Index by internal letter pairs
            sorted_letters = sorted(internal_letters)
            for i in range(len(sorted_letters)):
                for j in range(i, len(sorted_letters)):
                    l1, l2 = sorted_letters[i], sorted_letters[j]
                    if l1 == l2:
                        if internal_letter_counts[l1] >= 2:
                            self.letter_pair_to_words[(l1, l2)].append(w)
                    else:
                        self.letter_pair_to_words[(l1, l2)].append(w)
    
    def make_move(self, current_word, word_history):
        prev_word = current_word.lower()
        required1 = prev_word[0]
        required2 = prev_word[-1]
        prev_length = len(prev_word)
        
        # Get candidate words for the required letter pair
        pair = tuple(sorted([required1, required2]))
        candidates = self.letter_pair_to_words.get(pair, [])
        
        best_word = None
        best_score = float('-inf')
        
        for word in candidates:
            if word in word_history:
                continue
            
            info = self.word_info.get(word)
            if info is None:
                continue
            
            length, internal_letters, consecutive_pairs, has_hyphen = info
            
            if length == prev_length:
                continue
            
            # Check that required letters are not at start or end
            if word[0] in (required1, required2) or word[-1] in (required1, required2):
                continue
            
            # Calculate score
            score = length
            if has_hyphen:
                score = score // 2
            
            # Check consecutive bonus
            if (required1, required2) in consecutive_pairs:
                score *= 2
            
            # Add difficulty bonus (tiebreaker for defensive play)
            difficulty_bonus = (self.difficulty_scores.get(word[-1], 0) + 
                                self.difficulty_scores.get(word[0], 0) * 0.5)
            score += difficulty_bonus * 0.1
            
            if score > best_score:
                best_score = score
                best_word = word
        
        if best_word:
            return best_word
        
        # Fallback: partial move (one required letter only)
        best_partial = None
        best_partial_score = float('-inf')
        
        for word, info in self.word_info.items():
            if word in word_history:
                continue
            
            length, internal_letters, _, has_hyphen = info
            
            # Check positions of required letters
            required1_internal = required1 in internal_letters
            required2_internal = required2 in internal_letters
            required1_at_start = word[0] == required1
            required1_at_end = word[-1] == required1
            required2_at_start = word[0] == required2
            required2_at_end = word[-1] == required2
            
            required1_in_word = required1_internal or required1_at_start or required1_at_end
            required2_in_word = required2_internal or required2_at_start or required2_at_end
            
            # Partial move: exactly one letter in word, and it's internal
            if required1_internal and not required2_in_word:
                score = -length
                if has_hyphen:
                    score = score // 2
                if score > best_partial_score:
                    best_partial_score = score
                    best_partial = word
            elif required2_internal and not required1_in_word:
                score = -length
                if has_hyphen:
                    score = score // 2
                if score > best_partial_score:
                    best_partial_score = score
                    best_partial = word
        
        if best_partial:
            return best_partial
        
        # Absolute fallback: return any valid word
        for word in self.dictionary:
            w = word.lower()
            if w not in word_history and len(w) >= 3:
                return w
        
        return None