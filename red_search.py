import json

import engine
import pers_search


def calculate_query(query, wild_index, cache):
    def add(word1, word2):
        if type(word1) == str:
            if not wild_index.get_word(word1):
                set1 = {}
            else:
                set1 = set(map(int, cache.aux.lrange(engine.preprocess(word1)[0], 0, -1)))
        else:
            set1 = word1

        if type(word2) == str:
            if not wild_index.get_word(word2):
                return set1
            else:
                set2 = set(map(int, cache.aux.lrange(engine.preprocess(word2)[0], 0, -1)))
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
                set1 = set(map(int, cache.aux.lrange(engine.preprocess(word1)[0], 0, -1)))
        else:
            set1 = word1

        if type(word2) == str:
            if not wild_index.get_word(word2):
                return set1
            else:
                set2 = set(map(int, cache.aux.lrange(engine.preprocess(word2)[0], 0, -1)))
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
        return set(map(int, cache.aux.lrange(engine.preprocess(a[0])[0], 0, -1)))

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


def search(query, engine_obj):
    if len(engine_obj.cache.docs.keys())==0:
        print('No such docs in ram, going hard')
        return pers_search.search(query, engine_obj)

    a = engine.process_query(query, engine_obj.soundex_index, engine_obj.wild_index)
    a = calculate_query(a, engine_obj.wild_index, engine_obj.cache)

    if len(a)==0:
        print('No such docs in ram, going hard')
        return pers_search.search(query, engine_obj)
    print([(i,type(i)) for i in a])
    print([engine_obj.cache.docs.get(i) for i in list(a)])
    return [(i, engine.DocR(json=json.loads(engine_obj.cache.docs.get(i)))) for i in a]
