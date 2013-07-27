class Tree(object):
    def __init__(self, type_=None, children=()):
        self.type_ = type_
        self.children = list(children)
        self.parent = None
        for child in self.children:
            child.parent = self

    def __getitem__(self, i):
        return self.children[i]


    def __setitem__(self, i, value):
        self.children[i] = value

    def __len__(self):
        return len(self.children)

class Leaf(object):
    def __init__(self, type_, value=None):
        self.type_ = type_
        self.value = value
        self.parent = None

    def __len__(self):
        return 0