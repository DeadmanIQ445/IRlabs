import engine



def calculate_query(query, wild_index):
    def add(word1, word2):
        if type(word1) == str:
            if not wild_index.get_word(word1):
                set1 = {}
            else:
                set1 = set(engine.Inverted.objects.get(word=engine.preprocess(word1)[0]).docs)
        else:
            set1 = word1

        if type(word2) == str:
            if not wild_index.get_word(word2):
                return set1
            else:
                set2 = set(engine.Inverted.objects.get(word=engine.preprocess(word1)[0]).docs)
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
                set1 = set(Inverted.objects.get(word=engine.preprocess(word1)[0]).docs)
        else:
            set1 = word1

        if type(word2) == str:
            if not wild_index.get_word(word2):
                return set1
            else:
                set2 = set(Inverted.objects.get(word=engine.preprocess(word2)[0]).docs)
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
        return set(Inverted.objects.get(word=engine.preprocess(a[0])[0]).docs)

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


def search(query, enginge_obj):
    a = engine.process_query(query, enginge_obj.soundex_index, enginge_obj.wild_index)
    a = calculate_query(a, enginge_obj.wild_index)
    return [(i, engine.Doc.objects.get(id=i)) for i in a]
