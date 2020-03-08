import json
import os
from Doc import Doc
from cache import Cache
from index import *
import mongoengine
from processing import *
from soundex import Soundex

mongoengine.connect("engine")

from wild import Wild

if Doc.objects.count() == 0:
    init = True
else:
    init = False


def make_doc(soup):
    if soup.body is not None:
        return {"title": soup.title.string, 'body': soup.body.string, 'date': soup.dateline.string}
    return {"title": soup.text[:100], 'body': soup.text, 'date': None}


def make_collection():
    all_files = glob.glob('./data/*.sgm')
    for fil in all_files:
        with open(fil, 'rb') as f:
            sample_file = f.read()
            for text in sample_file.split(b"</REUTERS>"):
                soup = BeautifulSoup(text, 'html.parser')
                doc = make_doc(soup)
                Doc(title=doc['title'], body=doc['body'], date=doc['date']).save()


def make_index():
    inverted_index = {}
    for i in Doc.objects:
        text = i.body
        words = preprocess(text)
        for word in words:
            if word in inverted_index:
                inverted_index[word].add(i.id)
            else:
                inverted_index[word] = {i.id}
    return inverted_index


def make_wild_index():
    wild_index = Wild()
    for i in Doc.objects:
        text = i.body
        words = preprocess_no_lemma(text)
        for word in words:
            for i in range(len(word) + 1):
                wild_index.insert(word[i:len(word)] + '$' + word[:i])
    return wild_index


def process_query(query, soundex, wild_index):
    a = remove_stop_word(query.replace('(', "( ").replace(')', " )").split())
    for i in range(len(a)):
        if a[i] in ['(', ')', '||', "&"]:
            continue
        if "*" in a[i]:
            stars = wild_index.process_stars(a[i])
            a[i] = '( ' + ' || '.join(stars) + ' )'
            continue
        if not wild_index.get_word(a[i]):
            word = soundex.get_closest_soundex(a[i])
            a[i] = '( ' + word + ' || ' + a[i] + ' )'
    return ' & '.join(a).replace('( & (', '( (') \
        .replace('& || &', '||') \
        .replace(') & )', ') )') \
        .replace('( &', '(') \
        .replace('& )', ')') \
        .replace('& & &', '&')


def get_doc(id, engine):
    a = engine.cache.docs.get(id)
    if a:
        print(a)
        return json.loads(a)
    return Doc.objects.get(id=id)


def save_index(inverted_index):
    for k, v in inverted_index.items():
        Inverted(word=k, docs=v).save()


class Engine:
    def __init__(self):
        if init:
            make_collection()
            save_index(make_index())
        self.soundex_index = Soundex()
        self.wild_index = make_wild_index()
        self.cache = Cache()

    def update(self, doc):
        print(doc)
        words = preprocess_no_lemma(doc)
        print(words)
        for word in words:
            print(word)
            for i in range(len(word) + 1):
                self.wild_index.insert(word[i:len(word)] + '$' + word[:i])
            self.soundex_index.update(word)
        self.cache.update(doc)