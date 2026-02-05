"""
Agent Code: A4-WordFinder
Model: x-ai/grok-4.1-fast
Run: 2
Generated: 2026-02-05 21:09:40
"""

from collections import defaultdict
import sys

class WordFinderAgent:
    def __init__(self, name):
        self.name = name
        dictionary = load_words()
        self.words = sorted(list(dictionary))
        self.num_words = len(self.words)
        self.letter_mask = [0] * self.num_words
        self.word_len = [0] * self.num_words
        self.first_let = [0] * self.num
