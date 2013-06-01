"""
Module for parsing Lua programs with pyparsing. The abstract syntax tree
returned is composed of structures from the structures.py module.
"""

from pyparsing import *
from lua_structures import *

keywords = ['if', 'elseif', 'else', 'for', 'while', 'end', 'do', 'then', 'and',
            'not', 'or', 'break', 'goto', 'while', 'repeat', 'until',
            'function', 'local', 'return', 'nil', 'false', 'true', 'in']
name = ~MatchFirst(map(Keyword, keywords)) + Word(alphas + '_', alphanums + '_',
                                                  asKeyword=True)
# Constants.
number = Word(nums, asKeyword=True)
string = quotedString
true_ = Keyword('true')
false_ = Keyword('false')
nil_ = Keyword('nil')
ellipsis = Literal('...')

def registerClass(symbol, class_):
    class_.symbol = symbol
    symbol.addParseAction(class_)
    return symbol


# Constants' respective classes.
registerClass(name, Identifier)
registerClass(string, String).addParseAction(removeQuotes)
registerClass(number, Constant)
registerClass(nil_, Constant)
registerClass(true_, Constant)
registerClass(false_, Constant)
registerClass(ellipsis, Identifier)

# Main structures' classes.
block = registerClass(Forward(), Block)
doblock = registerClass(Forward(), DoBlock)
assignment = registerClass(Forward(), Assignment)
tableconstructor = registerClass(Forward(), Table)
fieldAssignment = registerClass(Forward(), FieldAssignment)
localvar = registerClass(Forward(), LocalVar)
namedfunc = registerClass(Forward(), NamedFunction)
localfunc = registerClass(Forward(), LocalFunction)
function = registerClass(Forward(), AnonFunction)
parlist = registerClass(Forward(), ParameterList)
functioncall = registerClass(Forward(), FunctionCall)
var = registerClass(Forward(), Variable)
listAccess = registerClass(Forward(), ListAccess)
prefixexp = registerClass(Forward(), make_prefixexp)
for_ = registerClass(Forward(), For)
forin = registerClass(Forward(), ForIn)
whilestat = registerClass(Forward(), While)
ifstat = registerClass(Forward(), FullIf)
mainif = registerClass(Forward(), If)
elsifstat = registerClass(Forward(), If)
elsestat = registerClass(Forward(), Else)
retstat = registerClass(Forward(), Return)
explist = registerClass(Forward(), ExpressionList)
repeatuntil = registerClass(Forward(), RepeatUntil)
funcname = registerClass(Forward(), FunctionName)
namelist = registerClass(Forward(), NameList)

# Intermediary structures.
exp = Forward()
Expression.symbol = exp
stat = Forward()
Statement.symbol = stat

varOrExp = Forward()
nameAndArgs = Forward()
varSuffix = Forward()
args = Forward()
funcbody = Forward()
fieldlist = Forward()
field = Forward()
fieldsep = Forward()

# Symbols (suppress means it is considered during the parsing, but is not sent
# to the structures' classes because their presence is implicit).
semicolon = Optional(Suppress(';'))
dot = Suppress(Literal('.'))
comma = Suppress(Literal(','))
colon = Suppress(Literal(':'))
open_parens = Suppress(Literal('('))
close_parens = Suppress(Literal(')'))
open_brackets = Suppress(Literal('['))
close_brackets = Suppress(Literal(']'))
open_curly = Suppress(Literal('{'))
close_curly = Suppress(Literal('}'))
equals = Suppress(Literal('='))

# Keywords.
function_ = Suppress(Keyword('function'))
return_ = Suppress(Keyword('return'))
break_ = Keyword('break')
end_ = Suppress(Keyword('end'))
while_ = Suppress(Keyword('while'))
do_ = Suppress(Keyword('do'))
repeat_ = Suppress(Keyword('repeat'))
until_ = Suppress(Keyword('until'))
if_ = Suppress(Keyword('if'))
elseif_ = Suppress(Keyword('elseif'))
then_ = Suppress(Keyword('then'))
else_ = Suppress(Keyword('else'))
forkeyword = Suppress(Keyword('for'))
local_ = Suppress(Keyword('local'))
in_ = Suppress(Keyword('in'))

