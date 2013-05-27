import json
from structures import *

class String(StaticNode):
    abstract = False
    template = '"{value}"'
    alphabet = [chr(i) for i in range(256)]
    subparts = [('value', basestring)]

    @staticmethod
    def default(): return String(['value'])

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0].replace('"', r'\"'))

class Number(StaticNode):
    abstract = False
    template = '{value}'
    subparts = [('value', int)]

    @staticmethod
    def default(): return Number([0])

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0])

class True_(StaticNode):
    abstract = False
    template = 'true'

    @staticmethod
    def default(): return True_()

    def render(self, wrapper=empty_wrapper):
        return wrapper(self)

class False_(StaticNode):
    abstract = False
    template = 'false'

    @staticmethod
    def default(): return False_()

    def render(self, wrapper=empty_wrapper):
        return wrapper(self)

class Null(StaticNode):
    abstract = False
    template = 'null'

    @staticmethod
    def default(): return Null()

    def render(self, wrapper=empty_wrapper):
        return wrapper(self)

class Array(Block):
    abstract = False
    delimiter = ',\n'
    template = '[{children}\n]'
    child_type = Node

class Assignment(StaticNode):
    abstract = False
    subparts = [('key', String), ('value', Node)]
    template = '{key}: {value}'

    @staticmethod
    def default(): return Assignment([String.default(), String.default()])

class Object(Block):
    abstract = False
    child_type = Assignment
    delimiter = ',\n'
    template = '{{{children}\n}}'

def convert(root):
    if isinstance(root, basestring):
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

def parseString(string):
    return convert(json.loads(string))

def parseFile(filename):
    return parseString(open(filename).read())

structures = __name__
