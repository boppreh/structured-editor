def index(tree):
    return tree.parent.children.index(tree)

def topmost(tree):
    return tree.parent is None

def bottommost(tree):
    return len(tree) == 0

def leftmost(tree):
    return topmost(tree) or index(tree) == 0

def rightmost(tree):
    return topmost(tree) or index(tree) == len(tree.parent) - 1


def left(tree):
    if leftmost(tree):
        return tree

    return tree.parent[index(tree) - 1]

def right(tree):
    if rightmost(tree):
        return tree

    return tree.parent[index(tree) + 1]

def up(tree):
    return tree.parent or tree

def down(tree):
    return tree[0] if len(tree) else tree

def next(tree):
    return rightup(tree) if bottommost(tree) else down(tree)

def rightup(tree):
    while not topmost(tree) and rightmost(tree):
        tree = up(tree)

    return right(tree)


def replace(tree, replacement):
    if tree.parent:
        tree.parent[index(tree)] = replacement

    return replacement