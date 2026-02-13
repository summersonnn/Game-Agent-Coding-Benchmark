"""
Agent Code: A6-WordMatrixGame
Model: google-gemini-3-flash-preview
Run: 2
Generated: 2026-02-12 18:13:26
"""

from collections import defaultdict

import random
from collections import defaultdict

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = self.load_words()
        # Precompute word lengths for faster filtering
        self.word_lengths = defaultdict(set)
        for word in self.dictionary:
            self.word_lengths[len(word)].add(word)
        # Precompute adjacency for 4x4 grid
        self.adjacent = self._precompute_adjacency()

    def load_words(self):
        # In a real implementation, this would load from a file
        # For this example, we'll use a small sample dictionary
        return {
            'cat', 'dog', 'coat', 'taco', 'act', 'god', 'at', 'do', 'go',
            'cog', 'cod', 'cot', 'dot', 'got', 'act', 'tag', 'toga',
            'a', 'an', 'at', 'ad', 'ago', 'and', 'ant', 'any', 'apt',
            'are', 'ark', 'arm', 'art', 'ash', 'ask', 'asp', 'ate',
            'bad', 'bag', 'ban', 'bar', 'bat', 'bed', 'bee', 'beg',
            'bet', 'bid', 'big', 'bin', 'bit', 'bog', 'box', 'boy',
            'but', 'buy', 'by', 'cab', 'cad', 'cam', 'can', 'cap',
            'car', 'cat', 'caw', 'cod', 'cog', 'con', 'coo', 'cop',
            'cot', 'cow', 'coy', 'cub', 'cue', 'cup', 'cur', 'cut',
            'dab', 'dad', 'dag', 'dam', 'day', 'dew', 'did', 'die',
            'dig', 'dim', 'din', 'dip', 'do', 'dog', 'don', 'dot',
            'dry', 'dub', 'dud', 'due', 'dug', 'dun', 'ear', 'eat',
            'eel', 'egg', 'ego', 'eke', 'elf', 'elk', 'elm', 'emu',
            'end', 'era', 'eve', 'ewe', 'eye', 'fad', 'fan', 'far',
            'fat', 'fax', 'fay', 'fed', 'fee', 'fen', 'few', 'fez',
            'fib', 'fig', 'fin', 'fir', 'fit', 'fix', 'flu', 'fly',
            'foe', 'fog', 'for', 'fox', 'fry', 'fun', 'fur', 'gab',
            'gad', 'gag', 'gal', 'gap', 'gas', 'gay', 'gee', 'gel',
            'gem', 'get', 'gig', 'gin', 'god', 'got', 'gum', 'gun',
            'gut', 'guy', 'had', 'hag', 'ham', 'has', 'hat', 'haw',
            'hay', 'hem', 'hen', 'her', 'hew', 'hey', 'hid', 'him',
            'hip', 'his', 'hit', 'hob', 'hog', 'hop', 'hot', 'how',
            'hub', 'hue', 'hug', 'huh', 'hum', 'hut', 'ice', 'icy',
            'igg', 'ilk', 'ill', 'imp', 'ink', 'inn', 'ion', 'ire',
            'irk', 'its', 'ivy', 'jab', 'jag', 'jam', 'jar', 'jaw',
            'jay', 'jet', 'jib', 'jig', 'job', 'joe', 'jog', 'jot',
            'joy', 'jug', 'jut', 'keg', 'ken', 'key', 'kid', 'kin',
            'kit', 'lab', 'lad', 'lag', 'lap', 'law', 'lax', 'lay',
            'lea', 'led', 'lee', 'leg', 'let', 'lib', 'lid', 'lie',
            'lip', 'lit', 'lob', 'log', 'lop', 'lot', 'low', 'lox',
            'lug', 'lux', 'lye', 'mad', 'man', 'map', 'mar', 'mat',
            'maw', 'may', 'men', 'met', 'mew', 'mid', 'min', 'mit',
            'mix', 'mob', 'mod', 'moo', 'mop', 'mow', 'mud', 'mug',
            'mum', 'nab', 'nag', 'nap', 'naw', 'nay', 'net', 'new',
            'nib', 'nil', 'nip', 'nit', 'nod', 'nog', 'nor', 'not',
            'now', 'nub', 'nun', 'nut', 'oaf', 'oak', 'oar', 'oat',
            'odd', 'ode', 'off', 'oft', 'ohm', 'oil', 'old', 'ole',
            'one', 'opt', 'orb', 'ore', 'our', 'out', 'ova', 'owe',
            'owl', 'own', 'pad', 'pal', 'pam', 'pan', 'pap', 'par',
            'pat', 'paw', 'pay', 'pea', 'peg', 'pen', 'pep', 'per',
            'pet', 'pew', 'pic', 'pie', 'pig', 'pin', 'pip', 'pit',
            'ply', 'pod', 'poe', 'pop', 'pot', 'pow', 'pox', 'pro',
            'pry', 'pub', 'pug', 'pun', 'pup', 'put', 'qua', 'rad',
            'rag', 'rah', 'ram', 'ran', 'rap', 'rat', 'raw', 'ray',
            'red', 'ref', 'rep', 'ret', 'rev', 'rib', 'rid', 'rig',
            'rim', 'rip', 'rob', 'rod', 'roe', 'rot', 'row', 'rub',
            'rue', 'rug', 'rum', 'run', 'rut', 'rye', 'sac', 'sad',
            'sag', 'sal', 'sap', 'sat', 'saw', 'sax', 'say', 'sea',
            'sec', 'see', 'set', 'sew', 'sex', 'she', 'shy', 'sic',
            'sim', 'sin', 'sip', 'sir', 'sis', 'sit', 'six', 'ski',
            'sky', 'sly', 'sob', 'sod', 'son', 'sop', 'sot', 'sow',
            'soy', 'spa', 'spy', 'sub', 'sue', 'sum', 'sun', 'sup',
            'tab', 'tad', 'tag', 'tam', 'tan', 'tap', 'tar', 'tat',
            'taw', 'tax', 'tea', 'ted', 'tee', 'ten', 'the', 'tho',
            'thy', 'tic', 'tie', 'til', 'tin', 'tip', 'tit', 'toe',
            'tog', 'tom', 'ton', 'too', 'top', 'tor', 'tot', 'tow',
            'toy', 'try', 'tub', 'tug', 'tum', 'tun', 'two', 'un',
            'up', 'use', 'van', 'vat', 'vet', 'vex', 'via', 'vie',
            'vim', 'vow', 'wab', 'wad', 'wae', 'wag', 'wan', 'war',
            'was', 'wax', 'way', 'web', 'wed', 'wee', 'wen', 'wet',
            'who', 'why', 'wig', 'win', 'wis', 'wit', 'wok', 'won',
            'woo', 'wow', 'wry', 'wye', 'wyn', 'xis', 'yaw', 'yea',
            'yen', 'yep', 'yes', 'yet', 'yew', 'yin', 'yip', 'yok',
            'you', 'yow', 'yuk', 'yum', 'yup', 'zag', 'zap', 'zed',
            'zee', 'zen', 'zig', 'zip', 'zit', 'zoo'
        }

    def _precompute_adjacency(self):
        """Precompute adjacent cells for all positions in a 4x4 grid"""
        adjacent = {}
        for r in range(4):
            for c in range(4):
                neighbors = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 4 and 0 <= nc < 4:
                        neighbors.append((nr, nc))
                adjacent[(r, c)] = neighbors
        return adjacent

    def make_move(self, board, scores, total_passes):
        # If too many passes, try to make a move to avoid game end
        if total_passes >= 4:
            move = self.find_best_move(board)
            if move:
                return move

        # First try to find a move that clears the most cells
        best_move = self.find_best_move(board)
        if best_move:
            return best_move

        # If no good moves found, pass
        return "PASS"

    def find_best_move(self, board):
        """Find the best move by searching for paths that can form words"""
        best_score = -1
        best_move = None

        # Try all possible path lengths from 2 to 8 (max possible in 4x4 grid)
        for path_length in range(2, 9):
            # Try all possible starting positions
            for r in range(4):
                for c in range(4):
                    if board[r][c] == "":
                        continue
                    path = [(r, c)]
                    move = self._dfs_find_words(board, path, path_length)
                    if move and self.calculate_move_score(board, move) > best_score:
                        best_score = self.calculate_move_score(board, move)
                        best_move = move

        return best_move

    def _dfs_find_words(self, board, current_path, target_length):
        """DFS to find valid paths that can form words"""
        if len(current_path) == target_length:
            # Check if this path can form any valid words
            path_letters = [board[r][c] for r, c in current_path]
            word_candidates = self.find_word_candidates(path_letters, target_length)
            if word_candidates:
                # Return the first valid word found (could be optimized to return the best)
                return (current_path, word_candidates[0])
            return None

        last_r, last_c = current_path[-1]
        for neighbor in self.adjacent[(last_r, last_c)]:
            if neighbor not in current_path and board[neighbor[0]][neighbor[1]] != "":
                result = self._dfs_find_words(board, current_path + [neighbor], target_length)
                if result:
                    return result
        return None

    def find_word_candidates(self, path_letters, path_length):
        """Find all valid words that can be formed from the path letters"""
        candidates = []
        min_word_length = path_length
        max_word_length = min(2 * path_length, 15)  # Max word length in our dictionary

        for word_length in range(min_word_length, max_word_length + 1):
            for word in self.word_lengths.get(word_length, set()):
                if self.is_subsequence(path_letters, word):
                    candidates.append(word)

        return candidates

    def is_subsequence(self, path_letters, word):
        """Check if path_letters is a subsequence of word"""
        it = iter(word)
        return all(c in it for c in path_letters)

    def calculate_move_score(self, board, move):
        """Calculate the potential score for a move"""
        path, word = move
        path_length = len(path)
        word_length = len(word)

        if word_length == path_length:
            # All path cells will be cleared
            return 10 + (10 * path_length)
        else:
            # Some cells will be filled with extra letters
            # Estimate cleared cells as path_length - (word_length - path_length)
            cleared_cells = path_length - (word_length - path_length)
            return 10 + (10 * max(0, cleared_cells))
