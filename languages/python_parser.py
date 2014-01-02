from .structures import *
import ast

class Expr(Statement):
    @staticmethod
    def default(): return Name(['value'])

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
    subparts = [('value', str)]

    @staticmethod
    def default(): return Num(['0'])

class Op(StaticNode):
    token_rule = 'or|and'
    template = '{op}'
    subparts = [('op', str)]

    @staticmethod
    def default(): return Op(['or'])

# TODO: bool op may have more than two values (ie chained expression)
class BinOp(Expr):
    template = '{left} {op} {right}'
    subparts = [('left', Expr), ('op', Op), ('right', Expr)]

class Body(Block):
    delimiter = '\n'
    template = '{children}'
    child_type = Statement

    def render(self, wrapper=empty_wrapper):
        if len(self) == 0:
            return wrapper(self).format(children='\n    pass')
        else:
            return Block.render(self, wrapper)

class Module(Block):
    pass

class Name(Expr):
    template = '{value}'
    subparts = [('value', str)]
    token_rule = '[a-zA-Z_]\w*'

class NameList(DynamicNode):
    delimiter = ', '
    child_type = Name
    min_length = 1

class Import(DynamicNode, Statement):
    delimiter = ', '
    template = 'import {children}'
    child_type = Name
    min_length = 1

class ImportFrom(Statement):
    template = 'from {module} import {names}'
    subparts = [('module', Name), ('names', NameList)]

class Assign(Statement):
    template = '{targets} = {value}'
    subparts = [('targets', ExprList), ('value', Expr)]
    @staticmethod
    def default(): return Assign([ExprList([Expr.default()]), Expr.default()])

class For(Statement):
    template = 'for {target} in {iter}:{body}'
    subparts = [('target', Expr), ('iter', Expr), ('body', Body)]

class Keyword(StaticNode):
    template = '{arg}={value}'
    subparts = [('arg', Name), ('value', Expr)]

class Keywords(DynamicNode):
    delimiter = ', '
    child_type = Keyword

class Call(Expr):
    template = '{func}({all_args})'
    subparts = [('func', Expr), ('args', ExprList), ('keywords', Keywords)]

    def render(self, wrapper=empty_wrapper):
        args = self.contents[1].render(wrapper)
        keywords = self.contents[2].render(wrapper)
        if self.contents[1] and self.contents[2]:
            all_args = args + ', ' + keywords
        else:
            all_args = args + keywords
        return wrapper(self).format(func=self.contents[0].render(wrapper),
                                    all_args=all_args)

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

class If(Statement):
    template = 'if {test}:{body}{orelse}'
    subparts = [('test', Expr), ('body', Body), ('orelse', Empty)]

class DictItem(StaticNode):
    template = '{key}: {value}'
    subparts = [('key', Expr), ('value', Expr)]

class Dict(DynamicNode, Expr):
    template = '{{{children}}}'
    child_type = DictItem
    delimiter = ', '

def convert(node):
    if node is None:
        return Empty()
    elif isinstance(node, ast.Expr):
        return convert(node.value)
    elif isinstance(node, ast.Str):
        return Str([node.s])
    elif isinstance(node, ast.Num):
        return Num([str(node.n)])
    elif isinstance(node, ast.Module):
        return Module(map(convert, node.body))
    elif isinstance(node, ast.keyword):
        return Keyword([Name([node.arg]), convert(node.value)])
    elif isinstance(node, ast.Call):
        args = ExprList(map(convert, node.args))
        keywords = Keywords(map(convert, node.keywords))
        return Call([convert(node.func), args, keywords])
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
        elif isinstance(node.op, ast.And):
            op = Op(['and'])
        return BinOp([convert(node.values[0]), op, convert(node.values[1])])
    elif isinstance(node, ast.Compare):
        return BinOp([convert(node.left), Op(['==']), convert(node.comparators[0])])
    elif isinstance(node, ast.Subscript):
        return Subscript([convert(node.value), convert(node.slice)])
    elif isinstance(node, ast.Index):
        return Num([node.value])
    elif isinstance(node, ast.Slice):
        return Slice([convert(node.lower), convert(node.upper), convert(node.step)])
    elif isinstance(node, ast.List):
        return List(map(convert, node.elts))
    elif isinstance(node, ast.If):
        assert not node.orelse
        return If([convert(node.test), Body(map(convert, node.body)), Empty()])
    elif isinstance(node, ast.Dict):
        items = [DictItem([convert(key), convert(value)]) for key, value in zip(node.keys, node.values)]
        return Dict(items)

    print('Failed to convert node', node)
    exit()

def parse_string(string):
    return convert(ast.parse(string))

def new_empty():
    return parse_string('')

import inspect
structures = [value for name, value in globals().items()
              if inspect.isclass(value)]
