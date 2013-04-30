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

# Constants' respective classes.
name.setParseAction(Identifier)
string.setParseAction(String)
number.setParseAction(Constant)
nil_.setParseAction(Constant)
true_.setParseAction(Constant)
false_.setParseAction(Constant)
ellipsis.setParseAction(Identifier)

# Main structures' classes.
block = Forward().setParseAction(Block)
assignment = Forward().setParseAction(Assignment)
tableconstructor = Forward().setParseAction(Table)
fieldAssignment = Forward().setParseAction(Assignment)
localvar = Forward().setParseAction(LocalVar)
namedfunc = Forward().setParseAction(NamedFunction)
localfunc = Forward().setParseAction(LocalFunction)
function = Forward().setParseAction(AnonFunction)
parlist = Forward().setParseAction(NameList)
functioncall = Forward().setParseAction(FunctionCall)
var = Forward().setParseAction(Variable)
listAccess = Forward().setParseAction(ListAccess)
prefixexp = Forward().setParseAction(make_prefixexp)
forin = Forward().setParseAction(ForIn)
whilestat = Forward().setParseAction(While)
ifstat = Forward().setParseAction(FullIf)
mainif = Forward().setParseAction(If)
elsifstat = Forward().setParseAction(If)
elsestat = Forward().setParseAction(Else)
retstat = Forward().setParseAction(Return)
explist = Forward().setParseAction(ExpressionList)

# Intermediary structures.
exp = Forward()
stat = Forward()
funcname = Forward()
namelist = Forward()
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
repeat_ = Keyword('repeat')
until_ = Suppress(Keyword('until'))
if_ = Suppress(Keyword('if'))
elseif_ = Suppress(Keyword('elseif'))
then_ = Suppress(Keyword('then'))
else_ = Suppress(Keyword('else'))
for_ = Suppress(Keyword('for'))
local_ = Suppress(Keyword('local'))
in_ = Suppress(Keyword('in'))

# Boolean keywords.
not_ = Keyword('not')
and_ = Keyword('and')
or_ = Keyword('or')

# Grammar.
block << (ZeroOrMore(stat + semicolon) + Optional(retstat + semicolon))
retstat << (return_ + Optional(explist) | break_)
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
         tableconstructor | string)
function << (function_ + funcbody)
funcbody << (open_parens + parlist + close_parens + block + end_)
parlist << Optional(namelist + Optional(comma + ellipsis) | ellipsis)
tableconstructor << (open_curly + Optional(fieldlist) + close_curly)
fieldlist << (delimitedList(Group(field), fieldsep) + Optional(fieldsep))
fieldAssignment << ((open_brackets + exp + close_brackets | name) + equals + exp)
field << (fieldAssignment | exp)
fieldsep << (comma | semicolon)

assignment << (Group(delimitedList(var)) + equals + explist)
localvar << (local_ + Group(namelist) + Optional(equals + explist))

namedfunc << (function_ + Group(funcname) + funcbody)

forin << (for_ + Group(namelist) + in_ + explist + do_ + block + end_)
whilestat<< (while_ + exp + do_ + block + end_)
ifstat << (Group(mainif + ZeroOrMore(elsifstat)) +
           Optional(elsestat) + end_ )
mainif << (if_ + exp + then_ + block)
elsifstat << (elseif_ + exp + then_ + block)
elsestat << (else_ + block)

localfunc << (local_ + function_ + name + funcbody)

stat << (whilestat |
         repeat_ + block + until_ + exp |
         ifstat |
         for_ + name + equals + exp + comma + exp +
             Optional(comma + exp) + do_ + block + end_ |
         forin |
         do_ + block + end_ |
         localfunc |
         localvar |
         assignment |
         namedfunc |
         functioncall)

# This part makes uses of a pyparsing functionality of automatically generating
# an operator grammar, with correct precedences.
# "enablepackrat" enables an important optimization for this type of grammar.
exp.enablePackrat()
exp << operatorPrecedence(nil_ |
                          false_ |
                          true_ |
                          '...' |
                          number |
                          string |
                          function |
                          prefixexp |
                          tableconstructor,
                          [
                           ('^', 2, opAssoc.LEFT, BinOp),
                           ((not_ | '#' | '-'), 1, opAssoc.RIGHT, UnoOp),
                           (oneOf('* / %'), 2, opAssoc.LEFT, BinOp),
                           (oneOf('+ - ..'), 2, opAssoc.LEFT, BinOp),
                           (oneOf('< > <= >= ~= =='), 2, opAssoc.LEFT, BinOp),
                           ((or_ | and_), 2, opAssoc.LEFT, BinOp),
                          ])


import re

def parseString(string):
    """
    Parses a Lua program from a string.
    """
    return block.parseString(re.sub(r'--.+', '', string), parseAll=True)[0]

def parseFile(filename):
    """
    Parses a Lua program from the contents of a file in a given path.
    """
    return parseString(open(filename).read())

if __name__ == '__main__':
    #print(parseString(str(parseFile('tests/1.lua'))))
    #print parseFile('tests/1.lua')
    #from editor import Editor
    #print assignment.parseString('a = 5')
    print assignment.parseString('asdf, fdsa = 5, (1 + 2)')[0]
