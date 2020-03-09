import glob
import json
from bs4 import BeautifulSoup
import mongoengine
from processing import *
from wild import Wild


# mongoengine.connect('engine', alias='alias')

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
    a = Doc.objects.get(id=id)
    return a


def save_index(inverted_index):
    # db = mongoengine.connect('engine', connect=False)

    for k, v in inverted_index.items():
        Inverted(word=k, docs=v).save()
    # db.close()


class Doc(mongoengine.Document):
    title = mongoengine.StringField()
    body = mongoengine.StringField()
    date = mongoengine.StringField()

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(__id=id)

class DocR:
    def __init__(self, title=None, body=None, date=None, id=None, json=None):
        if json:
            self.title = json['title']
            self.body = json['body']
            self.date = json['date']
            self.id = json['id']
        else:
            self.title = title
            self.body = body
            self.date = date
            self.id = id




class Inverted(mongoengine.Document):
    word = mongoengine.StringField()
    docs = mongoengine.ListField()
