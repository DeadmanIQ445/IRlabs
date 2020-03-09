import json
import time

import mongoengine
import redis

import engine


class Cache:
    def __init__(self):
        self.docs = redis.Redis(host='localhost', port=6379, db=0)
        self.aux = redis.Redis(host='localhost', port=6379, db=1)
        self.id = 0

    def update(self, text):
        print(text)
        # doc = DocR(title=doc['title'], body=doc['body'], date=doc['title'],id=self.id)
        doc = {'id': self.id, 'title': text['title'], 'body': text['body'], 'date': text['date']}
        self.docs.set(self.id, json.dumps(doc))
        words = engine.preprocess(text['body'])
        for word in words:
            self.aux.lpush(word, self.id)
        self.id += 1

    def dump(self):
        if len(self.docs.keys())>0:
            db = mongoengine.connect('engine', connect=False)
            print('starting dump')
            key_pair = {}
            for k, v in self.get_all():
                doc = engine.DocR(json=json.loads(v[0]))
                d = engine.Doc(title=doc.title, body=doc.body, date=doc.date).save()
                key_pair[k[0]] = d.id
            for k, v in self.get_all_ind():
                key = k.decode("UTF-8")
                print(key)
                ind = engine.Inverted.objects(word=key)
                if not ind:
                    engine.Inverted(word=key, docs=[key_pair[v[0]]]).save()
                    for i in range(1,len(v)):
                        ind.get().docs.append(key_pair[v[i]])
                else:
                    for i in v:
                        ind.get().docs.append(key_pair[i])
            db.close()
            self.docs.flushdb()
            self.aux.flushdb()
            self.id = 0
            print("Dumped ram into hdd")

    def get_all(self):
        data = []
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.docs.scan(cursor=cursor)
            values = self.docs.mget(*keys)
            values = [value for value in values if value is not None]
            data.append((keys, values))
        return data

    def get_all_ind(self):
        data = []
        for key in self.aux.keys():
            values = self.aux.lrange(key, 0, -1)
            values = list(set(values))
            data.append((key, values))
        return data




def run():
    ca = Cache()
    while True:
        # time.sleep(30)
        ca.dump()
