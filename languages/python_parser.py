from .structures import *
import ast
import difflib
import re
import html
import textwrap

class SliceType(StaticNode):
    pass

class Expr(Statement, SliceType):
    @classmethod
    def default(cls):
        return Name(['value']) if cls == Expr else cls()

class ExprList(DynamicNode):
    delimiter = ', '
    child_type = Expr

class Empty(StaticNode):
    template = ' '
    subparts = []

class NameConstant(Expr):
    template = '{value}'
    subparts = [('value', str)]

    def render(self, wrapper=empty_wrapper):
        if self.contents[0] == 'None' and (isinstance(self.parent.parent, Subscript)
                                           or isinstance(self.parent, ExceptHandler)
                                           or isinstance(self.parent, Return)):
            return wrapper(self).format(value=' ')
        return Expr.render(self, wrapper)

class Str(Expr):
    token_rule = '.+'
    template = '\'{value}\''
    subparts = [('value', str)]

    def render(self, wrapper=empty_wrapper):
        # Escape backslashes properly.
        value = self.contents[0].replace('\\', '\\\\')

        if self.contents[0].count('\n') == 1:
            # If we have a single line break, replace it \n instead of using a
            # multi-line string..
            self.template = '\'{value}\''
            value = value.replace('\'', '\\\'').replace('\n', '\\n')

        elif self.contents[0].count('\n') > 1:
            # Use triple quotes for multi-line strings.
            self.template = '"""{value}"""'
            value = textwrap.dedent(value.replace('"""', '\"""'))

        else:
            # Otherwise, just remember to escape single quotes.
            self.template = '\'{value}\''
            value = value.replace('\'', '\\\'')
        
        format = wrapper(self)

        # Hackish way to escape HTML characters from raw strings. Detects the
        # output will be HTML and then escapes HTML tags.
        if '<span' in format:
            value = html.escape(value)

        return format.format(value=value)

class Num(Expr):
    token_rule = '\d+'
    template = '{value}'
    subparts = [('value', str)]

    @staticmethod
    def default(): return Num(['0'])

class Bytes(Expr):
    token_rule = '.+'
    template = 'b\'{value}\''
    subparts = [('value', str)]

    @staticmethod
    def default(): return Bytes([''])

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

class BinOp(Expr):
    template = '{left} {op} {right}'
    subparts = [('left', Expr), ('op', Op), ('right', Expr)]

    def render(self, wrapper=empty_wrapper):
        if isinstance(self.parent, BinOp):
            self.template = '({left} {op} {right})'
        else:
            self.template = '{left} {op} {right}'

        return super(BinOp, self).render(wrapper)

class BoolOp(Expr):
    template = '{children}'
    subparts = [('op', Op), ('children', ExprList)]

    def render(self, wrapper=empty_wrapper):
        op = ' ' + self[0].render(wrapper) + ' '
        self[1].delimiter = op
        if isinstance(self.parent.parent, BoolOp):
            self.template = '({children})'
        else:
            self.template = '{children}'
        return super(Expr, self).render(wrapper)

class AugAssign(Statement):
    template = '{left} {op}= {right}'
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
    # Name will be filled in a moment because of a circular dependency.
    subparts = [[('name', Empty), ('default', Expr)]]

class Name(Expr, Arg):
    template = '{value}'
    subparts = [('value', str)]
    token_rule = '[a-zA-Z_]\w*'

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

class ImportLevel(StaticNode):
    template = '.'
    subparts = []

class ImportLevelList(DynamicNode):
    delimiter = ''
    child_type = ImportLevel

class ImportFrom(Statement):
    template = 'from {level}{module} import {names}'
    subparts = [('level', ImportLevelList), ('module', Name), ('names', NameList)]

class Assign(Statement):
    template = '{targets} = {value}'
    subparts = [('targets', ExprList), ('value', Expr)]
    @staticmethod
    def default(): return Assign([ExprList([Expr.default()]), Expr.default()])

