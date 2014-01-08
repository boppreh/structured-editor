from .structures import *
import ast
import difflib
import re

class Expr(Statement):
    @classmethod
    def default(cls):
        return Name(['value']) if cls == Expr else cls()

class ExprList(DynamicNode):
    delimiter = ', '
    child_type = Expr

class Empty(StaticNode):
    template = ' '
    subparts = []

class Str(Expr):
    token_rule = '.+'
    template = '\'{value}\''
    subparts = [('value', str)]

    # TODO: remove indentation from mult-line strings inside Blocks
    def render(self, wrapper=empty_wrapper):
        if self.contents[0].count('\n'):
            self.template = '"""{value}"""'
            replacement = ('"""', '\"""')
        else:
            self.template = '\'{value}\''
            replacement = ('\'', '\\\'')
        return wrapper(self).format(value=self.contents[0].replace(*replacement))

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

class UOp(StaticNode):
    token_rule = 'not|+|-'
    template = '{op}'
    subparts = [('op', str)]

    @staticmethod
    def default(): return Op(['not'])

class UnaryOp(Expr):
    template = '{op} {operand}'
    subparts = [('op', UOp), ('operand', Expr)]

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

class Arg(StaticNode):
    template = '{name}={default}'
    #Will be filled in a moment because of a circular dependency.
    subparts = [[('name', Empty), ('default', Expr)]]

class Name(Expr, Arg):
    template = '{value}'
    subparts = [('value', str)]
    token_rule = '[a-zA-Z_]\w*'

    def render(self, wrapper=empty_wrapper):
        if self.contents[0] == 'None' and isinstance(self.parent, SliceType):
            return wrapper(self).format(value=' ')

        return Expr.render(self, wrapper)

Arg.subparts = subparts = [('name', Name), ('default', Expr)]

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
        elif self.contents[1] or self.contents[2]:
            all_args = args if self.contents[1] else keywords
        else:
            all_args = ' '
        return wrapper(self).format(func=self.contents[0].render(wrapper),
                                    all_args=all_args)

class Attribute(Expr):
    template = '{value}.{attr}'
    subparts = [('value', Expr), ('attr', Name)]

class Slice(SliceType):
    template = '{lower}:{upper}'
    subparts = [('lower', Expr), ('upper', Expr), ('step', Expr)]

class SliceWithStep(SliceType):
    template = '{lower}:{upper}:{step}'
    subparts = [('lower', Expr), ('upper', Expr), ('step', Expr)]

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

# TODO: exception types and aliases
class ExceptHandler(StaticNode):
    #template = 'except {type} as {name}:{body}'
    #subparts = [('type', Name), ('name', Name), ('body', Body)]
    template = 'except:{body}'
    subparts = [('body', Body)]

class ExceptHandlers(DynamicNode):
    delimiter = '\n'
    child_type = ExceptHandler

class Try(Statement):
    template = 'try:{body}\n{handlers}'
    subparts = [('body', Body), ('handlers', ExceptHandlers)]

class ArgList(DynamicNode):
    child_type = Arg

class FunctionDef(Statement):
    template = 'def {name}({args}):{body}'
    subparts = [('name', Name), ('args', ArgList), ('body', Body)]

class Return(Statement):
    template = 'return {value}'
    subparts = [('value', Expr)]

# TODO: add message
class Assert(Statement):
    template = 'assert {value}'
    subparts = [('value', Expr)]

def convert(node):
    if isinstance(node, ast.Expr):
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
    elif isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Add):
            op = Op(['+'])
        return BinOp([convert(node.left), op, convert(node.right)])
    elif isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            op = UOp(['not'])
        return UnaryOp([op, convert(node.operand)])
    elif isinstance(node, ast.Compare):
        op = Op([{ast.Eq: '==',
                  ast.Lt: '<',
                  ast.Gt: '>',
                  ast.LtE: '<=',
                  ast.GtE: '>='}[type(node.ops[0])]])
        return BinOp([convert(node.left), op, convert(node.comparators[0])])
    elif isinstance(node, ast.Subscript):
        return Subscript([convert(node.value), convert(node.slice)])
    elif isinstance(node, ast.Index):
        return Num([str(node.value.n)])
    elif isinstance(node, ast.Slice):
        lower = node.lower or ast.Name(id='None', ctx=ast.Load())
        upper = node.upper or ast.Name(id='None', ctx=ast.Load())
        if node.step:
            return SliceWithStep([convert(lower), convert(upper), convert(node.step)])
        else:
            return Slice([convert(lower), convert(upper)])
    elif isinstance(node, ast.List):
        return List(map(convert, node.elts))
    elif isinstance(node, ast.If):
        assert not node.orelse
        return If([convert(node.test), Body(map(convert, node.body)), Empty()])
    elif isinstance(node, ast.Dict):
        items = [DictItem([convert(key), convert(value)]) for key, value in zip(node.keys, node.values)]
        return Dict(items)
    elif isinstance(node, ast.Try):
        handlers_list = []
        for handler in node.handlers:
            #e = ExceptHandler([convert(handler.type), convert(handler.name), Body(map(convert, handler.body))])
            e = ExceptHandler([Body(map(convert, handler.body))])
            handlers_list.append(e)
        return Try([Body(map(convert, node.body)), ExceptHandlers(handlers_list)])
    elif isinstance(node, ast.FunctionDef):
        args = []
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        for arg_node, default in zip(node.args.args, defaults):
            if default:
                args.append(Arg([Name([arg_node.arg]), convert(default)]))
            else:
                args.append(Name([arg_node.arg]))
        return FunctionDef([Name([node.name]), ArgList(args), Body(map(convert, node.body))])
    elif isinstance(node, ast.Return):
        return Return([convert(node.value)])
    elif isinstance(node, ast.Assert):
        return Assert([convert(node.test)])

    print('Failed to convert node', node)
    exit()

def parse_and_print(string):
    return ast.dump(ast.parse(string)).replace('=', '=\n').splitlines(keepends=True)

def parse_string(string):
    converted_parse = convert(ast.parse(string))

    original_text = parse_and_print(string)
    new_text = parse_and_print(converted_parse.render())
    diff = ''.join(difflib.unified_diff(original_text, new_text, n=10))
    if diff:
        print('Parse drift:\n', diff)

    return converted_parse

def new_empty():
    return parse_string('')

import inspect
structures = [value for name, value in globals().items()
              if inspect.isclass(value)]
