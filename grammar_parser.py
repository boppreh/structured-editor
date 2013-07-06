import re
rule_regex = r'(\w+)(?:\((\w+)\))? = (\w+\*|/[^/]+/|(?:\w+ *)+|\?)'

class NodeType(object):
    def __init__(self, name, rule, parent):
        self.name = name
        self.rule = rule
        self.parent = parent

    def extends(self, other):
        if self == other:
            return True
        elif self.parent:
            return self.parent.extends(other)
        else:
            return False

    def __str__(self, rule='?'):
        if self.parent:
            parent = '(' + self.parent.name+ ')'
        else:
            parent = ''

        return '{}{} = {}'.format(self.name, parent, rule)

class ListNode(list):
    def __init__(self, value, type_):
        self.type_ = type_
        list.__init__(self, value)

class DictNode(dict):
    def __init__(self, value, type_):
        self.type_ = type_
        dict.__init__(self, value)

class StrNode(str):
    def __new__(cls, value, type_):
        obj = str.__new__(cls, value)
        obj.type_ = type_
        return obj
    
def parse_grammar(grammar_text):
    nodes = {}
    for name, parent_name, rule in re.findall(rule_regex, grammar_text):
        if parent_name:
            parent = nodes[parent_name]
        else:
            parent = None

        if rule == '?':
            rule = None
        elif rule.startswith('/'):
            rule = rule
        elif rule.endswith('*') or rule.endswith('+'):
            rule = nodes[rule[:-1]]
        else:
            rule = map(nodes.get, rule.split(' '))

        nodes[name] = NodeType(name, rule, parent)

    return nodes

def convert_tree(root, grammar):
    type_ = grammar[root.tag]

    if isinstance(type_.rule, str):
        node = StrNode(root.text, type_)
    elif isinstance(type_.rule, NodeType):
        children = [convert_tree(child, grammar) for child in root]
        node = ListNode(children, type_)
    else:
        children = {i: convert_tree(child, grammar)
                    for i, child in enumerate(root)}
        node = DictNode(children, type_)

    return node

import xml.etree.ElementTree as ET
def parse_tree(xml, grammar):
    return convert_tree(ET.fromstring(sample_xml), grammar)

grammar_sample = r"""
exp = ?
statement = ?
block = ?

constant(exp) = /\d+/
identifier(constant) = /[a-zA-Z_]\w*/
do(statement) = block
exp_list = exp*
assignment(statement) = exp_list exp_list
return(statement) = exp
"""

sample_xml = r"""
<block>
    <assignment>
        <exp_list>
            <constant>a</constant>
        </exp_list>
        <exp_list>
            <constant>b</constant>
        </exp_list>
    </assignment>
    <return><constant>5</constant></return>
</block>
"""

print(parse_tree(sample_xml, parse_grammar(grammar_sample)))
