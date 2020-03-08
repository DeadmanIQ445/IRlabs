from jellyfish import soundex
from Levenshtein import ratio as levenshtein
from processing import *
from Doc import Doc

class Soundex():
    def __init__(self):
        self.index = {}

    def get_closest_soundex(self, word):
        x = self.index[soundex(word)].copy()
        if word in x:
            x.remove(word)
        return max([(levenshtein(word, i), i) for i in x])[1]

    def make_soundex_index(self):
        for i in Doc.objects:
            text = i.body
            words = preprocess_no_lemma(text)
            for word in words:
                sound = soundex(word)
                if sound in self.index:
                    self.index[sound].add(word)
                else:
                    self.index[sound] = {word}

    def update(self, word):
        sound = soundex(word)
        if sound in self.index:
            self.index[sound].add(word)
        else:
            self.index[sound] = {word}