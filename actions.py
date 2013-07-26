def left(tree):
    if not tree.parent:
        return tree

    index = max(tree.parent.children.index(tree) - 1, 0)
    return tree.parent[index]

def right(tree):
    if not tree.parent:
        return tree

    index = min(tree.parent.children.index(tree) + 1, len(tree.parent) - 1)
    return tree.parent[index]