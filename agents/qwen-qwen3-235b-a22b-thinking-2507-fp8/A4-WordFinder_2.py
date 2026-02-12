"""
Agent Code: A4-WordFinder
Model: qwen/qwen3-235b-a22b-thinking-2507@preset/fp8
Run: 2
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        self.by_letter = defaultdict(list)
        self.word_letters = {}
        for word in self.dictionary:
            self.word_letters[word] = set(word)
            n = len(word)
            if n > 2:
                middle = word[1:-1]
                for char in set(middle):
                    self.by_letter[char].append(word)

    def make_move(self, current_word, word_history):
        first_char = current_word[0]
        last_char = current_word[-1]
        current_len = len(current_word)
        
        # Full move candidates: must contain both letters in the middle
        list1 = self.by_letter.get(first_char, [])
        list2 = self.by_letter.get(last_char, [])
        candidate_set = set()
        if list1 and list2:
            set1 = set(list1)
            set2 = set(list2)
            candidate_set = set1 & set2
        
        full_candidates = []
        for word in candidate_set:
            if word in word_history or len(word) == current_len:
                continue
            base = len(word)
            if '-' in word:
                base = base // 2
            if first_char == last_char:
                if (first_char * 2) in word:
                    base *= 2
            else:
                if (first_char + last_char in word) or (last_char + first_char in word):
                    base *= 2
            full_candidates.append((base, word))
        
        if full_candidates:
            full_candidates.sort(key=lambda x: x[0], reverse=True)
            return full_candidates[0][1]
        
        # Partial move candidates: contain exactly one required letter (in the middle) and not the other
        partial_candidates = []
        # For first_char as the single required letter
        list1 = self.by_letter.get(first_char, [])
        for word in list1:
            if word in word_history or len(word) == current_len:
                continue
            if last_char in self.word_letters[word]:
                continue
            partial_candidates.append((len(word), word))
        
        # For last_char as the single required letter
        list2 = self.by_letter.get(last_char, [])
        for word in list2:
            if word in word_history or len(word) == current_len:
                continue
            if first_char in self.word_letters[word]:
                continue
            partial_candidates.append((len(word), word))
        
        if partial_candidates:
            partial_candidates.sort(key=lambda x: x[0])
            return partial_candidates[0][1]
        
        # Fallback: return any word not in history (will be invalid but avoids crash)
        for word in self.dictionary:
            if word not in word_history:
                return word
        return "a"  # extremely rare case: dictionary exhausted
