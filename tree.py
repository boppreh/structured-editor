class Tree(object):
    """
    Abstract element for AST nodes that contain other children.
    """
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
    """
    AST element containing a single string value.
    """
    def __init__(self, type_=None, value=None):
        self.type_ = type_
        self.value = value
        self.parent = None

    def __len__(self):
        return 0

    def __str__(self):
        return self.type_.output_template.format(self.value)


class ListTree(Tree):
    """
    AST element for nodes that contain a variable number of other nodes. Its
    node type "rule" attribute defines what kind of node types are expected as
    children.
    """
    def remove(self, index):
        self.children.pop(index)

    def __str__(self):
        children = map(str, self.children)
        return self.type_.output_template.format(', '.join(children))

class FixedTree(Tree):
    """
    AST element for nodes that contain a fixed number of other nodes. Its node
    type "rule" attribute define the type of each children, by position.

    The dictionary keys are numbers. A dictionary is used to disallow
    insertions and removals of elements.
    """
    def remove(self, index):
        self.children[index] = self.type_.rule[index].default()

    def __str__(self):
        children = map(str, self.children)
        return self.type_.output_template.format(*children)