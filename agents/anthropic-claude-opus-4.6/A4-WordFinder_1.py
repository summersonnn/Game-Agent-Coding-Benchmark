"""
Agent Code: A4-WordFinder
Model: anthropic-claude-opus-4.6
Run: 1
Generated: 2026-02-12 09:24:15
"""


from collections import defaultdict


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()

        # Count how many words each (c1,c2) pair can reach - fewer = harder for opponent
        pair_count = defaultdict(int)
        self.pair_index = defaultdict(list)
        self.char_index = defaultdict(list)

        word_data = []
        for word in self.dictionary:
            if len(word) < 3:
                continue
            inner = word[1:-1]
            if not inner:
                continue
            inner_chars = set(inner) - {'-'}
            has_hyphen = '-' in word
            wlen = len(word)
            base = wlen // 2 if has_hyphen else wlen
            fc, lc = word[0], word[-1]
            pair_count[(fc, lc)] += 1
            word_data.append((word, inner, inner_chars, has_hyphen, wlen, base, fc, lc))

        for word, inner, inner_chars, has_hyphen, wlen, base, fc, lc in word_data:
            # Difficulty: fewer options for opponent = better for us
            opponent_options = pair_count.get((fc, lc), 0)

            for c in inner_chars:
                self.char_index[c].append((wlen, word))

            chars_list = sorted(inner_chars)
            for i, a in enumerate(chars_list):
                for b in chars_list[i:]:
                    if a == b and inner.count(a) < 2:
                        continue
                    has_bonus = (a + b in inner) or (b + a in inner)
                    score = base * 2 if has_bonus else base
                    # Sort: score desc, opponent difficulty asc (fewer options = harder)
                    entry = (score, -opponent_options, wlen, word)
                    self.pair_index[(a, b)].append(entry)
                    if a != b:
                        self.pair_index[(b, a)].append(entry)

        for key in self.pair_index:
            self.pair_index[key].sort(reverse=True)
        for key in self.char_index:
            self.char_index[key].sort(reverse=True)

    def make_move(self, current_word, word_history):
        c1 = current_word[0].lower()
        c2 = current_word[-1].lower()
        cur_len = len(current_word)

        candidates = self.pair_index.get((c1, c2), [])
        for score, neg_opp, wlen, word in candidates:
            if wlen == cur_len:
                continue
            if word in word_history:
                continue
            return word

        best = None
        for char in set([c1, c2]):
            for wlen, word in self.char_index.get(char, []):
                if wlen == cur_len:
                    continue
                if word in word_history:
                    continue
                fc, lc = word[0], word[-1]
                if fc in (c1, c2) or lc in (c1, c2):
                    continue
                best = word
                break
            if best:
                break

        if best:
            return best

        for word in self.dictionary:
            if len(word) != cur_len and word not in word_history:
                return word

        return "fallback"