import json
import pickle
import time

import redis
from Doc import DocR
from Doc import Doc
import engine
from index import Inverted


class Cache:
    def __init__(self):
        self.docs = redis.Redis(host='localhost', port=6379, db=0)
        self.aux = redis.Redis(host='localhost', port=6379, db=1)
        self.id = 0

    def update(self, text):
        doc = engine.make_doc(engine.BeautifulSoup(text, 'html.parser'))
        # doc = DocR(title=doc['title'], body=doc['body'], date=doc['title'],id=self.id)
        doc = {'id': self.id, 'title': doc['title'], 'body': doc['body'], 'date': doc['date']}
        self.docs.set(self.id, json.dumps(doc))
        words = engine.preprocess(text)
        for word in words:
            self.aux.lpush(word, self.id)
        self.id += 1

    def dump(self):
        key_pair = {}
        for k, v in self.get_all(self.docs):
            doc = DocR(json=json.loads(v))
            d = Doc(title=doc.title, body=doc.body, date=doc.date).save()
            key_pair[k] = d.id
        for k, v in self.get_all(self.aux):
            ind = Inverted.objects(parameter=k)
            if not ind:
                Inverted(word=k, docs=key_pair[v]).save()
            else:
                ind.get().docs.append(v)
        self.docs.flushdb()
        self.aux.flushdb()

    def get_all(self, red):
        data = []
        cursor = '0'
        while cursor != 0:
            cursor, keys = red.scan(cursor=cursor)
            values = red.mget(*keys)
            values = [value for value in values if value is not None]
            data.append((keys, values))
        return data


def run():
    ca = Cache()
    while True:
        time.sleep(60)
        ca.dump()
