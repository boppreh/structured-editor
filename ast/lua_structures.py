"""
As the Lua parser works through a piece of text, it groups tokens into high
level structures. This is where those structures are declared.

A successfully parsed Lua program should only contain instances from these
classes in its abstract syntax tree.
"""
from .structures import *

class TableItem(StaticNode):
    pass

class Expression(TableItem, Statement):
    """ Abstract class for expressions that can be used as values. """
    template = 'ABSTRACT EXPRESSION'
    @classmethod
    def default(cls):
        if cls == Expression:
            return Identifier.default()
        else:
            return cls()

class Break(Statement):
    template = 'break'

class DoBlock(Statement):
    template = 'do{block}\nend'
    subparts = [('block', Block)]

class Constant(Expression):
    """ Literal string, number, nil, true or false. """
    subparts = [('value', str)]
    template = '{value}'
    token_rule = '\d+'

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0])

    @staticmethod
    def default():
        new = Constant(['0'])
        Node.defaulted.append(new)
        return new

class Identifier(Constant):
    """ A reference to an identifier. """
    token_rule = '[a-zA-Z_]\w+'
    @staticmethod
    def default():
        new = Identifier(['value'])
        Node.defaulted.append(new)
        return new

class String(Constant):
    """ Literal string. """
    template = '"{value}"'
    token_rule = '.+'

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0].replace('"', r'\"'))

    @staticmethod
    def default():
        new = String(['value'])
        Node.defaulted.append(new)
        return new

class ExpressionList(DynamicNode):
    """ Comma separated list of expressions ("foo, bar + 2, baz[1]"). """
    child_type = Expression
    @staticmethod
    def default(): return ExpressionList([Identifier.default()])

class NameList(DynamicNode):
    """ Comma separated list of names ("foo, bar, baz"). """
    child_type = Identifier
    @staticmethod
    def default(): return NameList([Identifier.default()])

class Assignment(Statement):
    template = '{left_side} = {right_side}'
    subparts = [('left_side', ExpressionList), ('right_side', ExpressionList)]

class LocalVar(Assignment):
    """ Variable declaration with "local" modifier. """
    subparts = [('names', NameList), ('values', ExpressionList)]
    template = 'local {names} = {values}'

    def render(self, wrapper=empty_wrapper):
        if len(self) == 1:
            self.template = LocalVar.template.replace('= {values}', '')
        else:
            self.template = LocalVar.template
        return super(LocalVar, self).render(wrapper)

class FieldAssignment(TableItem):
    template = '{left_side} = {right_side}'
    subparts = [('left_side', ExpressionList), ('right_side', ExpressionList)]

class Table(DynamicNode, Expression):
    """
    Table declaration. When printing, line breaks are inserted as necessary.
    """
    delimiter = ', '
    child_type = TableItem
    template = '{{{children}}}'

class FunctionName(DynamicNode):
    """
    Dot separated names, used in function declarations.
    """
    delimiter = '.'
    child_type = Identifier
    @staticmethod
    def default(): return FunctionName([Identifier.default()])

class ParameterList(NameList):
    @staticmethod
    def default(): return ParameterList([])

class NamedFunction(Statement):
    """
    Declaration of a named function, in contrast to an anonymous function.
    """
    template = 'function {name}({parameters}){body}\nend'
    subparts = [('name', FunctionName), ('parameters', ParameterList), ('body', Block)]

class LocalFunction(Statement):
    """ Specialization of a named function with the local modifier.  """
    template = 'local ' + NamedFunction.template
    subparts = [('name', Identifier), ('parameters', ParameterList), ('body', Block)]

class AnonFunction(Expression):
    """ Anonymous function declaration. Can be used as expression value. """
    template = 'function ({parameters}){body}\nend'
    subparts = [('parameters', NameList), ('body', Block)]

class SuffixOperator(Node): pass

class FunctionCall(DynamicNode, SuffixOperator):
    """ Simple function call with variable number of arguments. """
    child_type = Expression
    template = '({children})'

    def __init__(self, toks):
        super(FunctionCall, self).__init__(toks)

class ListAccess(StaticNode, SuffixOperator):
    """ Simple list access using the bracket notation ("[exp]"). """
    subparts = [('index', Expression)]
    template = '[{index}]'

class ForIn(Statement):
    """ "for item in list do" control structure. """
    subparts = [('item', NameList), ('iterator', ExpressionList), ('body', Block)] 
    template = 'for {item} in {iterator} do{body}\nend'

class For(Statement):
    subparts = [('item', Identifier), ('range', ExpressionList), ('body', Block)]
    template = 'for {item} = {range} do{body}\nend'

class RepeatUntil(Statement):
    """ "for item in list do" control structure. """
    subparts = [('body', Block), ('condition', Expression)] 
    template = 'repeat{body}\nuntil {condition}'

class While(Statement):
    """ "while condition do" control structure. """
    subparts = [('condition', Expression), ('body', Block)]
    template = 'while {condition} do{body}\nend'

class Else(StaticNode):
    """ The 'else' clause of a conditional. """
    subparts = [('body', Block)]
    template = '\nelse{body}'

class If(StaticNode):
    """ The condition/body pair of an 'if'/'elseif' control structure. """
    subparts = [('condition', Expression), ('body', Block)]
    template = 'if {condition} then{body}'

    def render(self, wrapper=empty_wrapper):
        if self.parent.index(self) != 0:
            self.template = 'else' + If.template
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
    template = '{if_chain}{else}\nend'
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

class Return(DynamicNode, Statement):
    """ A return statement, with zero or more expression returned. """
    child_type = Expression
    template = 'return {children}'

    @staticmethod
    def default():
        return Return()


class Operator(StaticNode):
    """ Class for binary and unary operators such as +, and, ^ and not.  """
    subparts = [('value', object)]
    template = '{value}'
    token_rule = '[#^*/%+-.<>=~]'

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0])

    @staticmethod
    def default():
        return Operator(['+'])

class BinOp(Expression):
    """
    Expression with binary operator, including the left_ and right_side and
    the operator itself.
    """
    subparts = [('left_side', Expression),
                ('operator', Operator),
                ('right_side', Expression)]
    template = '{left_side} {operator} {right_side}'

    def __init__(self, toks):
        super(BinOp, self).__init__(toks[0])

    @staticmethod
    def default():
        return BinOp([[Identifier.default(),
                       Operator.default(),
                       Identifier.default()]])

    def render(self, wrapper=empty_wrapper):
        if isinstance(self.parent, Expression):
            self.template = '(' + BinOp.template + ')'
        else:
            self.template = BinOp.template
        return super(BinOp, self).render(wrapper)

class UnoOp(Expression):
    """
    Expression with unary operator, including the right_side and the operator
    itself.
    """
    subparts = [('operator', Operator),
                ('right_side', Expression)]
    template = '{operator}{right_side}'

    def __init__(self, toks):
        super(UnoOp, self).__init__(toks[0])

    @staticmethod
    def default():
        return UnoOp([[Operator.default(), Identifier.default()]])

class DotAccess(DynamicNode, Expression):
    child_type = Expression
    delimiter = '.'
    template = '{children}'

    def __init__(self, toks):
        toks = filter(lambda t: type(t) != Operator, toks[0])
        super(DotAccess, self).__init__(toks)

class ExpWithSuffix(UnoOp):
    subparts = [('right_side', Expression),
                ('operator', SuffixOperator)]
    template = '{right_side}{operator}'

if __name__ == '__main__':
    from lua_parser import parseFile, parseString
    #print parseString('if (1) then print("oi") elseif "oi" then print("bye") end')
    #print parseFile('tests/1.lua')