# Boolean keywords.
not_ = Keyword('not')
and_ = Keyword('and')
or_ = Keyword('or')

# Grammar.
block << (ZeroOrMore(stat + semicolon) + Optional(retstat + semicolon))
retstat << (return_ + delimitedList(exp) | break_)
funcname << (delimitedList(name, dot) + Optional(colon + name))
namelist << delimitedList(name)
explist << delimitedList(exp)
var << ((name | open_parens + exp + close_parens + varSuffix) +
        ZeroOrMore(varSuffix))
prefixexp << (varOrExp + ZeroOrMore(nameAndArgs))
functioncall << (varOrExp + OneOrMore(nameAndArgs))
varOrExp << (var | open_parens + exp + close_parens)
nameAndArgs << (Group(Optional(colon + name)) + args)
listAccess << (open_brackets + exp + close_brackets)
varSuffix << (ZeroOrMore(nameAndArgs) +
              (listAccess | dot + name))
args << (open_parens + (explist | Group(empty)) + close_parens |
         Group(tableconstructor) | Group(string))
function << (function_ + funcbody)
funcbody << (open_parens + parlist + close_parens + block + end_)
parlist << Optional(delimitedList(name) + Optional(comma + ellipsis) | ellipsis)
tableconstructor << (open_curly + (fieldlist | empty) + close_curly)
fieldlist << (delimitedList(field, fieldsep) + Optional(fieldsep))
fieldAssignment << (Group(open_brackets + exp + close_brackets | name) + equals + Group(exp))
field << (fieldAssignment | exp)
fieldsep << (comma | semicolon)

assignment << (Group(delimitedList(var)) + equals + explist)
localvar << (local_ + namelist + Optional(equals + explist))

namedfunc << (function_ + funcname + funcbody)

for_ << (forkeyword + name + equals + Group(exp + comma + exp + Optional(comma + exp)) + do_ + block + end_)
forin << (forkeyword + namelist + in_ + explist + do_ + block + end_)
whilestat<< (while_ + exp + do_ + block + end_)
ifstat << (Group(mainif + ZeroOrMore(elsifstat)) +
           Optional(elsestat) + end_ )
mainif << (if_ + exp + then_ + block)
elsifstat << (elseif_ + exp + then_ + block)
elsestat << (else_ + block)
repeatuntil << (repeat_ + block + until_ + exp)

localfunc << (local_ + function_ + name + funcbody)

doblock << (do_ + block + end_)

stat << (whilestat |
         repeatuntil |
         ifstat |
         for_ |
         forin |
         doblock |
         localfunc |
         localvar |
         assignment |
         namedfunc |
         functioncall)

# This part makes uses of a pyparsing functionality of automatically generating
# an operator grammar, with correct precedences.
# "enablepackrat" enables an important optimization for this type of grammar.
exp.enablePackrat()
operators = [
    (registerClass(Literal('^'), Operator), 2, opAssoc.LEFT, BinOp),
    (registerClass((not_ | '#' | '-'), Operator), 1, opAssoc.RIGHT, UnoOp),
    (registerClass(oneOf('* / %'), Operator), 2, opAssoc.LEFT, BinOp),
    (registerClass(oneOf('+ - ..'), Operator), 2, opAssoc.LEFT, BinOp),
    (registerClass(oneOf('< > <= >= ~= =='), Operator), 2, opAssoc.LEFT, BinOp),
    (registerClass((or_ | and_), Operator), 2, opAssoc.LEFT, BinOp),
]
exp << operatorPrecedence(nil_ | false_ | true_ | '...' | number | string |
                          function | prefixexp | tableconstructor, operators)


import re

def parse_string(string):
    """
    Parses a Lua program from a string.
    """
    return block.parseString(re.sub(r'--.+', '', string), parseAll=True)[0]

import lua_structures, inspect
all_classes = inspect.getmembers(lua_structures, inspect.isclass)
structures = [cls for name, cls in all_classes]

if __name__ == '__main__':
    pass
    #print parseString('local function a(a) print() end')
    #print parseFile('../lua_test_files/full.lua')
    #print(parseString(str(parseFile('tests/1.lua'))))
    #from editor import Editor
    #print assignment.parseString('a = 5')
    #print assignment.parseString('asdf, fdsa = 5, (1 + 2)')[0]
