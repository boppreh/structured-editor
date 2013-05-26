"""
As the Lua parser works through a piece of text, it groups tokens into high
level structures. This is where those structures are declared.

A successfully parsed Lua program should only contain instances from these
classes in its abstract syntax tree.
"""
import string
from structures import *

class Expression(StaticNode):
    """ Abstract class for expressions that can be used as values. """
    @staticmethod
    def default(): return Identifier.default()

class DoBlock(Statement):
    abstract = False
    template = 'do{block}\nend'
    subparts = [('block', Block)]

class Constant(Expression):
    """ Literal string, number, nil, true or false. """
    abstract = False
    subparts = [('value', str)]
    template = '{value}'
    alphabet = string.digits

    def render(self, wrapper=empty_wrapper):
        return wrapper(self).format(value=self.contents[0])

class Identifier(Constant):
    """ A reference to an identifier. """
    abstract = False
    alphabet = string.lowercase + string.digits + '_'
    @staticmethod
    def default():
        new = Identifier(['value'])
        Node.defaulted.append(new)
        return new

class String(Constant):
    """ Literal string. """
    template = '"{value}"'
    abstract = False
    alphabet = [chr(i) for i in range(256)]

class ExpressionList(DynamicNode):
    """ Comma separated list of expressions ("foo, bar + 2, baz[1]"). """
    abstract = False
    child_type = Expression
    @staticmethod
    def default(): return ExpressionList([Identifier.default()])

class NameList(DynamicNode):
    """ Comma separated list of names ("foo, bar, baz"). """
    abstract = False
    child_type = Identifier
    @staticmethod
    def default(): return NameList([Identifier.default()])

class Assignment(Statement):
    abstract = False
    template = '{left_side} = {right_side}'
    subparts = [('left_side', ExpressionList), ('right_side', ExpressionList)]

class LocalVar(Assignment):
    """ Variable declaration with "local" modifier. """
    abstract = False
    subparts = [('names', NameList), ('values', ExpressionList)]
    template = 'local {names} = {values}'

    def render(self, wrapper=empty_wrapper):
        if len(self) == 1:
            self.template = LocalVar.template.replace('= {values}', '')
        else:
            self.template = LocalVar.template
        return super(LocalVar, self).render(wrapper)

class Table(DynamicNode, Expression):
    """
    Table declaration. When printing, line breaks are inserted as necessary.
    """
    abstract = False
    delimiter = ', '
    child_type = StaticNode
    template = '{{{children}}}'

class FunctionName(DynamicNode):
    """
    Dot separated names, used in function declarations.
    """
    abstract = False
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
    abstract = False
    template = 'function {name}({parameters}){body}\nend'
    subparts = [('name', FunctionName), ('parameters', ParameterList), ('body', Block)]

class LocalFunction(Statement):
    """ Specialization of a named function with the local modifier.  """
    abstract = False
    template = 'local ' + NamedFunction.template
    subparts = [('name', Identifier), ('parameters', ParameterList), ('body', Block)]

class AnonFunction(Expression):
    """ Anonymous function declaration. Can be used as expression value. """
    abstract = False
    template = 'function ({parameters}){body}\nend'
    subparts = [('parameters', NameList), ('body', Block)]

class ColonName(StaticNode):
    abstract = False
    subparts = [('name', Identifier)]
    template = ':{name}'

    def render(self, wrapper=empty_wrapper):
        if len(self):
            self.template = ColonName.template
        else:
            self.template = ''
        return super(ColonName, self).render(wrapper)

class FunctionCall(Expression, Statement):
    """
    A function call, possibly with method call syntax ("a:b(params)").
    """
    abstract = False
    template = '{name}{colon_name}({parameters})'
    subparts = [('name', Expression),
                ('colon_name', ColonName),
                ('parameters', ExpressionList)]

    @staticmethod
    def default(): return FunctionCall([Expression.default(),
                                         ColonName([]),
                                         ExpressionList()])

class Variable(DynamicNode, Expression):
    """ Variable reference, possibly with chained accesses ("(a).b[0].c.d"). """
    abstract = False
    child_type = Expression
    delimiter = '.'

class ListAccess(Expression):
    """ Simple list access using the bracket notation ("[exp]"). """
    abstract = False
    subparts = [('value', Expression)]
    template = '[{value}]'

def make_prefixexp(toks):
    """
    To remove left recursion from the grammar, the prefixexp non-terminal was
    created. This method converts a prefixexp into a function call or regular
    expression.
    """
    assert len(toks), 'Tokens for prefixexp must have at least one element; {} found.'.format(len(toks))
    if len(toks) == 1:
        return toks[0]
    else:
        return FunctionCall(toks)

class ForIn(Statement):
    """ "for item in list do" control structure. """
    abstract = False
    subparts = [('item', NameList), ('iterator', ExpressionList), ('body', Block)] 
    template = 'for {item} in {iterator} do{body}\nend'

class For(Statement):
    abstract = False
    subparts = [('item', Identifier), ('range', ExpressionList), ('body', Block)]
    template = 'for {item} = {range} do{body}\nend'

class RepeatUntil(Statement):
    """ "for item in list do" control structure. """
    abstract = False
    subparts = [('body', Block), ('condition', Expression)] 
    template = 'repeat{body}\nuntil {condition}'

class While(Statement):
    """ "while condition do" control structure. """
    abstract = False
    subparts = [('condition', Expression), ('body', Block)]
    template = 'while {condition} do{body}\nend'

class Else(StaticNode):
    """ The 'else' clause of a conditional. """
    abstract = False
    subparts = [('body', Block)]
    template = '\nelse{body}'

class If(Else):
    """ The condition/body pair of an 'if'/'elseif' control structure. """
    abstract = False
    subparts = [('condition', Expression), ('body', Block)]
    template = 'if {condition} then{body}'

class IfChain(DynamicNode):
    """
    Structure for the first 'if' and the chain of 'elseif' that follow.
    """
    abstract = False
    child_type = If
    delimiter = '\nelse'

    @staticmethod
    def default():
        return IfChain([If.default()])

class FullIf(Statement):
    """ If control structure, including related elseifs and elses. """
    abstract = False
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
    abstract = False
    child_type = ExpressionList
    template = 'return {children}'

class Operator(Constant):
    """ Class for binary and unary operators such as +, and, ^ and not.  """

class BinOp(Expression):
    """
    Expression with binary operator, including the left_ and right_side and
    the operator itself.
    """
    abstract = False
    subparts = [('left_side', Expression),
                ('operator', Operator),
                ('right_side', Expression)]
    template = '{left_side} {operator} {right_side}'

    def __init__(self, toks):
        super(BinOp, self).__init__(toks[0])

class UnoOp(Expression):
    """
    Expression with unary operator, including the right_side and the operator
    itself.
    """
    abstract = False
    subparts = [('operator', Operator),
                ('right_side', Expression)]
    template = '{operator}{right_side}'

    def __init__(self, toks):
        super(UnoOp, self).__init__(toks[0])


if __name__ == '__main__':
    from lua_parser import parseFile, parseString
    #print parseString('if (1) then print("oi") elseif "oi" then print("bye") end')
    print parseFile('tests/1.lua')
