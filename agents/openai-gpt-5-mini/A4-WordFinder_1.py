"""
Agent Code: A4-WordFinder
Model: openai/gpt-5-mini
Run: 1
Generated: 2026-02-12 09:24:15
"""

from collections import defaultdict

class WordFinderAgent:
    """
    Agent for the WordFinder game.
    Strategy:
    - Precompute, for each character, the set of dictionary words where that character appears
      at an interior position (not first or last). This speeds up lookups for valid moves.
    - On each turn try to find a valid word that:
        * contains both required letters,
        * neither required letter is the first or last letter of the candidate,
        * has length != previous word length,
        * is unused (not in word_history).
      Rank candidates by scored points (hyphen penalty, consecutive-letter bonus) and prefer
      those that leave the opponent with fewer options.
    - If no fully valid word exists, attempt a partial move: a word that contains exactly one
      of the required letters (interior) and does not contain the other required letter anywhere.
      Choose a short partial word to minimize penalty.
    - If nothing else is available, return a short unused dictionary word to avoid crashing.
    """
    def __init__(self, name):
        self.name = name
        # Load dictionary (set of lowercase words) from the environment
        self.dictionary = load_words()
        # All words as a set for quick membership checks
        self.words = set(self.dictionary)

        # Map character -> set(words) where the character appears at an interior position
        self.char_interior = defaultdict(set)
        # Precompute lengths for quick access
        self.word_len = {}

        for w in self.words:
            L = len(w)
            self.word_len[w] = L
            # Only words with length >= 3 can have interior characters
            if L < 3:
                continue
            # Mark characters that appear in interior positions (1 .. L-2)
            for i in range(1, L - 1):
                self.char_interior[w[i]].add(w)

        # Cache for opponent-option counts for a given (first, last) pair
        self._pair_count_cache = {}

    def _score_word(self, word, req1, req2):
        """
        Compute agent's point value for playing 'word' given required letters req1 and req2.
        Scoring adheres to:
         - base points = len(word)
         - hyphen penalty: if '-' in word -> base = base // 2 (integer division)
         - consecutive-letter bonus: if req1+req2 or req2+req1 in word -> base *= 2
        """
        base = len(word)
        if '-' in word:
            base = base // 2
        # Consecutive bonus (either order)
        if (req1 + req2) in word or (req2 + req1) in word:
            base = base * 2
        return base

    def _opponent_options_count(self, first, last):
        """
        Count how many candidate words would be valid for the opponent if they had to
        satisfy letters (first, last). This tries to estimate difficulty for the opponent.
        Uses caching to avoid repeated expensive computations.
        """
        key = (first, last)
        if key in self._pair_count_cache:
            return self._pair_count_cache[key]

        set_a = self.char_interior.get(first, set())
        set_b = self.char_interior.get(last, set())
        inter = set_a & set_b

        # From these, count words that also do NOT have first/last as their own first/last character
        count = 0
        for w in inter:
            if w[0] == first or w[0] == last or w[-1] == first or w[-1] == last:
                continue
            count += 1

        self._pair_count_cache[key] = count
        return count

    def make_move(self, current_word, word_history):
        """
        Choose a word in response to current_word given the game rules and word_history.
        Returns a single word (string).
        """
        cur = current_word.lower()
        if not cur:
            # Defensive fallback
            remaining = list(self.words - word_history)
            return random.choice(remaining) if remaining else random.choice(list(self.words))

        req1 = cur[0]
        req2 = cur[-1]
        prev_len = len(cur)

        # 1) Try to find fully valid words (contain both letters; neither letter at start/end)
        set1 = self.char_interior.get(req1, set())
        set2 = self.char_interior.get(req2, set())
        candidates_raw = set1 & set2  # words that have both letters somewhere interior

        candidates = []
        for w in candidates_raw:
            # Must not have either required letter as first or last character of the new word
            if w[0] == req1 or w[0] == req2 or w[-1] == req1 or w[-1] == req2:
                continue
            if w in word_history:
                continue
            if self.word_len.get(w, len(w)) == prev_len:
                continue
            score = self._score_word(w, req1, req2)
            hyphen = ('-' in w)
            # Opponent options count for defensive tie-breaking
            opp_count = self._opponent_options_count(w[0], w[-1])
            # Sorting key: maximize score -> negative score, prefer no hyphen (False < True),
            # minimize opponent options, prefer longer word (so -len(w)), deterministic fallback by word
            candidates.append((-score, hyphen, opp_count, -self.word_len.get(w, len(w)), w))

        if candidates:
            candidates.sort()
            best_word = candidates[0][-1]
            return best_word

        # 2) No fully valid words -> attempt partial move (contains exactly one required letter interior,
        #    and does NOT contain the other required letter anywhere). Choose shortest to minimize penalty.
        partial_choices = []

        # Words with req1 interior but not containing req2 anywhere
        for w in self.char_interior.get(req1, set()):
            if w in word_history:
                continue
            if self.word_len.get(w, len(w)) == prev_len:
                continue
            if req2 in w:
                continue
            # ensure the single required letter is not placed at start or end (must be interior)
            if w[0] == req1 or w[-1] == req1:
                continue
            partial_choices.append((self.word_len.get(w, len(w)), '-' in w, w))

        # Words with req2 interior but not containing req1 anywhere
        for w in self.char_interior.get(req2, set()):
            if w in word_history:
                continue
            if self.word_len.get(w, len(w)) == prev_len:
                continue
            if req1 in w:
                continue
            if w[0] == req2 or w[-1] == req2:
                continue
            partial_choices.append((self.word_len.get(w, len(w)), '-' in w, w))

        if partial_choices:
            # Prefer shortest length, avoid hyphens, deterministic tie-break
            partial_choices.sort(key=lambda x: (x[0], x[1], x[2]))
            return partial_choices[0][2]

        # 3) No valid or partial moves found. As a last resort return a short unused dictionary word
        #    (this will be treated as invalid and incur the invalid-move penalty, but we must not crash).
        remaining = [w for w in sorted(self.words, key=len) if w not in word_history and self.word_len.get(w, len(w)) != prev_len]
        if remaining:
            return remaining[0]
        # If everything used or filtered out, pick any unused word
        remaining_all = list(self.words - word_history)
        if remaining_all:
            return random.choice(remaining_all)
        # Absolute fallback
        return random.choice(list(self.words))

