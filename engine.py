import re
import string
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from nltk.stem import WordNetLemmatizer
lemmatizer=WordNetLemmatizer()
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
    wntag = tag[0].lower() # appropriated from stackoverflow https://stackoverflow.com/a/32959872
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