import json
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

    def update(self, text):
        doc = engine.make_doc(engine.BeautifulSoup(text, 'html.parser'))
        id = Doc.objects.count()
        self.docs.sadd(id, json.dumps(doc))
        words = engine.preprocess(text)
        for word in words:
            self.aux.lpush(word, id)

    def dump(self):
        for _,v in self.get_all(self.docs):
            print(v)
            Doc(title=v['title'], body=v['body'], date=v['date']).save()
        for k,v in self.get_all(self.aux):
            ind = Inverted.objects(parameter=k)
            if not ind:
                Inverted(word=k, docs=v).save()
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