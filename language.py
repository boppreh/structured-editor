try:
    import ConfigParser as configparser
except:
    import configparser
import re, os
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE

# Grammar regexes. Examples:
# assignment(statement) = expression expression
# parameters = expression*
# identifier(expression) = /[a-zA-Z_]w*/
node_name_regex = re.compile(r'^(\w+)(?:\((\w+)\))?$')

class NodeType(object):
    """
    Class for representing a node type, for example "Assignment" or
    "Expression". Each node type has a name, a formation rule and possibly
    another node type as parent.
    """
    def __init__(self, name, rule, parent):
        self.name = name
        self.rule = rule
        self.parent = parent

    def extends(self, other):
        """
        Returns if the "parent" chain of this node type reaches the given one.
        """
        if self == other:
            return True
        elif self.parent:
            return self.parent.extends(other)
        else:
            return False

class ListNode(list):
    """
    AST element for nodes that contain a variable number of other nodes. Its
    node type "rule" attribute defines what kind of node types are expected as
    children.
    """
    def __init__(self, value, type_):
        self.type_ = type_
        list.__init__(self, value)

    def __str__(self):
        children = map(str, self)
        return self.type_.output_template.format(', '.join(children))

class DictNode(dict):
    """
    AST element for nodes that contain a fixed number of other nodes. Its node
    type "rule" attribute define the type of each children, by position.

    The dictionary keys are numbers. A dictionary is used to disallow
    insertions and removals of elements.
    """
    def __init__(self, value, type_):
        self.type_ = type_
        dict.__init__(self, value)

    def __str__(self):
        return self.type_.output_template.format(*map(str, self.values()))

class StrNode(str):
    """
    AST element containing a single string value.
    """
    def __new__(cls, value, type_):
        obj = str.__new__(cls, value)
        obj.type_ = type_
        return obj

    def __str__(self):
        return self.type_.output_template.format(str.__str__(self))

class Language(object):
    """
    Class representing a supported language, with group of node types and
    parser.
    """
    def __init__(self, types, parser):
        self.types = types
        self.parser = parser

    def _convert_tree(self, root):
        """
        Converts an XML tree to a tree of ListNode, DictNode and StrNode
        elements with their types appropriately set.
        """
        type_ = self.types[root.tag]

        if isinstance(type_.rule, str):
            # Literal type, rule is regex.
            node = StrNode(root.text, type_)
        elif isinstance(type_.rule, NodeType):
            # List type, rule is child type.
            children = map(self._convert_tree, root)
            node = ListNode(children, type_)
        else:
            # List type, rule is list of children type.
            children = {i: self._convert_tree(child)
                        for i, child in enumerate(root)}
            node = DictNode(children, type_)

        return node

    def parse_xml(self, xml):
        """
        Parses an XML string and returns the equivalent AST with type
        annotations.
        """
        return self._convert_tree(ET.fromstring(xml))

    def parse(self, text):
        """
        Parses arbitrary text in this language into the equivalent AST with
        type annotations.
        """
        process = Popen(['python', self.parser], stdout=PIPE, stdin=PIPE)
        stdout, stderr = process.communicate(text)
        return self.parse_xml(stdout)

    
def parse_grammar(rule_pairs):
    """
    Converts a list of (name, rule) keypairs into a dictionary
    {name: NodeType}. "name" can extend other names by specifying the parent in
    parenthesis, and the rule must abstract ("?"), literal ("/regex/"),
    list-like ("expression*") or with a fixed number of known types
    ("name parameters body")
    """
    nodes = {}
    for node_name, rule in rule_pairs:
        name, parent_name = node_name_regex.match(node_name).groups()
        if parent_name:
            parent = nodes[parent_name]
        else:
            parent = None

        if rule == '?':
            # Abstract type.
            rule = None
        elif rule.startswith('/'):
            # Literal type, rule is regex.
            rule = rule[1:-1]
        elif rule.endswith('*') or rule.endswith('+'):
            # List type, rule is reference to one other type.
            rule = nodes[rule[:-1]]
        else:
            # Dict type, rule is list of references to other types.
            rule = map(nodes.get, rule.split(' '))

        nodes[name] = NodeType(name, rule, parent)

    return nodes

def merge_config(config):
    """
    From the configuration object for a given language, parses the grammar
    structure, defaults, hotkeys, styles and output and display templates.

    Returns the types dictionary {type_name: type_object} with types setup
    according to the configuration object.
    """
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
        except configparser.NoOptionError:
            n.display_template = n.output_template

    return types


def read_language(language):
    """
    Reads the configuration file for a given language and returns the Language
    object representing it.
    """
    parser_path = os.path.join('languages', language, 'parser.py')
    config_path = os.path.join('languages', language, 'config.ini')
    assert os.path.exists(parser_path) and os.path.exists(config_path)

    config = configparser.RawConfigParser()
    config.read(config_path)

    return Language(merge_config(config), parser_path)

def read_languages():
    return {language: read_language(language)
            for language in os.listdir('languages')}

if __name__ == '__main__':
    text = open('test_files/1.json').read()
    print(read_language('json').parse(text))
