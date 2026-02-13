"""
Agent Code: A6-WordMatrixGame
Model: openai/gpt-5.2
Run: 2
Generated: 2026-02-13 23:28:39
"""

from array import array
from bisect import bisect_left
import time

from array import array
from bisect import bisect_left
import time
import random


class WordMatrixAgent:
    """
    Heuristic agent for WordMatrixGame (Simplified).

    Core idea:
    - Enumerate many valid board paths (length 2..~10).
    - For each path string P, try to find a dictionary word W such that:
        P is a subsequence of W, and len(P) <= len(W) <= 2*len(P)
      while keeping W as short as possible (fewest "extra" letters),
      because score = 10 + 10 * (cleared_cells) and cleared_cells = 2*|P| - |W|.
    - Uses a preprocessed "ordered letter-pair index" over the dictionary to avoid
      scanning all words for each query.
    """

    # Tunables
    INDEX_MAX_WORD_LEN = 16          # only index words up to this length (huge speed/memory win)
    DEFAULT_MAX_PATH_LEN = 10        # search board paths up to this length (<= 16 always)
    DEFAULT_EXTRA_LIMIT = 3          # try word lengths |P|..|P|+extra_limit (also bounded by <=2|P|)
    MAX_PAIR_FILTERS = 6             # how many (rare) ordered-pair constraints to enforce per query
    MOVE_TIME_BUDGET_SEC = 0.45      # soft internal budget (to reduce risk of external timeout)

    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()  # provided by environment, set of lowercase words

        # 4x4 board helpers
        self._neighbors = self._build_neighbors_4x4()

        # Build compact indices over dictionary words of length 2..INDEX_MAX_WORD_LEN
        self._build_dictionary_indices()

    # ---------------------------- Public API ----------------------------

    def make_move(self, board, scores, total_passes):
        my_score = scores.get(self.name, 0)
        opp_score = 0
        for k, v in scores.items():
            if k != self.name:
                opp_score = v
                break

        # If the game will end immediately by passing and we're ahead, do it.
        if total_passes >= 5 and my_score > opp_score:
            return "PASS"

        # Flatten board and filter empties
        cells = []
        filled = 0
        for r in range(4):
            for c in range(4):
                ch = board[r][c]
                if ch == "":
                    cells.append(None)
                else:
                    cells.append(ch)
                    filled += 1

        if filled < 2:
            return "PASS"

        # Soft time budget
        start_t = time.perf_counter()
        deadline = start_t + self.MOVE_TIME_BUDGET_SEC

        # Search parameters (slightly more aggressive if passes are about to end the game and we're behind)
        max_path_len = min(self.DEFAULT_MAX_PATH_LEN, filled)
        extra_limit = self.DEFAULT_EXTRA_LIMIT
        if total_passes >= 4 and my_score <= opp_score:
            extra_limit = max(extra_limit, 4)

        # Best found so far
        best_cleared = -1
        best_word_len = 10**9
        best_word = None
        best_path = None  # indices 0..15

        # Cache per move: (pattern, target_word_len) -> word or "" (meaning none)
        query_cache = {}

        # Randomize start order a bit to avoid pathological cases
        starts = [i for i, ch in enumerate(cells) if ch is not None]
        random.shuffle(starts)

        # Local bindings for speed
        neighbors = self._neighbors
        dictionary_set = self.dictionary
        idx_to_rc = self._idx_to_rc
        max_index_word_len = self.INDEX_MAX_WORD_LEN

        def consider_current_path(path_indices, letters):
            nonlocal best_cleared, best_word_len, best_word, best_path

            L = len(path_indices)
            if L < 2:
                return

            # Can't beat current best unless we could clear more than best_cleared.
            # Since cleared <= L, any candidate must have L > best_cleared.
            if L <= best_cleared:
                return

            pattern = "".join(letters)

            # Try shortest possible word first for this pattern.
            # extras e => target word length m = L+e, cleared = L-e.
            max_e = extra_limit
            if max_e > L:
                max_e = L
            if L + max_e > 2 * L:
                max_e = L  # redundant but safe
            # Respect what we indexed (we can still do exact check via set for e=0)
            if L + 1 > max_index_word_len:
                max_e = 0  # only exact can possibly work via dict-set, but pattern length is <= 10 so fine

            for e in range(max_e + 1):
                m = L + e
                if m > 2 * L:
                    break

                w = None
                if e == 0:
                    # Exact match (best possible for this path)
                    if pattern in dictionary_set:
                        w = pattern
                else:
                    if m > max_index_word_len:
                        continue
                    key = (pattern, m)
                    cached = query_cache.get(key)
                    if cached is None:
                        found = self._find_word_of_length_with_pattern(pattern, m)
                        query_cache[key] = found if found is not None else ""
                        w = found
                    else:
                        w = cached if cached != "" else None

                if w is not None:
                    cleared = L - e
                    # Primary: maximize cleared. Secondary: minimize word length.
                    if (cleared > best_cleared) or (cleared == best_cleared and m < best_word_len):
                        best_cleared = cleared
                        best_word_len = m
                        best_word = w
                        best_path = list(path_indices)
                    break  # no need to try longer words for this same path

        def dfs_from(start_idx):
            # iterative recursion with closure-based lists
            path = [start_idx]
            letters = [cells[start_idx]]
            visited = 1 << start_idx

            # Explicit stack: (current_idx, next_neighbor_index_to_try)
            stack = [(start_idx, 0)]

            while stack:
                # Time check (not every iteration would also work; this is cheap enough)
                if time.perf_counter() > deadline:
                    return

                cur, ni = stack[-1]

                # Evaluate at current depth
                consider_current_path(path, letters)

                # Stop growing if at max depth
                if len(path) >= max_path_len:
                    stack.pop()
                    if stack:
                        # backtrack one step
                        path.pop()
                        letters.pop()
                        visited &= ~(1 << cur)
                    continue

                nbrs = neighbors[cur]
                if ni >= len(nbrs):
                    # done exploring this node, backtrack
                    stack.pop()
                    if stack:
                        path.pop()
                        letters.pop()
                        visited &= ~(1 << cur)
                    continue

                # Otherwise try next neighbor
                nxt = nbrs[ni]
                stack[-1] = (cur, ni + 1)

                if (visited >> nxt) & 1:
                    continue
                ch = cells[nxt]
                if ch is None:
                    continue

                # advance
                visited |= (1 << nxt)
                path.append(nxt)
                letters.append(ch)
                stack.append((nxt, 0))

        for s in starts:
            if time.perf_counter() > deadline:
                break

            dfs_from(s)

            # Early exit: if we found an exact word clearing max_path_len, can't do better in this search.
            if best_cleared >= max_path_len:
                break

        if best_path is None:
            # If we couldn't find anything at all, PASS is safest.
            return "PASS"

        # Convert index path to (row,col)
        path_coords = [idx_to_rc(i) for i in best_path]
        return (path_coords, best_word)

    # ---------------------------- Index building ----------------------------

    def _build_dictionary_indices(self):
        """
        Build:
        - self._words: list of indexed words (len 2..INDEX_MAX_WORD_LEN)
        - self._wlen: array('B') word lengths by id
        - self._ids_by_len[L]: array('I') of word ids with that length
        - self._pair_ids[pair]: array('I') of word ids that contain letter a before letter b
          where pair = a*26 + b
        - self._pair_example[pair, L]: a single example word id for this ordered pair at length L
        """
        maxL = self.INDEX_MAX_WORD_LEN

        self._words = []
        self._wlen = array("B")
        self._ids_by_len = [array("I") for _ in range(maxL + 1)]  # only use 0..maxL
        self._pair_ids = [array("I") for _ in range(26 * 26)]

        # 1D table: pair* (maxL+1) + L -> word_id or -1
        self._pair_example = array("i", [-1]) * (26 * 26 * (maxL + 1))

        # Dedup helper for "for each target letter b, which 'seen a' have already been paired to b in this word"
        done_for_b = [0] * 26

        # Iterate dictionary and index short words only
        for w in self.dictionary:
            lw = len(w)
            if lw < 2 or lw > maxL:
                continue
            # Assume provided dictionary is already lowercase a-z, but be safe:
            # (Avoid expensive checks; just skip if something looks off.)
            ok = True
            for ch in w:
                o = ord(ch)
                if o < 97 or o > 122:
                    ok = False
                    break
            if not ok:
                continue

            wid = len(self._words)
            self._words.append(w)
            self._wlen.append(lw)
            self._ids_by_len[lw].append(wid)

            # Build ordered-pair occurrence for this word (unique per (a,b) per word).
            seen = 0  # 26-bit mask of letters seen so far
            touched = []  # which b's we touched so we can reset done_for_b efficiently

            for ch in w:
                b = ord(ch) - 97
                if done_for_b[b] == 0:
                    touched.append(b)

                new_mask = seen & ~done_for_b[b]  # a's seen before that haven't yet been paired with this b
                mm = new_mask
                while mm:
                    lsb = mm & -mm
                    a = lsb.bit_length() - 1
                    pair = a * 26 + b
                    self._pair_ids[pair].append(wid)

                    ex_idx = pair * (maxL + 1) + lw
                    if self._pair_example[ex_idx] == -1:
                        self._pair_example[ex_idx] = wid

                    mm -= lsb

                done_for_b[b] |= new_mask
                seen |= (1 << b)

            for b in touched:
                done_for_b[b] = 0

    # ---------------------------- Pattern -> word query ----------------------------

    @staticmethod
    def _is_subsequence(pattern, word):
        i = 0
        L = len(pattern)
        # pattern length is small (<= ~10), word length <= 16 in our indexed search
        for ch in word:
            if ch == pattern[i]:
                i += 1
                if i == L:
                    return True
        return False

    @staticmethod
    def _contains_id(sorted_ids, target):
        # sorted_ids is an array('I') or list of ints, sorted ascending
        j = bisect_left(sorted_ids, target)
        return j != len(sorted_ids) and sorted_ids[j] == target

    def _find_word_of_length_with_pattern(self, pattern, target_len):
        """
        Find any indexed dictionary word W with:
        - len(W) == target_len
        - pattern is a subsequence of W
        Uses ordered-pair constraints to narrow candidates quickly.
        Returns word string or None.
        """
        L = len(pattern)
        if L < 2:
            return None
        if target_len < L or target_len > 2 * L:
            return None
        if target_len > self.INDEX_MAX_WORD_LEN:
            return None

        words = self._words
        wlen = self._wlen
        pair_ids = self._pair_ids
        ids_by_len = self._ids_by_len[target_len]

        # Fast path for length-2 pattern: just need ordered pair (a before b)
        if L == 2:
            a = ord(pattern[0]) - 97
            b = ord(pattern[1]) - 97
            pair = a * 26 + b
            ex_idx = pair * (self.INDEX_MAX_WORD_LEN + 1) + target_len
            wid = self._pair_example[ex_idx]
            return words[wid] if wid != -1 else None

        # Build a small set of ordered-pair constraints implied by the pattern.
        # We include:
        # - adjacent pairs
        # - skip-2 pairs (i -> i+2)
        # - endpoints (0 -> last)
        # Then keep only the rarest few (MAX_PAIR_FILTERS) for filtering.
        pair_set = set()

        # adjacent
        for i in range(L - 1):
            a = ord(pattern[i]) - 97
            b = ord(pattern[i + 1]) - 97
            pair_set.add(a * 26 + b)

        # skip-2
        if L >= 4:
            for i in range(L - 2):
                a = ord(pattern[i]) - 97
                b = ord(pattern[i + 2]) - 97
                pair_set.add(a * 26 + b)

        # endpoints
        a0 = ord(pattern[0]) - 97
        a1 = ord(pattern[-1]) - 97
        pair_set.add(a0 * 26 + a1)

        # If any required pair never occurs in indexed words, impossible
        for p in pair_set:
            if len(pair_ids[p]) == 0:
                return None

        pairs = list(pair_set)
        pairs.sort(key=lambda p: len(pair_ids[p]))
        if len(pairs) > self.MAX_PAIR_FILTERS:
            pairs = pairs[: self.MAX_PAIR_FILTERS]

        # Choose a base iteration list: either the rarest pair list or the length bucket, whichever is smaller.
        base_pair_list = pair_ids[pairs[0]]
        use_len_bucket_as_base = len(ids_by_len) <= len(base_pair_list)

        if use_len_bucket_as_base:
            # Iterate only words of this length, check pair membership by binary search
            for wid in ids_by_len:
                ok = True
                for p in pairs:
                    if not self._contains_id(pair_ids[p], wid):
                        ok = False
                        break
                if not ok:
                    continue
                w = words[wid]
                if self._is_subsequence(pattern, w):
                    return w
            return None

        # Otherwise iterate words that satisfy the rarest pair, then filter by length + other pairs
        for wid in base_pair_list:
            if wlen[wid] != target_len:
                continue
            ok = True
            for p in pairs[1:]:
                if not self._contains_id(pair_ids[p], wid):
                    ok = False
                    break
            if not ok:
                continue
            w = words[wid]
            if self._is_subsequence(pattern, w):
                return w

        return None

    # ---------------------------- Board helpers ----------------------------

    @staticmethod
    def _idx_to_rc(idx):
        return (idx // 4, idx % 4)

    @staticmethod
    def _build_neighbors_4x4():
        neighbors = [[] for _ in range(16)]
        for r in range(4):
            for c in range(4):
                idx = r * 4 + c
                if r > 0:
                    neighbors[idx].append((r - 1) * 4 + c)
                if r < 3:
                    neighbors[idx].append((r + 1) * 4 + c)
                if c > 0:
                    neighbors[idx].append(r * 4 + (c - 1))
                if c < 3:
                    neighbors[idx].append(r * 4 + (c + 1))
        return neighbors