class For(Statement):
    template = 'for {target} in {iter}:{body}'
    subparts = [('target', Expr), ('iter', Expr), ('body', Body)]

# TODO: allow multiple items
class With(Statement):
    template = 'with {item}:{body}'
    subparts = [('item', Expr), ('body', Body)]

class WithAs(Statement):
    template = 'with {item} as {alias}:{body}'
    subparts = [('item', Expr), ('alias', Name), ('body', Body)]

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

    def render(self, wrapper=empty_wrapper):
        has_upper = self[0][0] == 'None'
        has_lower = self[1][0] == 'None'
        if not has_upper and not has_lower:
            self.template = ':'
        elif not has_lower:
            self.template = ':{upper}' 
        elif not has_upper:
            self.template = '{lower}:' 
        else:
            self.template = '{lower}:{upper}'

        return super(Slice, self).render(wrapper)

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

class Tuple(DynamicNode, Expr):
    template = '({children})'
    delimiter = ', '
    child_type = Expr

class While(Statement):
    template = 'while {test}:{body}'
    subparts = [('test', Expr), ('body', Body)]

class Else(StaticNode):
    """ The 'else' clause of a conditional. """
    subparts = [('body', Body)]
    template = '\nelse:{body}'

class If(StaticNode):
    """ The condition/body pair of an 'if'/'elif' control structure. """
    template = 'if {test}:{body}'
    subparts = [('test', Expr), ('body', Body)]

    def render(self, wrapper=empty_wrapper):
        if self.parent.index(self) != 0:
            self.template = 'el' + If.template
        else:
            self.template = If.template
        return super(If, self).render(wrapper)

class IfChain(DynamicNode):
    """
    Structure for the first 'if' and the chain of 'elseif' that follow.
    """
    child_type = If
    delimiter = '\n'

    @staticmethod
    def default():
        return IfChain([If.default()])

class FullIf(Statement):
    """ If control structure, including related elseifs and elses. """
    template = '{if_chain}{else}'
    subparts = [('if_chain', IfChain), ('else', Else)]

    @staticmethod
    def default():
        return FullIf([IfChain.default(), Else.default()])

    def render(self, wrapper=empty_wrapper):
        if len(self) == 1:
            self.template = FullIf.template.replace('{else}', '')
        else:
            self.template = FullIf.template
        return super(FullIf, self).render(wrapper)

class IfExp(Expr):
    template = '{body} if {test} else {orelse}'
    subparts = [('body', Expr), ('test', Expr), ('orelse', Expr)]

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
    template = 'except {type}:{body}'
    subparts = [('type', Expr), ('body', Body)]

    def render(self, wrapper=empty_wrapper):
        if self[0][0] == 'None':
            self.template = 'except:{body}'
        else:
            self.template = 'except {type}:{body}'

        return super(ExceptHandler, self).render(wrapper)

class ExceptHandlers(DynamicNode):
    delimiter = '\n'
    child_type = ExceptHandler

class Try(Statement):
    template = 'try:{body}\n{handlers}'
    subparts = [('body', Body), ('handlers', ExceptHandlers)]

class ArgList(DynamicNode):
    child_type = Arg

class Decorator(StaticNode):
    template = '@{value}'
    subparts = [('value', Expr)]

class DecoratorList(DynamicNode):
    template = '{children}'
    child_type = Decorator
    delimiter = '\n'

    def render(self, wrapper=empty_wrapper):
        if len(self) == 0:
            self.template = ''
        else:
            self.template = '{children}\n'
        return DynamicNode.render(self, wrapper)

class FunctionDef(Statement):
    template = '{decorators}def {name}({args}):{body}'
    subparts = [('decorators', DecoratorList), ('name', Name), ('args', ArgList), ('body', Body)]

class Lambda(Expr):
    template = 'lambda {args}: {body}'
    subparts = [('args', ArgList), ('body', Expr)]

class ClassDef(Statement):
    template = 'class {name}({bases}):{body}'
    subparts = [('name', Name), ('bases', ExprList), ('body', Body)]

