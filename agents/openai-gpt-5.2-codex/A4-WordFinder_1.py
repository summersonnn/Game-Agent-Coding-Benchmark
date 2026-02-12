"""
Agent Code: A4-WordFinder
Model: openai/gpt-5.2-codex
Run: 1
Generated: 2026-02-12 09:30:10
"""



class WordFinderAgent:
    """
    WordFinder Agent
    """

    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()

        # Core word data
        self.word_list = []
        self.word_len = []
        self.word_base = []
        self.word_full_mask = []
        self.word_bigram_mask = []
        self.word_pair_key = []

        # Lookup structures
        self.pair_to_words = [[] for _ in range(26 * 26)]
        self.single_to_words = [[] for _ in range(26)]

        for w in self.dictionary:
            if not w:
                continue
            w = w.lower()
            length = len(w)

            f = ord(w[0]) - 97
            l = ord(w[-1]) - 97
            if not (0 <= f < 26 and 0 <= l < 26):
                continue  # skip non-letter boundaries

            full_mask = 0
            internal_mask = 0

            for i, ch in enumerate(w):
                o = ord(ch) - 97
                if 0 <= o < 26:
                    full_mask |= 1 << o
                    if 0 < i < length - 1:
                        internal_mask |= 1 << o

            bigram_mask = 0
            for i in range(length - 1):
                o1 = ord(w[i]) - 97
                o2 = ord(w[i + 1]) - 97
                if 0 <= o1 < 26 and 0 <= o2 < 26:
                    bigram_mask |= 1 << (o1 * 26 + o2)

            base = length // 2 if "-" in w else length

            idx = len(self.word_list)
            self.word_list.append(w)
            self.word_len.append(length)
            self.word_base.append(base)
            self.word_full_mask.append(full_mask)
            self.word_bigram_mask.append(bigram_mask)

            pair_key = f * 26 + l if f <= l else l * 26 + f
            self.word_pair_key.append(pair_key)

            if internal_mask:
                # extract internal letter indices (sorted)
                internal_indices = []
                mask = internal_mask
                while mask:
                    lsb = mask & -mask
                    internal_indices.append(lsb.bit_length() - 1)
                    mask -= lsb

                # single-letter lists
                for li in internal_indices:
                    if li != f and li != l:
                        self.single_to_words[li].append(idx)

                # pair lists
                n = len(internal_indices)
                for a in range(n):
                    i_letter = internal_indices[a]
                    if i_letter == f or i_letter == l:
                        continue
                    self.pair_to_words[i_letter * 26 + i_letter].append(idx)
                    for b in range(a + 1, n):
                        j_letter = internal_indices[b]
                        if j_letter == f or j_letter == l:
                            continue
                        self.pair_to_words[i_letter * 26 + j_letter].append(idx)

        # Sort lists for efficient search
        base_scores = self.word_base
        for lst in self.pair_to_words:
            lst.sort(key=base_scores.__getitem__, reverse=True)
        for lst in self.single_to_words:
            lst.sort(key=base_scores.__getitem__)

        self.pair_counts = [len(lst) for lst in self.pair_to_words]

        # Fallback list
        self.fallback_list = self.word_list.copy()
        random.shuffle(self.fallback_list)

    def make_move(self, current_word, word_history):
        if not current_word:
            return self._fallback(word_history)

        cw = current_word.strip().lower()
        if not cw:
            return self._fallback(word_history)

        i1 = ord(cw[0]) - 97
        i2 = ord(cw[-1]) - 97
        if not (0 <= i1 < 26 and 0 <= i2 < 26):
            return self._fallback(word_history)

        key = i1 * 26 + i2 if i1 <= i2 else i2 * 26 + i1
        current_len = len(cw)

        # Try full valid move
        word = self._find_full(key, i1, i2, current_len, word_history)
        if word:
            return word

        # Try partial move
        word = self._find_partial(i1, i2, current_len, word_history)
        if word:
            return word

        # Last resort
        return self._fallback(word_history)

    def _find_full(self, key, i1, i2, current_len, word_history):
        candidates = self.pair_to_words[key]
        if not candidates:
            return None

        bits = (1 << (i1 * 26 + i2)) | (1 << (i2 * 26 + i1))
        word_list = self.word_list
        word_base = self.word_base
        word_len = self.word_len
        bigrams = self.word_bigram_mask
        pair_counts = self.pair_counts
        pair_keys = self.word_pair_key
        used = word_history

        best_word = None
        best_score = -1
        best_diff = None
        found = False

        for idx in candidates:
            base = word_base[idx]
            if found and base * 2 < best_score:
                break

            w = word_list[idx]
            if w in used:
                continue
            if word_len[idx] == current_len:
                continue

            score = base * 2 if (bigrams[idx] & bits) else base

            if not found or score > best_score:
                best_word = w
                best_score = score
                best_diff = pair_counts[pair_keys[idx]]
                found = True
            elif score == best_score:
                diff = pair_counts[pair_keys[idx]]
                if diff < best_diff:
                    best_word = w
                    best_diff = diff

        return best_word

    def _find_partial(self, i1, i2, current_len, word_history):
        best_word = None
        best_base = None
        best_diff = None

        letter_indices = [i1] if i1 == i2 else [i1, i2]

        word_list = self.word_list
        word_base = self.word_base
        word_len = self.word_len
        full_masks = self.word_full_mask
        pair_counts = self.pair_counts
        pair_keys = self.word_pair_key
        used = word_history

        for li in letter_indices:
            other = i2 if li == i1 else i1
            other_bit = 1 << other

            for idx in self.single_to_words[li]:
                base = word_base[idx]
                if best_base is not None and base > best_base:
                    break

                w = word_list[idx]
                if w in used:
                    continue
                if word_len[idx] == current_len:
                    continue
                if i1 != i2 and (full_masks[idx] & other_bit):
                    continue

                diff = pair_counts[pair_keys[idx]]
                if best_word is None or base < best_base or (base == best_base and diff < best_diff):
                    best_word = w
                    best_base = base
                    best_diff = diff

        return best_word

    def _fallback(self, word_history):
        for w in self.fallback_list:
            if w not in word_history:
                return w
        return next(iter(self.dictionary))
