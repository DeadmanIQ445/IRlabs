import re
import string
import nltk
import pickle
import os

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()
from nltk import pos_tag
from nltk.corpus import stopwords

nltk.download('stopwords')
import glob
from bs4 import BeautifulSoup
from jellyfish import soundex
from Levenshtein import ratio as levenshtein


def get_closest_soundex(soundex_index, word):
    x = soundex_index[soundex(word)].copy()
    if word in x:
        x.remove(word)
    return max([(levenshtein(word, i), i) for i in x])[1]


def normalize(text):
    ret = text.lower()
    ret = re.sub('[^a-zA-Z* ]+', '', ret)
    return ret


def tokenize(text):
    return nltk.word_tokenize(text)


def lemmatization(tokens):
    posed = pos_tag(tokens)
    ret = []
    for word, tag in posed:
        wntag = tag[0].lower()  # appropriated from stackoverflow https://stackoverflow.com/a/32959872
        wntag = wntag if wntag in ['a', 'r', 'n', 'v'] else None
        if not wntag:
            lemma = word
        else:
            lemma = lemmatizer.lemmatize(word, wntag)
        ret.append(lemma)
    return ret


def remove_stop_word(tokens):
    sw = set(stopwords.words('english'))
    return [word for word in tokens if not word in sw]


def preprocess(text):
    return remove_stop_word(lemmatization(tokenize(normalize(text))))


def preprocess_no_lemma(text):
    return remove_stop_word(tokenize(normalize(text)))


def make_collection():
    all_files = glob.glob('data/*.sgm')
    collection = []
    for fil in all_files:
        with open(fil, 'rb') as f:
            sample_file = f.read()
            for text in sample_file.split(b"</REUTERS>"):
                soup = BeautifulSoup(text, 'html.parser')
                collection.append(soup.get_text())
    return collection


def make_index(collection):
    inverted_index = {}
    for i in range(len(collection)):
        text = collection[i]
        words = preprocess(text)
        for word in words:
            if word in inverted_index:
                inverted_index[word].add(i)
            else:
                inverted_index[word] = {i}
    return inverted_index


def make_soundex_index(collection):
    soundex_index = {}
    for i in range(len(collection)):
        text = collection[i]
        words = preprocess_no_lemma(text)
        for word in words:
            sound = soundex(word)
            if sound in soundex_index:
                soundex_index[sound].add(word)
            else:
                soundex_index[sound] = {word}
    return soundex_index


from BTrees.OOBTree import OOBTree

t = OOBTree()


class Wild(object):
    def __init__(self):
        self.tree = OOBTree()

    def insert(self, s):
        self.tree.insert(s, s)

    def find_stars(self, s):
        key1 = s
        key2 = s[:-1] + chr(ord(s[-1]) + 1)
        return self.tree.items(min=key1, max=key2, excludemax=True)

    def process_stars(self, s):
        n = s.count('*')
        if n == 1:
            if s[-1] == '*':
                stars = self.find_stars("$" + s[:-1])
            elif s[0] == '*':
                stars = self.find_stars(s[1:] + "$")
            else:
                arr = s.split("*")
                stars = self.find_stars(arr[1] + "$" + arr[0])
            return [sp.split("$")[1] + sp.split("$")[0] for sp, _ in stars]
        else:
            print("Sorry, we only work with one '*' at a time")

    def get_word(self, word):
        return self.tree.get("$" + word, False)


def make_wild_index(collection):
    wild_index = Wild()
    for i in range(len(collection)):
        text = collection[i]
        words = preprocess_no_lemma(text)
        for word in words:
            for i in range(len(word) + 1):
                wild_index.insert(word[i:len(word)] + '$' + word[:i])
    return wild_index


def process_query(query):
    a = remove_stop_word(query.replace('(', "( ").replace(')', " )").split())
    for i in range(len(a)):
        if a[i] in ['(', ')', '||', "&"]:
            continue
        if "*" in a[i]:
            stars = wild_index.process_stars(a[i])
            a[i] = '( ' + ' || '.join(stars) + ' )'
            continue
        if wild_index.get_word(a[i]) == False:
            word = get_closest_soundex(soundex_index, a[i])
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
            if wild_index.get_word(word1) == False:
                set1 = {}
            else:
                set1 = set(index[preprocess(word1)[0]])
        else:
            set1 = word1

        if type(word2) == str:
            if wild_index.get_word(word2) == False:
                return set1
            else:
                set2 = set(index[preprocess(word2)[0]])
        else:
            set2 = word2

        if set1 == {}:
            return set2

        set1.update(set2)
        return set1

    def mult(word1, word2):
        if type(word1) == str:
            if wild_index.get_word(word1) == False:
                set1 = {}
            else:
                set1 = set(index[preprocess(word1)[0]])
        else:
            set1 = word1

        if type(word2) == str:
            if wild_index.get_word(word2) == False:
                return set1
            else:
                set2 = set(index[preprocess(word2)[0]])
        else:
            set2 = word2

        if set1 == {}:
            return set2

        set1 = set1.intersection(set2)
        return set1

    a = query.split()
    num = []
    calc = []
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


def search(index, query):
    a = process_query(query)
    print('Internal representation of query:', a)
    a = calculate_query(a)
    return [(i, collection[i]) for i in a]


collection = make_collection()
index = make_index(collection)
soundex_index = make_soundex_index(collection)
wild_index = make_wild_index(collection)
# def save():
#     if not os.path.exists("./dumps"):
#         os.mkdir("./dumps")
#     with open('./dumps/soundex.pickle', 'wb') as f:
#         pickle.dump(soundex_index, f)
#     with open('./dumps/index.pickle', 'wb') as f:
#         pickle.dump(index, f)
#     with open('./dumps/wild.pickle', 'wb') as f:
#         pickle.dump(wild_index, f)
#
#
# def init():
#     global soundex_index
#     global index
#     global wild_index
#     if os.path.exists("./dumps/soundex.pickle"):
#         with open('./dumps/soundex.pickle', 'rb') as f:
#             soundex_index = pickle.load(f)
#     else:
#         soundex_index = make_soundex_index(collection)
#     if os.path.exists("./dumps/index.pickle"):
#         with open('./dumps/index.pickle', 'rb') as f:
#             index = pickle.load(f)
#     else:
#         index = make_index(collection)
#     if os.path.exists("./dumps/wild.pickle"):
#         with open('./dumps/wild.pickle', 'rb') as f:
#             wild_index = pickle.load(f)
#     else:
#         wild_index = make_wild_index(collection)
#     save()

# init()
# print(soundex_index)
