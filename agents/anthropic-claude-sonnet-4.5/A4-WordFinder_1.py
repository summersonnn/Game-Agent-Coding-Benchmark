"""
Agent Code: A4-WordFinder
Model: anthropic-claude-sonnet-4.5
Run: 1
Generated: 2026-02-12 09:24:15
"""


class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        self.dictionary = load_words()
        
        # Pre-compute word metadata for efficient searching
        self.word_data = {}
        for word in self.dictionary:
            upper = word.upper()
            self.word_data[upper] = {
                'length': len(word),
                'has_hyphen': '-' in word,
                'letters': set(upper),
                'pairs': {upper[i:i+2] for i in range(len(upper)-1)}
            }
    
    def make_move(self, current_word, word_history):
        cur = current_word.upper()
        req1, req2 = cur[0], cur[-1]
        cur_len = len(current_word)
        used = {w.upper() for w in word_history}
        
        candidates = []
        
        for word, data in self.word_data.items():
            if word in used or data['length'] == cur_len:
                continue
            
            if req1 not in data['letters'] or req2 not in data['letters']:
                continue
            
            if word[0] in (req1, req2) or word[-1] in (req1, req2):
                continue
            
            score = data['length']
            if data['has_hyphen']:
                score /= 2
            
            if req1+req2 in data['pairs'] or req2+req1 in data['pairs']:
                score *= 2
            
            candidates.append((word, score))
        
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        # Partial move fallback
        for word, data in self.word_data.items():
            if word in used or data['length'] == cur_len:
                continue
            if ((req1 in data['letters'] and word[0] != req1 and word[-1] != req1) or
                (req2 in data['letters'] and word[0] != req2 and word[-1] != req2)):
                return word
        
        # Last resort
        for word in self.word_data:
            if word not in used:
                return word