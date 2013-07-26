class Tree(object):
    def __init__(self, type_, children=()):
        self.type_ = type_
        self.children = list(children)

    def __getitem__(self, i):
        return self.children[i]

    def __len__(self):
        return len(self.children)

class Leaf(object):
    def __init__(self, type_, value=None):
        self.type_ = type_
        self.value = value

    def __len__(self):
        return 0