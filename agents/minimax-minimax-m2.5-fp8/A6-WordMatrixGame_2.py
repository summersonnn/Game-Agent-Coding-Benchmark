"""
Agent Code: A6-WordMatrixGame
Model: minimax/minimax-m2.5@preset/fp8
Run: 2
Generated: 2026-02-13 14:10:12
"""

import os
from collections import defaultdict

import os
from collections import defaultdict

# ----------------------------------------------------------------------
# Helper: subsequence test
def is_subsequence(pattern, word):
    """Return True iff pattern appears as a subsequence of word."""
    pi = 0
    pw = len(pattern)
    for ch in word:
        if pi < pw and ch == pattern[pi]:
            pi += 1
            if pi == pw:          # all characters matched
                return True
    return pi == pw


# ----------------------------------------------------------------------
class WordMatrixAgent:
    # ------------------------------------------------------------------
    def __init__(self, name, dict_path="words.txt"):
        """
        name        – agent name (displayed in logs)
        dict_path   – location of a newline‑separated word list (lowercase)
        """
        self.name = name
        self.words = set()               # for quick membership (if ever needed)
        self.by_len = defaultdict(list)  # words grouped by length

        # ------------------------------------------------------------------
        # Try to load a full word list; fall back to a tiny embedded one.
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip().lower()
                    if w:
                        self.words.add(w)
                        self.by_len[len(w)].append(w)
        else:
            # minimal embedded dictionary (enough for simple tests)
            tiny = [
                "an","as","at","be","by","do","go","he","if","in","is","it",
                "me","my","no","of","on","or","so","to","up","we","ace","act",
                "add","age","ago","aid","aim","air","ale","and","ant","any",
                "ape","arc","are","arm","art","ash","ask","ate","bad","bag",
                "ban","bar","bat","bay","bed","bee","bet","bid","big","bin",
                "bit","box","boy","bud","bug","bus","but","buy","can","cap",
                "car","cat","cop","cow","cry","cup","cut","day","den","did",
                "die","dig","dim","dip","dog","dot","dry","due","eat","egg",
                "end","eye","fan","far","fat","fed","fee","few","fig","fin",
                "fit","fix","fly","for","fox","fun","fur","gap","gas","gel",
                "get","gig","gin","god","got","gum","gun","gut","had","ham",
                "has","hat","hay","hen","her","hid","him","his","hit","hog",
                "hop","hot","how","hub","hue","hug","hum","ice","icy","ill",
                "imp","ink","inn","ion","ire","its","ivy","jam","jar","jaw",
                "jet","jog","joy","jug","key","kid","lab","lad","lap","law",
                "lay","led","leg","let","lid","lie","lip","lit","log","lot",
                "low","mad","man","map","mar","mat","may","men","met","mid",
                "mix","mob","mom","mud","mug","nag","nap","net","new","nil",
                "nip","nod","nor","not","now","nut","oak","oar","odd","ode",
                "off","oil","old","one","opt","orb","ore","our","out","owe",
                "owl","own","pad","pal","pan","par","pat","paw","pay","pea",
                "peg","pen","pet","pie","pig","pin","pit","pop","pot","pri",
                "pub","pug","pun","pup","pus","put","rag","ram","ran","rap",
                "rat","raw","ray","red","ref","rib","rid","rig","rim","rip",
                "rob","rod","rot","row","rub","rug","rum","run","rut","sac",
                "sad","sag","sap","sat","saw","say","sea","set","sew","she",
                "sin","sip","sir","sit","six","ski","sky","sly","sob","son",
                "sop","sow","spa","spy","sty","sub","sue","sum","sun","tab",
                "tad","tag","tan","tap","tar","tax","tea","ten","the","thy",
                "tie","tin","tip","toe","ton","top","tot","tow","toy","try",
                "tub","tug","two","urn","use","van","vat","vet","via","vie",
                "vim","vow","wad","wag","war","was","wax","way","web","wed",
                "wee","wet","who","why","wig","win","wit","woe","won","wow",
                "yak","yam","yap","yaw","yea","yes","yet","yin","yip","you",
                "zap","zed","zee","zen","zig","zip","zit","zoo"
            ]
            for w in tiny:
                self.words.add(w)
                self.by_len[len(w)].append(w)

        # sort each length bucket (helps the “shortest word first” logic)
        for lst in self.by_len.values():
            lst.sort()

    # ------------------------------------------------------------------
    # Depth‑first generation of all simple paths of length >= 2.
    def _enumerate_paths(self, board):
        """Yield (letters, coord_list) for every admissible path."""
        n = len(board)
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        def dfs(r, c, visited, path, acc):
            # visited: set of (r,c) already in path
            # path    : current list of coordinates
            # acc     : list to which we append completed paths
            path.append((r, c))
            visited.add((r, c))

            if len(path) >= 2:
                # store a copy
                letters = [board[pr][pc] for (pr, pc) in path]
                acc.append((letters, list(path)))

            # continue deeper (max possible length is 16)
            if len(path) < 16:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in visited \
                            and board[nr][nc] != "":
                        dfs(nr, nc, visited, path, acc)

            path.pop()
            visited.remove((r, c))

        all_paths = []
        for r in range(n):
            for c in range(n):
                if board[r][c] != "":
                    dfs(r, c, set(), [], all_paths)
        return all_paths

    # ------------------------------------------------------------------
    def make_move(self, board, scores, total_passes):
        """
        Called by the game engine.  Returns either
            (list_of_coords, word)   – the chosen move
        or   "PASS"
        """
        # ------------------------------------------------------------------
        # Quick check: at least two non‑empty cells are needed.
        cells = [board[r][c] for r in range(4) for c in range(4) if board[r][c] != ""]
        if len(cells) < 2:
            return "PASS"

        # ------------------------------------------------------------------
        # 1) enumerate all admissible paths
        all_paths = self._enumerate_paths(board)

        # 2) sort by decreasing length (greater theoretical maximum)
        all_paths.sort(key=lambda x: len(x[0]), reverse=True)

        best_score = -1
        best_move = None      # (coords, word)

        # ------------------------------------------------------------------
        # 3) try each path
        for letters, coords in all_paths:
            p = len(letters)
            max_possible = 10 + 10 * p          # exact‑length word
            if max_possible <= best_score:
                # cannot improve any more, even in the best case
                continue

            # word lengths allowed for this path
            for w in range(p, 2 * p + 1):
                word_list = self.by_len.get(w)
                if not word_list:
                    continue
                for word in word_list:          # already shortest‑first
                    if is_subsequence(letters, word):
                        cleared = 2 * p - w
                        score = 10 + 10 * cleared
                        if score > best_score:
                            best_score = score
                            best_move = (coords, word)
                        # shortest word for this p found -> optimal for this path
                        break
                if w == p:        # we already hit exact length, cannot do better
                    break

            # If we already reached the absolute optimum for any path,
            # we can stop scanning the rest.
            if best_score == max_possible:
                break

        # ------------------------------------------------------------------
        if best_move is None:
            return "PASS"
        return best_move
