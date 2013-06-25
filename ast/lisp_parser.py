from pyparsing import *
from .structures import DynamicNode, Node, empty_wrapper, StaticNode

class Value(StaticNode):
    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0])

class SExpression(DynamicNode, Value):
    child_type = Value
    delimiter = ' '
    template = '({children})'

    @staticmethod
    def default(): return SExpression([])

class Program(DynamicNode):
    child_type = SExpression
    delimiter = '\n'

class Identifier(Value):
    subparts = [('value', str)]
    template = '{value}'
    token_rule = '[^ ()]+'

    @staticmethod
    def default(): return String(['name'])

class Number(Value):
    subparts = [('value', int)]
    template = '{value}'
    token_rule = '[+-]?\d+\.?\d*'

    def __init__(self, toks):
        super(Number, self).__init__(self, [int(''.join(toks))])

    @staticmethod
    def default(): return Number([0])

class String(Value):
    subparts = [('value', str)]
    template = '"{value}"'

    @staticmethod
    def default(): return String(['value'])

number = Combine(Word('+-' + nums, nums) + 
                 Optional('.' + Optional(Word(nums))) +
                 Optional(CaselessLiteral('e') + Word('+-' + nums, nums)))

value = number | Word(alphanums + '-/*!@#$%&_') | quotedString
sexp = nestedExpr('(', ')', value)
root = OneOrMore(sexp)

def convert(root):
    if isinstance(root, int):
        return Number([root])
    elif isinstance(root, str) and not root.startswith('"'):
        return Identifier([root])
    elif isinstance(root, str):
        return String([root])
    else:
        return SExpression(map(convert, root))

def parse_string(text):
    return Program(map(convert, root.parseString(text, parseAll=True)))

def new_empty():
    return SExpression([])

structures = [Identifier, Number, String, SExpression]
