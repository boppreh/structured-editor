from .structures import *
import ast

class Expr(Statement):
    pass

class ExprList(DynamicNode):
    delimiter = ', '
    child_type = Expr

class Str(Expr):
    token_rule = '.+'
    template = '\'{value}\''
    subparts = [('value', str)]

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0].replace('"', r'\"'))

class SliceType(StaticNode):
    pass

class Num(Expr, SliceType):
    token_rule = '\d+'
    template = '{value}'
    subparts = [('value', int)]

class Op(StaticNode):
    token_rule = 'or|and'
    template = '{op}'
    subparts = [('op', str)]

# TODO: bool op may have more than two values (ie chained expression)
class BoolOp(Expr):
    template = '{left} {op} {right}'
    subparts = [('left', Expr), ('op', Op), ('right', Expr)]

class Body(Block):
    delimiter = '\n'
    template = '{children}'
    child_type = Statement

class Module(Body):
    pass

class Name(Expr):
    template = '{value}'
    subparts = [('value', str)]
    token_rule = '[a-zA-Z_]\w*'

class NameList(DynamicNode):
    delimiter = ', '
    child_type = Name

class Import(DynamicNode, Statement):
    delimiter = ', '
    template = 'import {children}'
    child_type = Name

class ImportFrom(Statement):
    template = 'from {module} import {names}'
    subparts = [('module', Name), ('names', NameList)]

class Assign(Statement):
    template = '{targets} = {value}'
    subparts = [('targets', ExprList), ('value', Expr)]

class For(Statement):
    template = 'for {target} in {iter}:{body}'
    subparts = [('target', Expr), ('iter', Expr), ('body', Block)]

class Call(Expr):
    template = '{func}({args})'
    subparts = [('func', Expr), ('args', ExprList)]

class Attribute(Expr):
    template = '{value}.{attr}'
    subparts = [('value', Expr), ('attr', Name)]

class Slice(SliceType):
    template = '{lower}:{upper}:{step}'
    subparts = [('lower', Expr), ('upper', Expr), ('step', Expr)]

class Empty(Expr):
    template = ' '
    subparts = []

class Subscript(Expr):
    template = '{value}[{slice}]'
    subparts = [('value', Expr), ('slice', SliceType)]

class List(DynamicNode, Expr):
    template = '[{children}]'
    delimiter = ', '
    child_type = Expr

def convert(node):
    if node is None:
        return Empty()
    elif isinstance(node, ast.Expr):
        return convert(node.value)
    elif isinstance(node, ast.Str):
        return Str([node.s])
    elif isinstance(node, ast.Num):
        return Num([node.n])
    elif isinstance(node, ast.Module):
        return Module(map(convert, node.body))
    elif isinstance(node, ast.Call):
        return Call([convert(node.func), ExprList(map(convert, node.args))])
    elif isinstance(node, ast.Import):
        return Import(Name([alias.name]) for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        return ImportFrom([Name([node.module]), NameList(Name([alias.name]) for alias in node.names)])
    elif isinstance(node, ast.Assign):
        return Assign([ExprList(map(convert, node.targets)), convert(node.value)])
    elif isinstance(node, ast.For):
        return For([convert(node.target), convert(node.iter), Body(map(convert, node.body))])
    elif isinstance(node, ast.Name):
        return Name([node.id])
    elif isinstance(node, ast.Attribute):
        return Attribute([convert(node.value), Name([node.attr])])
    elif isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.Or):
            op = Op(['or'])
        return BoolOp([convert(node.values[0]), op, convert(node.values[1])])
    elif isinstance(node, ast.Subscript):
        return Subscript([convert(node.value), convert(node.slice)])
    elif isinstance(node, ast.Index):
        return Num([node.value])
    elif isinstance(node, ast.Slice):
        return Slice([convert(node.lower), convert(node.upper), convert(node.step)])
    elif isinstance(node, ast.List):
        return List(map(convert, node.elts))

    print('Failed to convert node', node)
    exit()

def parse_string(string):
    return convert(ast.parse(string))

def new_empty():
    return parse_string('')

import inspect
structures = [value for name, value in globals().items()
              if inspect.isclass(value)]