class Return(Statement):
    template = 'return {value}'
    subparts = [('value', Expr)]

class Pass(Statement):
    template = 'pass'
    subparts = []

class Continue(Statement):
    template = 'continue'
    subparts = []

class Break(Statement):
    template = 'break'
    subparts = []

# TODO: add message
class Assert(Statement):
    template = 'assert {value}'
    subparts = [('value', Expr)]

class Raise(Statement):
    template = 'raise {value}'
    subparts = [('value', Expr)]

class ListComp(Expr):
    template = '[{elt} for {target} in {iter}]'
    subparts = [('elt', Expr), ('target', Expr), ('iter', Expr)]

class DictComp(Expr):
    template = '{{{key}: {value} for {target} in {iter}}}'
    subparts = [('key', Expr), ('value', Expr), ('target', Expr), ('iter', Expr)]

class GeneratorExp(Expr):
    template = '({elt} for {target} in {iter})'
    subparts = [('elt', Expr), ('target', Expr), ('iter', Expr)]

binop_char_by_class = {
    ast.Add: '+',
    ast.Mult: '*',
    ast.Div: '/',
    ast.Sub: '-',
    ast.Pow: '**',
    ast.RShift: '>>',
    ast.LShift: '<<',
    ast.BitOr: '|',
    ast.BitAnd: '&',
    ast.BitXor: '^',

    ast.Or: 'or',
    ast.And: 'and',
}

compop_char_by_class = {
    ast.Eq: '==',
    ast.NotEq: '!=',
    ast.Is: 'is',
    ast.IsNot: 'is not',
    ast.In: 'in',
    ast.Lt: '<',
    ast.Gt: '>',
    ast.LtE: '<=',
    ast.GtE: '>=',
}

uop_char_by_class = {
    ast.Not: 'not',
    ast.Invert: '~',
    ast.USub: '-',
}

