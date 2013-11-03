import json
from .structures import *

class Value(StaticNode):
    pass

class String(Value):
    template = '"{value}"'
    alphabet = [chr(i) for i in range(256)]
    subparts = [('value', str)]

    @staticmethod
    def default(): return String(['value'])

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0].replace('"', r'\"'))

class Number(Value):
    template = '{value}'
    subparts = [('value', int)]

    @staticmethod
    def default(): return Number([0])

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0])

class True_(Value):
    template = 'true'

    @staticmethod
    def default(): return True_()

    def render(self, wrapper=empty_wrapper):
        return wrapper(self)

class False_(Value):
    template = 'false'

    @staticmethod
    def default(): return False_()

    def render(self, wrapper=empty_wrapper):
        return wrapper(self)

class Null(Value):
    template = 'null'

    @staticmethod
    def default(): return Null()

    def render(self, wrapper=empty_wrapper):
        return wrapper(self)

class Array(Block, Value):
    delimiter = ',\n'
    template = '[{children}\n]'
    child_type = Value

class Assignment(StaticNode):
    subparts = [('key', String), ('value', Value)]
    template = '{key}: {value}'

    @staticmethod
    def default(): return Assignment([String.default(), String.default()])

class Object(Block, Value):
    child_type = Assignment
    delimiter = ',\n'
    template = '{{{children}\n}}'

def convert(root):
    if isinstance(root, str):
        return String([root])
    elif isinstance(root, bool):
        return True_() if root else False_()
    elif isinstance(root, int):
        return Number([root])
    elif root is None:
        return Null()
    elif isinstance(root, list):
        return Array(map(convert, root))
    elif isinstance(root, dict):
        return Object([Assignment([String([key]), convert(value)])
                       for key, value in root.items()])

def parse_string(string):
    return convert(json.loads(string))

def new_empty():
    return Object()

structures = [Value, Number, True_, False_, Null, Array, Assignment, Object]