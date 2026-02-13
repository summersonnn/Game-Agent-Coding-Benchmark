"""
Agent Code: A6-WordMatrixGame
Model: minimax/minimax-m2.5@preset/fp8
Run: 1
Generated: 2026-02-13 14:10:12
"""

import os
import sys
from collections import defaultdict
from typing import List, Tuple, Set, Dict

import os
import sys
from collections import defaultdict
from typing import List, Tuple, Set, Dict

# ------------------------------------------------------------
# 1.  Dictionary loading (with a small fallback)
# ------------------------------------------------------------
def load_words() -> Set[str]:
    """
    Try to load a standard word list.
    If no file is found we fall back to a tiny set of common words.
    """
    possible_paths = [
        "/usr/share/dict/words",
        "/usr/dict/words",
        "words.txt",
        "wordlist.txt"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                # keep only lower‑case alphabetic words
                return {w.strip().lower() for w in f if w.strip().isalpha()}

    # -----------------------------------------------------------------
    # Fallback – only a few words, enough to demonstrate the algorithm.
    # In a real submission you would supply a proper word list.
    # -----------------------------------------------------------------
    return {
        "cat", "dog", "coat", "taco", "bat", "ball", "apple", "banana",
        "cherry", "date", "egg", "fish", "grape", "ham", "ice", "jam",
        "kite", "lion", "mouse", "nut", "owl", "pig", "queen", "rat",
        "sun", "tea", "umbrella", "violet", "whale", "zebra",
        "acorn", "actor", "afire", "ajar", "apple", "apron", "bacon",
        "badge", "baker", "barge", "baron", "basil", "beach", "beard",
        "beast", "beef", "beer's", "belly", "berry", "birth", "black",
        "blade", "blame", "blank", "blast", "blaze", "bleak", "blend",
        "bless", "blind", "blink", "bliss", "block", "blond", "blood",
        "bloom", "blown", "board", "boast", "boost", "booth", "bound",
        "brain", "brake", "brand", "brass", "brave", "bread", "break",
        "breed", "brick", "bride", "brief", "bring", "brink", "brisk",
        "broad", "broil", "broke", "brook", "broom", "brown", "brush",
        "buddy", "buggy", "bunch", "burst", "buyer", "cabin", "cable",
        "camel", "candy", "cargo", "carry", "carve", "catch", "cause",
        "cease", "chain", "chair", "chalk", "champ", "chaos", "charm",
        "chart", "chase", "cheap", "cheat", "check", "cheek", "cheer",
        "chess", "chest", "chewy", "chief", "child", "chill", "china",
        "choir", "choke", "chord", "chose", "chunk", "cigar", "civic",
        "civil", "claim", "clamp", "clash", "clasp", "class", "clean",
        "clear", "clerk", "click", "cliff", "climb", "cling", "cloak",
        "clock", "clone", "close", "cloth", "cloud", "clout", "clown",
        "coach", "coast", "cobra", "cocoa", "colon", "color", "couch",
        "cough", "could", "count", "court", "cover", "crack", "craft",
        "crane", "crash", "crawl", "craze", "crazy", "cream", "creed",
        "creek", "creep", "crest", "crew", "crisp", "cross", "crowd",
        "crown", "crude", "cruel", "crush", "curve", "cycle", "daily",
        "dairy", "dance", "dealt", "death", "debit", "debut", "decay",
        "delay", "depth", "diary", "dirty", "disco", "ditch", "dough",
        "doubt", "dough", "draft", "drain", "drama", "drank", "drawl",
        "dread", "dream", "dress", "dried", "drift", "drill", "drink",
        "drive", "drown", "drunk", "dying", "eager", "early", "earth",
        "eight", "elbow", "elder", "elect", "elite", "email", "empty",
        "enact", "endow", "enjoy", "enter", "entry", "equal", "equip",
        "erase", "error", "essay", "ethic", "event", "every", "exact",
        "exert", "exile", "exist", "extra", "faint", "fairy", "faith",
        "false", "fancy", "fatal", "fault", "favor", "feast", "fence",
        "ferry", "fetch", "fever", "fewer", "fiber", "field", "fiery",
        "fifth", "fifty", "fight", "final", "first", "fixed", "flame",
        "flash", "flask", "flesh", "flick", "fling", "flint", "float",
        "flock", "flood", "floor", "flour", "fluid", "flung", "flush",
        "flute", "focal", "focus", "force", "forge", "forth", "forum",
        "found", "frame", "frank", "fraud", "freak", "fresh", "fried",
        "front", "frost", "frown", "froze", "fruit", "fully", "funny",
        "fuzzy", "giant", "given", "gland", "glare", "glass", "gleam",
        "glide", "glint", "gloom", "glory", "gloss", "glove", "grace",
        "grade", "grain", "grand", "grant", "grape", "graph", "grasp",
        "grass", "grave", "gravy", "great", "greed", "green", "greet",
        "grief", "grill", "grind", "groan", "groom", "gross", "group",
        "grove", "growl", "grown", "guard", "guess", "guest", "guide",
        "guilt", "guise", "gulf", "guru", "gusty", "habit", "hairy",
        "happy", "hardy", "harsh", "haste", "hasty", "hatch", "haven",
        "heart", "heath", "heave", "heavy", "hedge", "heist", "hello",
        "hence", "herbs", "hinge", "hippo", "hoist", "holly", "homer",
        "homes", "honey", "honor", "horse", "hotel", "hound", "house",
        "hover", "human", "humid", "humor", "hurry", "ideal", "image",
        "imply", "index", "inner", "input", "intro", "issue", "ivory",
        "japan", "jeans", "jelly", "jewel", "joint", "joker", "jolly",
        "judge", "juice", "juicy", "jumbo", "jumpy", "karma", "kayak",
        "kebab", "keyed", "khaki", "knife", "knock", "known", "label",
        "labor", "lapse", "large", "laser", "latch", "later", "laugh",
        "layer", "leads", "learn", "lease", "least", "leave", "legal",
        "lemon", "level", "lever", "light", "limit", "linen", "liner",
        "links", "lions", "lists", "liver", "lives", "llama", "loads",
        "loans", "lobby", "local", "lodge", "lofty", "logic", "loner",
        "loose", "lorry", "loser", "lousy", "loved", "lover", "lower",
        "loyal", "lucky", "lunar", "lunch", "lying", "lyric", "macro",
        "magic", "major", "maker", "mango", "manor", "maple", "march",
        "marry", "marsh", "match", "maybe", "mayor", "medal", "media",
        "melon", "mercy", "merge", "merit", "merry", "messy", "metal",
        "meter", "micro", "might", "miner", "minor", "minus", "mixed",
        "mixer", "model", "modem", "money", "month", "moose", "moral",
        "motor", "motto", "mould", "mount", "mouse", "mouth", "moved",
        "mover", "movie", "muddy", "music", "naive", "naked", "nasty",
        "naval", "nerve", "never", "newly", "niche", "night", "ninth",
        "noble", "noise", "noisy", "north", "notch", "noted", "notes",
        "novel", "nudge", "nurse", "nylon", "occur", "ocean", "offer",
        "often", "olive", "onion", "onset", "opera", "orbit", "order",
        "organ", "other", "ought", "ounce", "outer", "outgo", "owner",
        "oxide", "ozone", "paint", "pairs", "panda", "panel", "panic",
        "pants", "paper", "party", "pasta", "paste", "patch", "pause",
        "peace", "peach", "pearl", "penny", "perch", "peril", "petal",
        "petty", "phase", "phone", "photo", "piano", "piece", "pilot",
        "pinch", "pitch", "pixel", "pizza", "place", "plain", "plane",
        "plant", "plate", "plaza", "plead", "pluck", "plumb", "plume",
        "plump", "plunk", "plush", "point", "polar", "polls", "ponds",
        "poppy", "porch", "poser", "posts", "pouch", "pound", "power",
        "press", "price", "pride", "prime", "print", "prior", "prism",
        "prize", "probe", "promo", "prone", "proof", "prose", "proud",
        "prove", "proxy", "prune", "pulse", "punch", "pupil", "puppy",
        "purse", "quack", "quake", "query", "quest", "queue", "quick",
        "quiet", "quilt", "quirk", "quite", "quota", "quote", "radar",
        "radio", "raise", "rally", "ranch", "range", "rapid", "rarer",
        "ratty", "raven", "rayon", "razor", "reach", "react", "reads",
        "ready", "realm", "rebel", "refer", "reign", "relax", "relay",
        "remit", "renal", "renew", "repay", "reply", "rider", "ridge",
        "rifle", "right", "rigid", "rigor", "rings", "ripen", "risen",
        "riser", "risky", "rival", "river", "roast", "robot", "rocky",
        "rodeo", "roles", "roots", "roses", "rotor", "rouge", "rough",
        "round", "route", "rover", "royal", "rugby", "ruler", "rumor",
        "rural", "rusty", "sadly", "safer", "saint", "salad", "sales",
        "salon", "salsa", "salty", "salve", "sandy", "sassy", "sauce",
        "sauna", "scale", "scalp", "scamp", "scant", "scare", "scarf",
        "scary", "scene", "scent", "school", "scope", "score", "scout",
        "scrap", "seize", "sense", "serve", "setup", "seven", "shade",
        "shaft", "shake", "shall", "shame", "shape", "share", "shark",
        "sharp", "sheep", "sheer", "sheet", "shelf", "shell", "shift",
        "shine", "shiny", "shirt", "shock", "shoes", "shone", "shook",
        "shoot", "shore", "short", "shout", "shown", "shows", "sides",
        "sight", "sigma", "silky", "silly", "since", "sixth", "sixty",
        "sized", "sizes", "skate", "skill", "skimp", "skirt", "skull",
        "slack", "slain", "slang", "slant", "slash", "slate", "slave",
        "sleek", "sleep", "slept", "slice", "slide", "slope", "small",
        "smart", "smell", "smile", "smirk", "smith", "smoke", "snack",
        "snail", "snake", "snare", "sneak", "sniff", "solar", "solid",
        "solve", "sonic", "sorry", "sorts", "souls", "sound", "south",
        "space", "spade", "spare", "spark", "speak", "spear", "speck",
        "speed", "spell", "spend", "spent", "spice", "spicy", "spill",
        "spine", "spite", "split", "spoon", "sport", "spots", "spray",
        "spree", "squad", "stack", "staff", "stage", "stain", "stair",
        "stake", "stale", "stamp", "stand", "stare", "stark", "start",
        "state", "stays", "steak", "steal", "steam", "steel", "steep",
        "steer", "stems", "steps", "stick", "stiff", "still", "sting",
        "stock", "stomp", "stone", "stood", "stool", "store", "storm",
        "story", "stout", "stove", "strap", "straw", "stray", "strip",
        "stuck", "study", "stuff", "style", "sugar", "suite", "sunny",
        "super", "surge", "swamp", "swarm", "swear", "sweat", "sweep",
        "sweet", "swell", "swept", "swift", "swine", "swing", "swirl",
        "swiss", "sword", "syrup", "table", "tacky", "taint", "taken",
        "taker", "tales", "talks", "tangy", "tanks", "tapes", "tardy",
        "taste", "tasty", "taxes", "teach", "teams", "tears", "teddy",
        "teens", "teeth", "tempo", "tends", "tenor", "tense", "tenth",
        "terms", "tests", "texts", "thank", "theft", "their", "theme",
        "there", "these", "thick", "thief", "thigh", "thing", "think",
        "third", "thorn", "those", "three", "threw", "thrill", "thrive",
        "throw", "thumb", "tiger", "tight", "tiles", "timer", "times",
        "tired", "title", "toast", "today", "token", "toner", "tones",
        "tools", "tooth", "topic", "torch", "total", "touch", "tough",
        "tours", "towel", "tower", "towns", "toxic", "trace", "track",
        "trade", "trail", "train", "trait", "trash", "treat", "trees",
        "trend", "trial", "tribe", "trick", "tried", "troop", "trout",
        "truck", "truly", "trunk", "trust", "truth", "tuber", "tulip",
        "tumor", "tuned", "tuner", "tunes", "tunic", "tutor", "twice",
        "twist", "typed", "types", "ultra", "uncle", "under", "union",
        "unite", "units", "unity", "until", "upper", "upset", "urban",
        "urged", "usage", "users", "using", "usual", "utter", "vague",
        "valid", "value", "valve", "vapor", "vault", "vegas", "vegan",
        "veins", "venue", "verse", "video", "views", "villa", "vinyl",
        "viola", "viral", "virus", "visit", "visor", "vista", "vital",
        "vivid", "vocal", "vodka", "vogue", "voice", "voted", "voter",
        "votes", "vouch", "vowel", "wacky", "wader", "wades", "wager",
        "wages", "wagon", "waist", "walks", "walls", "waltz", "wants",
        "waste", "watch", "water", "waved", "waves", "waxed", "weary",
        "weave", "wedge", "weeds", "weeks", "weeps", "weigh", "weird",
        "wells", "whale", "wheat", "wheel", "where", "which", "while",
        "whine", "white", "whole", "whose", "widen", "wider", "widow",
        "width", "wield", "wines", "wings", "wiped", "wiper", "wires",
        "witch", "wives", "woken", "woman", "women", "woods", "words",
        "works", "world", "worms", "worry", "worse", "worst", "worth",
        "would", "wound", "woven", "wrath", "wreck", "wrist", "write",
        "wrong", "wrote", "yacht", "yards", "yearn", "years", "yeast",
        "yield", "young", "yours", "youth", "zebra", "zonal"
    }


# ------------------------------------------------------------
# 2.  Agent definition
# ------------------------------------------------------------
MAX_PATH_LEN = 7               # longest path we ever consider
MAX_WORD_LEN = 2 * MAX_PATH_LEN


class WordMatrixAgent:
    """
    Simple but effective agent for the WordMatrixGame.

    The agent:
      1. Loads and indexes the dictionary once at init time.
      2. Enumerates every simple path of length 2 … MAX_PATH_LEN.
      3. For each path searches the shortest possible extra‑letter word.
      4. Returns the highest‑scoring (path, word) pair, or "PASS" if none.
    """

    # -----------------------------------------------------------------
    # 2.1  Initialization & dictionary preprocessing
    # -----------------------------------------------------------------
    def __init__(self, name: str):
        self.name = name

        # ----- load raw dictionary ---------------------------------
        raw_dict = load_words()

        # ----- keep only words that can ever be used ---------------
        # (length <= 2 * MAX_PATH_LEN)
        self.dictionary: Set[str] = {w for w in raw_dict if len(w) <= MAX_WORD_LEN}

        # ----- index by length for fast candidate retrieval -------
        self.by_len: List[Set[str]] = [set() for _ in range(MAX_WORD_LEN + 1)]
        for w in self.dictionary:
            self.by_len[len(w)].add(w)

    # -----------------------------------------------------------------
    # 2.2  Helper: subsequence test
    # -----------------------------------------------------------------
    @staticmethod
    def _is_subsequence(sub: str, word: str) -> bool:
        """Return True iff `sub` appears in `word` as a subsequence."""
        i = 0
        ls = len(sub)
        for ch in word:
            if i < ls and ch == sub[i]:
                i += 1
                if i == ls:
                    return True
        return i == ls

    # -----------------------------------------------------------------
    # 2.3  Path generation – all simple horizontal/vertical paths
    # -----------------------------------------------------------------
    def _all_paths(self, board: List[List[str]], max_len: int) -> List[List[Tuple[int, int]]]:
        """Return a list of all simple paths of length 2 … max_len."""
        paths = []
        rows, cols = 4, 4

        # directions: up, down, left, right
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # depth‑first search that builds paths
        def dfs(r: int, c: int, visited: Set[Tuple[int, int]], cur: List[Tuple[int, int]]):
            # any path of length >= 2 is a candidate
            if len(cur) >= 2:
                paths.append(cur.copy())
            if len(cur) == max_len:
                return

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols \
                        and (nr, nc) not in visited and board[nr][nc] != '':
                    visited.add((nr, nc))
                    cur.append((nr, nc))
                    dfs(nr, nc, visited, cur)
                    cur.pop()
                    visited.remove((nr, nc))

        # start DFS from every non‑empty cell
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == '':
                    continue
                dfs(r, c, {(r, c)}, [(r, c)])

        return paths

    # -----------------------------------------------------------------
    # 2.4  Evaluate a single path – find the best word & score
    # -----------------------------------------------------------------
    def _evaluate_path(self, path: List[Tuple[int, int]], board: List[List[str]]):
        """
        Returns (path, word, score) if at least one dictionary word matches,
        otherwise None.
        """
        # letters that appear on the board along the path, in order
        path_letters = ''.join(board[r][c] for (r, c) in path)
        L = len(path)

        # 1) exact‑length word – always optimal for this path
        if path_letters in self.by_len[L]:
            # exact match → all cells cleared
            return path, path_letters, 10 + 10 * L

        # 2) otherwise try the smallest possible number of extra letters
        for extra in range(1, L + 1):
            word_len = L + extra
            if word_len > 2 * L:          # rule: word length ≤ 2*path length
                break

            # quick filter: every character of the path must appear in the word
            needed = set(path_letters)

            for w in self.by_len[word_len]:
                # set inclusion test (fast)
                if not needed.issubset(set(w)):
                    continue

                # final subsequence test (more expensive)
                if self._is_subsequence(path_letters, w):
                    # score = 10 + 10 * cleared_cells,
                    # cleared = L - extra
                    score = 10 + 10 * (L - extra)
                    return path, w, score

        # no word fits the rules for this path
        return None

    # -----------------------------------------------------------------
    # 2.5  Main move routine
    # -----------------------------------------------------------------
    def make_move(self,
                  board: List[List[str]],
                  scores: Dict[str, int],
                  total_passes: int):
        """
        Called by the game engine.
        Returns:
            - (path, word)  : a tuple of coordinate list and a valid English word
            - "PASS"        : skip the turn
        """
        # ----- quick sanity: at least two adjacent non‑empty cells? -----
        # (if not, no possible path)
        non_empty = sum(1 for row in board for cell in row if cell != '')
        if non_empty < 2:
            return "PASS"

        # ----- enumerate all candidate paths ----------------------------
        max_len = min(MAX_PATH_LEN, non_empty)
        all_paths = self._all_paths(board, max_len)

        # ----- evaluate each path, keep the best -----------------------
        best_move = None          # (path, word)
        best_score = -1

        for path in all_paths:
            result = self._evaluate_path(path, board)
            if result is None:
                continue
            _, word, score = result
            if score > best_score:
                best_score = score
                best_move = (path, word)

        # ----- if we found any valid move return it --------------------
        if best_move is not None:
            return best_move

        # ----- no word fits any path → pass ---------------------------
        return "PASS"
