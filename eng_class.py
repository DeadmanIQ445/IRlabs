import engine
from cache import Cache
from soundex import Soundex


class Engine:
    def __init__(self):
        if engine.Doc.objects.count() == 0:
            init = True
        else:
            init = False
        if init:
            engine.make_collection()
            engine.save_index(engine.make_index())
            print("Generated inverted")
        self.soundex_index = Soundex()
        print("Created Soundex")
        self.wild_index = engine.make_wild_index()
        print("Created Wild Card")
        self.cache = Cache()

    def update(self, text):
        soup = engine.BeautifulSoup(text, 'html.parser')
        doc = engine.make_doc(soup)
        words = engine.preprocess_no_lemma(doc['body'])
        for word in words:
            for i in range(len(word) + 1):
                self.wild_index.insert(word[i:len(word)] + '$' + word[:i])
            self.soundex_index.update(word)
        self.cache.update(doc)