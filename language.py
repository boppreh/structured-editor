try:
    import configparser as ConfigParser
except:
    import ConfigParser
import re, os
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE

node_name_regex = r'(\w+)(?:\((\w+)\))?'
node_rule_regex = r'(\w+\*|/[^/]+/|(?:\w+ *)+|\?)'

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

class ListNode(list):
    def __init__(self, value, type_):
        self.type_ = type_
        list.__init__(self, value)

    def __str__(self):
        children = map(str, self)
        return self.type_.output_template.format(', '.join(children))

class DictNode(dict):
    def __init__(self, value, type_):
        self.type_ = type_
        dict.__init__(self, value)

    def __str__(self):
        return self.type_.output_template.format(*map(str, self.values()))

class StrNode(str):
    def __new__(cls, value, type_):
        obj = str.__new__(cls, value)
        obj.type_ = type_
        return obj

    def __str__(self):
        return self.type_.output_template.format(str.__str__(self))

class Language(object):
    def __init__(self, types, parser):
        self.types = types
        self.parser = parser

    def convert_tree(self, root):
        type_ = self.types[root.tag]

        if isinstance(type_.rule, str):
            node = StrNode(root.text, type_)
        elif isinstance(type_.rule, NodeType):
            children = map(self.convert_tree, root)
            node = ListNode(children, type_)
        else:
            children = {i: self.convert_tree(child)
                        for i, child in enumerate(root)}
            node = DictNode(children, type_)

        return node

    def parse_xml(self, xml):
        return self.convert_tree(ET.fromstring(xml))

    def parse(self, text):
        process = Popen(['python', self.parser], stdout=PIPE, stdin=PIPE)
        stdout, stderr = process.communicate(text)
        return self.parse_xml(stdout)

    
def parse_grammar(rule_pairs):
    nodes = {}
    for node_name, rule in rule_pairs:
        name, parent_name = re.match(node_name_regex, node_name).groups()
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

def read_language(language):
    parser_path = os.path.join('languages', language, 'parser.py')
    config_path = os.path.join('languages', language, 'config.ini')
    assert os.path.exists(parser_path) and os.path.exists(config_path)

    config = ConfigParser.RawConfigParser()
    config.read(config_path)
    types = parse_grammar(config.items('Composition Rules'))

    for n in types.values():
        if n.rule is None:
            continue

        n.default = ET.fromstring(config.get('Defaults', n.name))
        n.hotkey = config.get('Hotkeys', n.name)
        n.style = config.get('Style', n.name)

        n.output_template = config.get('Output Templates', n.name)
        try:
            n.display_template = config.get('Display Templates', n.name)
        except ConfigParser.NoOptionError:
            n.display_template = n.output_template

    return Language(types, parser_path)

languages = {}
for language in os.listdir('languages'):
    languages[language] = read_language(language)

if __name__ == '__main__':
    text = open('test_files/1.json').read()
    print(languages['json'].parse(text))
