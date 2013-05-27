import json
from structures import *

class String(StaticNode):
    abstract = False
    template = '"{value}"'
    alphabet = [chr(i) for i in range(256)]
    subparts = [('value', basestring)]

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0].replace('"', r'\"'))

class Number(StaticNode):
    abstract = False
    template = '"{value}"'
    subparts = [('value', int)]

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0])

class Array(DynamicNode):
    abstract = False
    delimiter = ', '
    template = '[{children}]'
    child_type = Node

class Assignment(StaticNode):
    abstract = False
    subparts = [('key', String), ('value', Node)]
    template = '{key}: {value}'

class Object(DynamicNode):
    child_type = Assignment
    delimiter = ', '
    template = '{{{children}}}'

def convert(root):
    if isinstance(root, basestring):
        return String([root])
    elif isinstance(root, int):
        return Number([root])
    elif isinstance(root, list):
        return Array(map(convert, root))
    elif isinstance(root, dict):
        return Object([Assignment([String(key), convert(value)])
                       for key, value in root.items()])

def parseString(string):
    return convert(json.loads(string))

def parseFile(filename):
    return parseString(open(filename).read())
