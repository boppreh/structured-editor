"""
As the Lua parser works through a piece of text, it groups tokens into high
level structures. This is where those structures are declared.

A successfully parsed Lua program should only contain instances from these
classes in its abstract syntax tree.
"""
from structures import *

import cgi
class Constant(Expression):
    """ Literal string, number, nil, true or false. """
    abstract = False
    template = '{value}'
    subparts = [('value', str)]

    def __str__(self):
        href = self.href_template.format(self.id)
        Node.global_dict[self.id] = self
        text = cgi.escape(str(self.dictionary['value']))
        full_text = href + text + '</a>'

        if self.str_wrapper:
            return self.str_wrapper(full_text)
        else:
            return full_text

class Identifier(Constant):
    """ A reference to an identifier. """
    abstract = False

class ExpressionList(StructureList):
    """ Comma separated list of expressions ("foo, bar + 2, baz[1]"). """
    abstract = False
    child_type = Expression

class NameList(StructureList):
    """ Comma separated list of names ("foo, bar, baz"). """
    abstract = False
    child_type = Identifier

class Assignment(Statement):
    abstract = False
    template = '{left_side} = {right_side}'
    subparts = [('left_side', ExpressionList), ('right_side', ExpressionList)]

class LocalVar(Assignment):
    """ Variable declaration with "local" modifier. """
    abstract = False
    template = 'local ' + Assignment.template

class Table(StructureList, Expression):
    """
    Table declaration. When printing, line breaks are inserted as necessary.
    """
    abstract = False
    delimiter = '\n\t'
    child_type = AbstractStructure
    template = '{{\n{children}\n\t}}'

    def __str__(self):
        # Tables with more items use one line per item.
        try:
            Block.increaseIndentation()
            return super(Table, self).__str__()
        finally:
            Block.decreaseIdentation()

class FunctionName(StructureList):
    """
    Dot separated names, used in function declarations. May end with colon
    and another name ("a.b.c:d")
    """
    abstract = False
    delimiter = '.'
    child_type = Identifier

class ParameterList(StructureList):
    """ List of parameter names in a function declaration. """
    abstract = False
    child_type = Identifier
    template = ' {children} '

class NamedFunction(Statement):
    """
    Declaration of a named function, in contrast to an anonymous function.
    """
    abstract = False
    template = 'function {name}({parameters})\n{body}\n\tend'
    subparts = [('name', FunctionName), ('parameters', ParameterList), ('body', Block)]

class LocalFunction(NamedFunction):
    """ Specialization of a named function with the local modifier.  """
    abstract = False
    template = 'local ' + NamedFunction.template

class AnonFunction(Expression):
    """ Anonymous function declaration. Can be used as expression value. """
    abstract = False
    template = 'function ({parameters})\n{body}\n\tend'
    subparts = [('parameters', ParameterList), ('body', Block)]

class FunctionCall(Expression, Statement):
    """
    A function call, possibly with method call syntax ("a:b(params)").
    """
    abstract = False
    template = '{name}({parameters})'
    subparts = [('name', Expression), ('parameters', ExpressionList)]

class Variable(StructureList, Expression):
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
    template = 'for {item} in {iterator} do\n{body}\n\tend'

class While(Statement):
    """ "while condition do" control structure. """
    abstract = False
    subparts = [('condition', Expression), ('body', Block)]
    template = 'while {condition} do\n{body}\n\tend'

class If(AbstractStructure):
    """ The condition/body pair of an 'if'/'elseif' control structure. """
    abstract = False
    subparts = [('condition', Expression), ('body', Block)]
    template = 'if {condition} then\n{body}'

class IfChain(StructureList):
    """
    Structure for the first 'if' and the chain of 'elseif' that follow.
    """
    abstract = False
    child_type = If
    delimiter = '\n\telse'

class Else(AbstractStructure):
    """ The 'else' clause of a conditional. """
    abstract = False
    subparts = [('body', Block)]
    template = 'else\n{body}'

class FullIf(Statement):
    """ If control structure, including related elseifs and elses. """
    abstract = False
    subparts = [('if_chain', IfChain),
                ('else', Else)]

    def update_template(self):
        if 'else' in self.dictionary:
            self.template = '{if_chain}\n\t{else}\n\tend'
        else:
            self.template = '{if_chain}\n\tend'

class Return(StructureList, Statement):
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
    subparts = [('left_side', ExpressionList),
                ('operator', Operator),
                ('right_side', ExpressionList)]
    template = '{left_side} {operator} {right_side}'

class UnoOp(Expression):
    """
    Expression with unary operator, including the right_side and the operator
    itself.
    """
    abstract = False
    subparts = [('operator', Operator),
                ('right_side', ExpressionList)]
    template = '{operator} {right_side}'


if __name__ == '__main__':
    from lua_parser import parseFile, parseString
    #print parseString('if (1) then print("oi") elseif "oi" then print("bye") end')
    print parseFile('tests/1.lua')
