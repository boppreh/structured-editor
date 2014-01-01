from .structures import *
import ast

def make_ids():
    i = 0
    while True:
        yield i
        i += 1
ids = make_ids()

ast.Module.__len__ = lambda self: len(self.body)
ast.Module.index = lambda self, value: self.body.index(value)
ast.Module.__getitem__ = lambda self, index: self.body[index]
def s(self, index, value):
    self.body[index] = value
ast.Module.__setitem__ = s
ast.Module.render = lambda self, wrapper: wrapper(self).format('\n'.join(map(str, self)))

def convert(node, parent=None):
    node.parent = parent
    node.template = '{}'
    node.node_id = ids.__next__()
    node.defaulted = []
    if isinstance(node, ast.Module):
        for body_part in node.body:
            convert(body_part, node)
    return node

def parse_string(string):
    return convert(ast.parse(string))

def new_empty():
    return parse_string('')

structures = []