"""
Agent Code: A6-WordMatrixGame
Model: xiaomi/mimo-v2-flash@preset/fp8-speedy
Run: 1
Generated: 2026-02-13 22:39:54
"""

from collections import deque

import random
from collections import deque

class WordMatrixAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = self.load_words()
        
    def load_words(self):
        """
        Load dictionary words and pre-process for efficient lookup.
        For this simplified version, I'll use a basic word list.
        In a real implementation, you'd load from a file.
        """
        # Common English words (simplified dictionary)
        words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her',
            'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how',
            'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did',
            'its', 'let', 'put', 'say', 'she', 'too', 'use', 'dad', 'mom', 'cat',
            'dog', 'run', 'big', 'red', 'hot', 'yes', 'eat', 'far', 'fun', 'got',
            'hat', 'ice', 'joy', 'key', 'lot', 'map', 'net', 'own', 'pay', 'ran',
            'sit', 'top', 'van', 'war', 'yet', 'zip', 'able', 'back', 'ball', 'bear',
            'beat', 'been', 'best', 'bird', 'blue', 'boat', 'body', 'book', 'born', 'both',
            'call', 'came', 'care', 'case', 'city', 'club', 'cold', 'come', 'cook', 'cool',
            'dark', 'data', 'deal', 'deep', 'door', 'down', 'draw', 'drop', 'drug', 'duck',
            'each', 'east', 'easy', 'edge', 'else', 'even', 'ever', 'face', 'fact', 'fall',
            'farm', 'fast', 'fear', 'feel', 'file', 'fill', 'film', 'find', 'fine', 'fire',
            'fish', 'five', 'food', 'foot', 'form', 'four', 'free', 'from', 'full', 'game',
            'girl', 'give', 'goal', 'gold', 'good', 'grow', 'hair', 'half', 'hall', 'hand',
            'hard', 'have', 'head', 'hear', 'heat', 'help', 'here', 'high', 'hold', 'home',
            'hope', 'hour', 'huge', 'idea', 'into', 'item', 'join', 'just', 'keep', 'kind',
            'king', 'know', 'land', 'last', 'late', 'lead', 'left', 'less', 'life', 'like',
            'line', 'list', 'live', 'long', 'look', 'lost', 'love', 'main', 'make', 'many',
            'mark', 'mean', 'meet', 'mile', 'mind', 'miss', 'move', 'much', 'must', 'name',
            'near', 'need', 'next', 'nice', 'nine', 'none', 'note', 'once', 'only', 'open',
            'over', 'page', 'part', 'past', 'path', 'pick', 'plan', 'play', 'poor', 'pull',
            'pure', 'push', 'race', 'rain', 'rate', 'read', 'real', 'rest', 'rich', 'ride',
            'risk', 'road', 'rock', 'room', 'rule', 'safe', 'salt', 'save', 'seat', 'seek',
            'self', 'send', 'ship', 'shop', 'show', 'side', 'sign', 'sing', 'size', 'skin',
            'slow', 'snow', 'soft', 'some', 'song', 'soon', 'sort', 'star', 'stay', 'step',
            'stop', 'such', 'sure', 'take', 'talk', 'tall', 'team', 'tell', 'test', 'text',
            'that', 'then', 'they', 'thin', 'this', 'time', 'town', 'tree', 'trip', 'true',
            'turn', 'type', 'unit', 'upon', 'used', 'user', 'vary', 'very', 'view', 'vote',
            'wait', 'walk', 'wall', 'want', 'warm', 'wash', 'wave', 'wear', 'week', 'well',
            'west', 'what', 'when', 'wide', 'wife', 'wild', 'will', 'wind', 'wine', 'wing',
            'wish', 'with', 'wood', 'word', 'work', 'year', 'your', 'zero', 'zone',
            # Longer words for better scoring
            'about', 'above', 'abuse', 'actor', 'acute', 'admit', 'adopt', 'adult', 'after', 'again',
            'agent', 'agree', 'ahead', 'alarm', 'album', 'alert', 'align', 'alike', 'alive', 'allow',
            'alone', 'along', 'alter', 'among', 'anger', 'angle', 'angry', 'apart', 'apple', 'apply',
            'arena', 'argue', 'arise', 'array', 'aside', 'asset', 'audio', 'avoid', 'award', 'aware',
            'badly', 'baker', 'bases', 'basic', 'basis', 'beach', 'began', 'begin', 'begun', 'being',
            'below', 'bench', 'billy', 'birth', 'black', 'blade', 'blame', 'blind', 'block', 'blood',
            'board', 'boost', 'booth', 'bound', 'brain', 'brand', 'bread', 'break', 'breed', 'brief',
            'bring', 'broad', 'broke', 'brown', 'build', 'built', 'buyer', 'cable', 'calif', 'carry',
            'catch', 'cause', 'chain', 'chair', 'chaos', 'chart', 'chase', 'cheap', 'check', 'chest',
            'chief', 'child', 'china', 'chose', 'civil', 'claim', 'class', 'clean', 'clear', 'click',
            'clock', 'close', 'coach', 'coast', 'could', 'count', 'court', 'cover', 'craft', 'crash',
            'crazy', 'cream', 'crime', 'cross', 'crowd', 'crown', 'crude', 'curve', 'cycle', 'daily',
            'dance', 'dated', 'dealt', 'death', 'debut', 'delay', 'depth', 'doing', 'doubt', 'dozen',
            'draft', 'drama', 'drank', 'drawn', 'dream', 'dress', 'drill', 'drink', 'drive', 'drove',
            'dying', 'eager', 'early', 'earth', 'eight', 'elite', 'empty', 'enemy', 'enjoy', 'enter',
            'entry', 'equal', 'error', 'event', 'every', 'exact', 'exist', 'extra', 'faith', 'false',
            'fancy', 'fault', 'fiber', 'field', 'fifth', 'fifty', 'fight', 'final', 'first', 'fixed',
            'flash', 'fleet', 'floor', 'fluid', 'focus', 'force', 'forth', 'forty', 'forum', 'found',
            'frame', 'frank', 'fraud', 'fresh', 'front', 'fruit', 'fully', 'funny', 'giant', 'given',
            'glass', 'globe', 'going', 'grace', 'grade', 'grand', 'grant', 'grass', 'great', 'green',
            'gross', 'group', 'grown', 'guard', 'guess', 'guest', 'guide', 'happy', 'harry', 'heart',
            'heavy', 'hence', 'henry', 'horse', 'hotel', 'house', 'human', 'ideal', 'image', 'index',
            'inner', 'input', 'issue', 'japan', 'jimmy', 'joint', 'jones', 'judge', 'known', 'label',
            'large', 'laser', 'later', 'laugh', 'layer', 'learn', 'lease', 'least', 'leave', 'legal',
            'level', 'lewis', 'light', 'limit', 'links', 'lives', 'local', 'logic', 'loose', 'lower',
            'lucky', 'lunch', 'lying', 'magic', 'major', 'maker', 'march', 'maria', 'match', 'maybe',
            'mayor', 'meant', 'media', 'metal', 'might', 'minor', 'minus', 'mixed', 'model', 'money',
            'month', 'moral', 'motor', 'mount', 'mouse', 'mouth', 'movie', 'music', 'needs', 'never',
            'newly', 'night', 'noise', 'north', 'noted', 'novel', 'nurse', 'occur', 'ocean', 'offer',
            'often', 'order', 'other', 'ought', 'paint', 'panel', 'paper', 'party', 'peace', 'peter',
            'phase', 'phone', 'photo', 'piece', 'pilot', 'pitch', 'place', 'plain', 'plane', 'plant',
            'plate', 'point', 'pound', 'power', 'press', 'price', 'pride', 'prime', 'print', 'prior',
            'prize', 'proof', 'proud', 'prove', 'queen', 'quick', 'quiet', 'quite', 'radio', 'raise',
            'range', 'rapid', 'ratio', 'reach', 'ready', 'refer', 'right', 'rival', 'river', 'robin',
            'roger', 'roman', 'rough', 'round', 'route', 'royal', 'rural', 'scale', 'scene', 'scope',
            'score', 'sense', 'serve', 'seven', 'shall', 'shape', 'share', 'sharp', 'sheet', 'shelf',
            'shell', 'shift', 'shine', 'shirt', 'shock', 'shoot', 'short', 'shown', 'sight', 'since',
            'sixth', 'sixty', 'sized', 'skill', 'sleep', 'slide', 'small', 'smart', 'smile', 'smith',
            'smoke', 'solid', 'solve', 'sorry', 'sound', 'south', 'space', 'spare', 'speak', 'speed',
            'spend', 'spent', 'split', 'spoke', 'sport', 'staff', 'stage', 'stake', 'stand', 'start',
            'state', 'steam', 'steel', 'stick', 'still', 'stock', 'stone', 'stood', 'store', 'storm',
            'story', 'strip', 'stuck', 'study', 'stuff', 'style', 'sugar', 'suite', 'super', 'sweet',
            'table', 'taken', 'taste', 'taxes', 'teach', 'terry', 'texas', 'thank', 'theft', 'their',
            'theme', 'there', 'these', 'thick', 'thing', 'think', 'third', 'those', 'three', 'threw',
            'throw', 'tight', 'times', 'tired', 'title', 'today', 'topic', 'total', 'touch', 'tough',
            'tower', 'track', 'trade', 'train', 'treat', 'trend', 'trial', 'tribe', 'trick', 'tried',
            'tries', 'truck', 'truly', 'trust', 'truth', 'twice', 'under', 'undue', 'union', 'unity',
            'until', 'upper', 'upset', 'urban', 'usage', 'usual', 'valid', 'value', 'video', 'virus',
            'visit', 'vital', 'vocal', 'voice', 'waste', 'watch', 'water', 'wheel', 'where', 'which',
            'while', 'white', 'whole', 'whose', 'woman', 'women', 'world', 'worry', 'worse', 'worst',
            'worth', 'would', 'wound', 'write', 'wrong', 'wrote', 'yield', 'young', 'youth'
        }
        return words
    
    def is_subsequence(self, path_str, word):
        """
        Check if path_str is a subsequence of word.
        """
        i = 0
        for char in word:
            if i < len(path_str) and char == path_str[i]:
                i += 1
        return i == len(path_str)
    
    def find_paths(self, board):
        """
        Find all possible paths of length 2-4 on the board.
        Returns list of paths, each path is a list of (row, col) coordinates.
        """
        paths = []
        rows, cols = 4, 4
        
        # Directions: up, down, left, right
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        def dfs(r, c, path, visited):
            # Add current cell to path
            path.append((r, c))
            visited.add((r, c))
            
            # If path length is at least 2, add to results
            if len(path) >= 2:
                paths.append(path[:])
            
            # If path length is 4, stop (max length for efficiency)
            if len(path) == 4:
                path.pop()
                visited.remove((r, c))
                return
            
            # Explore neighbors
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols and 
                    board[nr][nc] != "" and (nr, nc) not in visited):
                    dfs(nr, nc, path, visited)
            
            path.pop()
            visited.remove((r, c))
        
        # Start DFS from each non-empty cell
        for i in range(rows):
            for j in range(cols):
                if board[i][j] != "":
                    dfs(i, j, [], set())
        
        return paths
    
    def find_best_move(self, board):
        """
        Find the best move by checking all paths and dictionary words.
        """
        paths = self.find_paths(board)
        if not paths:
            return None
        
        best_score = -1
        best_move = None
        
        # Sort paths by length (longer paths can give higher scores)
        paths.sort(key=len, reverse=True)
        
        for path in paths:
            # Get the string from the path
            path_str = "".join(board[r][c] for r, c in path)
            path_len = len(path)
            
            # Check words of appropriate length
            min_word_len = path_len
            max_word_len = min(2 * path_len, 16)  # Max word length 16
            
            for word_len in range(min_word_len, max_word_len + 1):
                # Look for words of this length that contain path_str as subsequence
                for word in self.dictionary:
                    if len(word) != word_len:
                        continue
                    
                    if self.is_subsequence(path_str, word):
                        # Calculate score
                        cleared_cells = 2 * path_len - word_len
                        score = 10 + 10 * cleared_cells
                        
                        if score > best_score:
                            best_score = score
                            best_move = (path, word)
                        
                        # If we can clear all cells, take it immediately
                        if cleared_cells == path_len:
                            return best_move
        
        return best_move
    
    def make_move(self, board, scores, total_passes):
        """
        Make a move on the board.
        """
        try:
            # Find the best move
            move = self.find_best_move(board)
            
            if move:
                path, word = move
                # Validate the move
                if len(path) >= 2 and len(word) >= len(path) and len(word) <= 2 * len(path):
                    return (path, word)
            
            # If no good move found, pass
            return "PASS"
            
        except Exception as e:
            # If anything goes wrong, pass to avoid penalty
            return "PASS"
