"""
Agent Code: A4-WordFinder
Model: x-ai/grok-code-fast-1
Run: 1
Generated: 2026-02-12 09:24:15
"""

import collections

import collections
import random

class WordFinderAgent:
    """
    Your agent implementation goes here.
    """
    def __init__(self, name):
        """
        Initialize your agent.
        """
        self.name = name
        self.dictionary = load_words()  # Load the full word dictionary
        self.words_by_letters = collections.defaultdict(list)
        for word in self.dictionary:
            letters = set(word)
            for c1 in letters:
                for c2 in letters:
                    if c1 <= c2:
                        self.words_by_letters[(c1, c2)].append(word)

    def make_move(self, current_word, word_history):
        """
        Called when it's your turn.

        Parameters:
        -----------
        current_word : str
            The word played by the opponent (or the starting word).

        word_history : set
            A set of all words that have been used so far in the game (by both players).
            This includes the current_word and all previous words.
            You MUST NOT return a word that is in this set.

        Returns:
        --------
        str
            Your word choice.
        """
        req1 = current_word[0].lower()
        req2 = current_word[-1].lower()
        key = (min(req1, req2), max(req1, req2))
        candidates = self.words_by_letters.get(key, [])
        valid = []
        for w in candidates:
            if w in word_history:
                continue
            if len(w) == len(current_word):
                continue
            if w[0] in [req1, req2]:
                continue
            if w[-1] in [req1, req2]:
                continue
            valid.append(w)
        
        if valid:
            def score(w):
                base = len(w)
                if '-' in w:
                    base //= 2
                consec = (req1 + req2 in w) or (req2 + req1 in w)
                if consec:
                    base *= 2
                return base
            best = max(valid, key=score)
            return best
        else:
            # Partial move: try with req1 only, shortest word
            partial1 = [w for w in self.dictionary if req1 in w and req2 not in w and w not in word_history and len(w) != len(current_word) and w[0] != req1 and w[-1] != req1 and len(w) > 1]
            if partial1:
                partial1.sort(key=len)
                return partial1[0]
            # Else try with req2 only
            partial2 = [w for w in self.dictionary if req2 in w and req1 not in w and w not in word_history and len(w) != len(current_word) and w[0] != req2 and w[-1] != req2 and len(w) > 1]
            if partial2:
                partial2.sort(key=len)
                return partial2[0]
            else:
                # No valid move, return something invalid to incur penalty (should be rare)
                return "invalid"
