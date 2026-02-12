"""
Agent Code: A4-WordFinder
Model: openai/gpt-oss-120b@preset/fp8
Run: 2
Generated: 2026-02-12 09:24:15
"""

import string

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        # Map each interior letter to the set of words that contain it (not at first or last position)
        self.letter_to_words = {ch: set() for ch in string.ascii_lowercase}
        for w in self.dictionary:
            if len(w) < 3:
                continue
            interior = w[1:-1]
            for ch in set(interior):
                if ch in self.letter_to_words:
                    self.letter_to_words[ch].add(w)
        # Keep a list for random fallback selections
        self.all_words = list(self.dictionary)

    def make_move(self, current_word, word_history):
        cur = current_word.lower()
        first = cur[0]
        last = cur[-1]
        cur_len = len(cur)

        # Full move candidates: words that have both required letters in interior positions
        set_first = self.letter_to_words.get(first, set())
        set_last = self.letter_to_words.get(last, set())
        candidates = set_first & set_last

        valid_full = []
        for w in candidates:
            if w in word_history:
                continue
            if len(w) == cur_len:
                continue
            if w[0] in (first, last) or w[-1] in (first, last):
                continue
            valid_full.append(w)

        if valid_full:
            best_score = -1
            best_words = []
            for w in valid_full:
                length = len(w)
                hyphen = '-' in w
                base = length // 2 if hyphen else length
                if (first + last) in w or (last + first) in w:
                    base *= 2
                if base > best_score:
                    best_score = base
                    best_words = [w]
                elif base == best_score:
                    best_words.append(w)
            return random.choice(best_words)

        # Partial move: one required letter interior, the other absent entirely
        partial_candidates = set()
        # Words containing 'first' but not 'last'
        for w in set_first:
            if w in word_history or len(w) == cur_len:
                continue
            if w[0] in (first, last) or w[-1] in (first, last):
                continue
            if last in w:
                continue
            partial_candidates.add(w)
        # Words containing 'last' but not 'first'
        for w in set_last:
            if w in word_history or len(w) == cur_len:
                continue
            if w[0] in (first, last) or w[-1] in (first, last):
                continue
            if first in w:
                continue
            partial_candidates.add(w)

        if partial_candidates:
            min_len = min(len(w) for w in partial_candidates)
            shortest = [w for w in partial_candidates if len(w) == min_len]
            return random.choice(shortest)

        # Fallback: any unused word respecting start/end and length constraint
        fallback = []
        for w in self.all_words:
            if w in word_history or len(w) == cur_len:
                continue
            if w[0] in (first, last) or w[-1] in (first, last):
                continue
            fallback.append(w)
        if fallback:
            return random.choice(fallback)

        # Last resort: any unused word
        remaining = [w for w in self.all_words if w not in word_history]
        if remaining:
            return random.choice(remaining)

        # Should never happen; return a minimal word
        return "a"