def convert(node):
    if type(node) in binop_char_by_class:
        return Op([binop_char_by_class[type(node)]])
    elif type(node) in uop_char_by_class:
        return UOp([uop_char_by_class[type(node)]])
    elif type(node) in compop_char_by_class:
        return Op([compop_char_by_class[type(node)]])
    elif isinstance(node, ast.Expr):
        return convert(node.value)
    elif isinstance(node, ast.Str):
        return Str([node.s])
    elif isinstance(node, ast.Bytes):
        return Bytes([node.s.decode()])
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
        import_level = ImportLevelList(ImportLevel() for i in range(node.level))
        return ImportFrom([import_level, Name([node.module or '']), NameList(Name([alias.name]) for alias in node.names)])
    elif isinstance(node, ast.Assign):
        return Assign([ExprList(map(convert, node.targets)), convert(node.value)])
    elif isinstance(node, ast.For):
        return For([convert(node.target), convert(node.iter), Body(map(convert, node.body))])
    elif isinstance(node, ast.With):
        alias = node.items[0].optional_vars
        if alias:
            return With([convert(node.items[0].context_expr), convert(alias), Body(map(convert, node.body))])
        else:
            return With([convert(node.items[0].context_expr), Body(map(convert, node.body))])
    elif isinstance(node, ast.Name):
        return Name([node.id])
    elif isinstance(node, ast.NameConstant):
        return Name([str(node.value)])
    elif isinstance(node, ast.Attribute):
        return Attribute([convert(node.value), Name([node.attr])])
    elif isinstance(node, ast.BoolOp):
        operator = convert(node.op)
        operands = ExprList(map(convert, node.values))
        return BoolOp([operator, operands])
    elif isinstance(node, ast.BinOp):
        return BinOp([convert(node.left), convert(node.op), convert(node.right)])
    elif isinstance(node, ast.UnaryOp):
        return UnaryOp([convert(node.op), convert(node.operand)])
    elif isinstance(node, ast.Compare):
        # TODO: support chained comparisons
        return BinOp([convert(node.left), convert(node.ops[0]), convert(node.comparators[0])])
    elif isinstance(node, ast.Subscript):
        return Subscript([convert(node.value), convert(node.slice)])
    elif isinstance(node, ast.Index):
        return convert(node.value)
    elif isinstance(node, ast.Slice):
        lower = node.lower or ast.NameConstant(value='None')
        upper = node.upper or ast.NameConstant(value='None')
        if node.step:
            return SliceWithStep([convert(lower), convert(upper), convert(node.step)])
        else:
            return Slice([convert(lower), convert(upper)])
    elif isinstance(node, ast.List):
        return List(map(convert, node.elts))
    elif isinstance(node, ast.Tuple):
        return Tuple(map(convert, node.elts))
    elif isinstance(node, ast.While):
        return While([convert(node.test), Body(map(convert, node.body))])
    elif isinstance(node, ast.If):
        if_list = []
        while True:
            body = Body(map(convert, node.body))
            test = convert(node.test)
            if_list.append(If([test, body]))
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                node = node.orelse[0]
            else:
                break

        if len(node.orelse) == 0:
            return FullIf([IfChain(if_list)])
        else:
            else_body = Body(map(convert, node.orelse))
            return FullIf([IfChain(if_list), Else([else_body])])
    elif isinstance(node, ast.IfExp):
        return IfExp([convert(node.body), convert(node.test), convert(node.orelse)])
    elif isinstance(node, ast.Dict):
        items = [DictItem([convert(key), convert(value)]) for key, value in zip(node.keys, node.values)]
        return Dict(items)
    elif isinstance(node, ast.Try):
        handlers_list = []
        for handler in node.handlers:
            #e = ExceptHandler([convert(handler.type), convert(handler.name), Body(map(convert, handler.body))])
            e = ExceptHandler([convert(handler.type or ast.Name(id='None', ctx=ast.Load())), Body(map(convert, handler.body))])
            handlers_list.append(e)
        return Try([Body(map(convert, node.body)), ExceptHandlers(handlers_list)])
    elif isinstance(node, ast.FunctionDef):
        decorators = DecoratorList(Decorator([convert(value)]) for value in node.decorator_list)
        args = []
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        for arg_node, default in zip(node.args.args, defaults):
            if default:
                args.append(Arg([Name([arg_node.arg]), convert(default)]))
            else:
                args.append(Name([arg_node.arg]))
        return FunctionDef([decorators, Name([node.name]), ArgList(args), Body(map(convert, node.body))])
    elif isinstance(node, ast.Lambda):
        args = []
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        for arg_node, default in zip(node.args.args, defaults):
            if default:
                args.append(Arg([Name([arg_node.arg]), convert(default)]))
            else:
                args.append(Name([arg_node.arg]))
        return Lambda([ArgList(args), convert(node.body)])
    elif isinstance(node, ast.ClassDef):
        return ClassDef([Name([node.name]), ExprList(map(convert, node.bases)), Body(map(convert, node.body))])
    elif isinstance(node, ast.Return):
        return Return([convert(node.value or ast.Name(id='None', ctx=ast.Load()))])
    elif isinstance(node, ast.Pass):
        return Pass()
    elif isinstance(node, ast.Continue):
        return Continue()
    elif isinstance(node, ast.Break):
        return Break()
    elif isinstance(node, ast.ListComp):
        return ListComp([convert(node.elt), convert(node.generators[0].target), convert(node.generators[0].iter)])
    elif isinstance(node, ast.DictComp):
        return DictComp([convert(node.key), convert(node.value), convert(node.generators[0].target), convert(node.generators[0].iter)])
    elif isinstance(node, ast.GeneratorExp):
        return GeneratorExp([convert(node.elt), convert(node.generators[0].target), convert(node.generators[0].iter)])
    elif isinstance(node, ast.Assert):
        return Assert([convert(node.test)])
    elif isinstance(node, ast.Raise):
        return Raise([convert(node.exc)])
    elif isinstance(node, ast.AugAssign):
        return AugAssign([convert(node.target), convert(node.op), convert(node.value)])

    raise TypeError('Unknown node type', node)

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
