"""
Agent Code: A4-WordFinder
Model: anthropic-claude-opus-4.6
Run: 1
Generated: 2026-02-12 09:24:15
"""


import random


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()

        self.word_info = {}
        self.by_letter = {}

        for word in self.dictionary:
            if '-' in word or len(word) < 3:
                continue
            wlen = len(word)
            fc = word[0]
            lc = word[-1]
            valid_chars = set(word[1:-1]) - {fc, lc}
            if not valid_chars:
                continue
            self.word_info[word] = (wlen, valid_chars, fc, lc)
            for c in valid_chars:
                if c not in self.by_letter:
                    self.by_letter[c] = []
                self.by_letter[c].append(word)

        # Precompute candidate counts per pair for difficulty scoring
        self.pair_count = {}
        all_chars = list(self.by_letter.keys())
        for i, c1 in enumerate(all_chars):
            s1 = set(self.by_letter[c1])
            for c2 in all_chars[i:]:
                s2 = set(self.by_letter[c2])
                count = len(s1 & s2)
                self.pair_count[(c1, c2)] = count
                self.pair_count[(c2, c1)] = count

        # Build candidate lists sorted by: score desc, then difficulty for opponent (fewer options = harder)
        self.candidates = {}
        for i, c1 in enumerate(all_chars):
            s1 = set(self.by_letter[c1])
            for c2 in all_chars[i:]:
                s2 = set(self.by_letter[c2])
                both = s1 & s2
                if not both:
                    continue
                scored = []
                for w in both:
                    wlen, _, fc, lc = self.word_info[w]
                    consec = (c1 + c2) in w or (c2 + c1) in w
                    score = wlen * 2 if consec else wlen
                    difficulty = self.pair_count.get((fc, lc), 0)
                    scored.append((score, difficulty, wlen, w))
                # Sort: highest score first, then fewest opponent options (hardest)
                scored.sort(key=lambda x: (-x[0], x[1]))
                result = [(s, wl, w) for s, d, wl, w in scored]
                self.candidates[(c1, c2)] = result
                if c1 != c2:
                    self.candidates[(c2, c1)] = result

        self.partial = {}
        for c, words in self.by_letter.items():
            self.partial[c] = sorted(
                [(self.word_info[w][0], w) for w in words],
                key=lambda x: -x[0]
            )

    def make_move(self, current_word, word_history):
        cw = current_word.lower()
        c1 = cw[0]
        c2 = cw[-1]
        cw_len = len(cw)

        for score, wlen, word in self.candidates.get((c1, c2), []):
            if wlen != cw_len and word not in word_history:
                return word

        for c in (c1, c2):
            for wlen, word in self.partial.get(c, []):
                if wlen != cw_len and word not in word_history:
                    return word

        return random.choice(list(self.dictionary - word_history))