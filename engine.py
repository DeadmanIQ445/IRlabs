import os
from Doc import Doc
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


def process_query(query, soundex):
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


def calculate_query(query):
    def add(word1, word2):
        if type(word1) == str:
            if not wild_index.get_word(word1):
                set1 = {}
            else:
                set1 = set(Inverted.objects.get(word=preprocess(word1)[0]).docs)
        else:
            set1 = word1

        if type(word2) == str:
            if not wild_index.get_word(word2):
                return set1
            else:
                set2 = set(Inverted.objects.get(word=preprocess(word1)[0]).docs)
        else:
            set2 = word2

        if set1 == {}:
            return set2

        set1.update(set2)
        return set1

    def mult(word1, word2):
        if type(word1) == str:
            if not wild_index.get_word(word1):
                set1 = {}
            else:
                set1 = set(Inverted.objects.get(word=preprocess(word1)[0]).docs)
        else:
            set1 = word1

        if type(word2) == str:
            if not wild_index.get_word(word2):
                return set1
            else:
                set2 = set(Inverted.objects.get(word=preprocess(word2)[0]).docs)
        else:
            set2 = word2

        if set1 == {}:
            return set2

        set1 = set1.intersection(set2)
        return set1

    a = query.split(" ")
    num = []
    calc = []
    if len(a) == 1:
        return set(Inverted.objects.get(word=preprocess(a[0])[0]).docs)

    for i in range(len(a)):
        if a[i] in ['(', ')', '||', "&"]:
            calc.append(a[i])
            if calc[-2:] == ['(', ')']:
                calc = calc[:len(calc) - 2]
            if calc[-3:] == ['(', '||', ')']:
                num.append(add(num.pop(), num.pop()))
                calc = calc[:len(calc) - 3]
            if len(calc) > 0 and i + 2 <= len(a) and len(num) > 1 and calc[-1] == "&" and a[i + 2] != "(":
                num.append(mult(num.pop(), num.pop()))
                calc.pop()
            if calc[-2:] == ["||", "||"]:
                num.append(add(num.pop(), num.pop()))
                calc.pop()
        else:
            num.append(a[i])

    for i in calc:
        if i == "&":
            num.append(mult(num.pop(), num.pop()))
            calc.pop()
        elif i == "||":
            num.append(add(num.pop(), num.pop()))
            calc.pop()
        else:
            print('Something\'s not right ')

    return list(num[0])


def search(query):
    a = process_query(query, soundex_index)
    a = calculate_query(a)
    return [(i, Doc.objects.get(id=i)) for i in a]


def get_doc(id):
    return Doc.objects.get(id=id)


def update(doc):
    words = preprocess_no_lemma(doc)
    for word in words:
        for i in range(len(word) + 1):
            wild_index.insert(word[i:len(word)] + '$' + word[:i])
            soundex_index.update(word)
            if word in ram_index:
                ram_index[word] += n
            else:
                ram_index[word] = {n}
    ram_docs[n] = make_doc(doc)


def save_index(inverted_index):
    for k, v in inverted_index.items():
        Inverted(word=k, docs=v).save()


if init:
    make_collection()
    save_index(make_index())

soundex_index = Soundex()
wild_index = make_wild_index()

ram_docs = {}
ram_index = {}
n = Doc.objects.count()
