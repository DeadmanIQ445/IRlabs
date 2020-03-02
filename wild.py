from BTrees.OOBTree import OOBTree


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