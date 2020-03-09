import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from nltk.stem import WordNetLemmatizer
import re
lemmatizer = WordNetLemmatizer()
from nltk import pos_tag
from nltk.corpus import stopwords
nltk.download('stopwords')



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