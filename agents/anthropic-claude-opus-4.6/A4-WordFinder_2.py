"""
Agent Code: A4-WordFinder
Model: anthropic-claude-opus-4.6
Run: 2
Generated: 2026-02-12 09:24:15
"""


from collections import defaultdict


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()

        # pair_index[(c1,c2)] = sorted list of (score, word) for words containing
        # both c1 and c2 in interior. For c1==c2, just needs one occurrence.
        self.pair_index = defaultdict(list)
        # single_index[c] = words with c in interior, sorted by length desc
        self.single_index = defaultdict(list)

        for word in self.dictionary:
            wlen = len(word)
            if wlen < 3:
                continue

            inner = word[1:-1]
            inner_chars = set(inner)
            has_hyphen = '-' in word
            base = wlen // 2 if has_hyphen else wlen
            w0 = word[0]
            wn = word[-1]

            consec = set()
            for i in range(len(inner) - 1):
                a, b = inner[i], inner[i + 1]
                consec.add((min(a, b), max(a, b)))
                if a == b:
                    consec.add((a, a))

            chars_list = sorted(inner_chars)
            for i, c1 in enumerate(chars_list):
                for c2 in chars_list[i:]:
                    if w0 in (c1, c2) or wn in (c1, c2):
                        continue
                    key = (c1, c2)
                    is_consec = key in consec
                    score = base * 2 if is_consec else base
                    self.pair_index[key].append((score, word))

            for c in inner_chars:
                if w0 != c and wn != c:
                    self.single_index[c].append(word)

        # Sort: primary by score desc, secondary by opponent difficulty (fewer options = harder)
        for key in self.pair_index:
            for i, (score, word) in enumerate(self.pair_index[key]):
                opp_key = (min(word[0], word[-1]), max(word[0], word[-1]))
                opp_options = len(self.pair_index.get(opp_key, []))
                self.pair_index[key][i] = (score, opp_options, word)
            self.pair_index[key].sort(key=lambda x: (-x[0], x[1]))

        for key in self.single_index:
            self.single_index[key].sort(reverse=True, key=lambda x: len(x))

    def make_move(self, current_word, word_history):
        first = current_word[0].lower()
        last = current_word[-1].lower()
        cur_len = len(current_word)

        key = (min(first, last), max(first, last))
        for score, _, word in self.pair_index.get(key, []):
            if len(word) != cur_len and word not in word_history:
                return word

        # Partial move fallback
        for c in (first, last):
            for word in self.single_index.get(c, []):
                if len(word) != cur_len and word not in word_history:
                    return word

        return "fallback"