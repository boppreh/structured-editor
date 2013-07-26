try:
    import ConfigParser as configparser
except:
    import configparser
import re, os
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE
from tree import Tree, Leaf

# Grammar regexes. Examples:
# assignment(statement) = expression expression
# parameters = expression*
# identifier(expression) = /[a-zA-Z_]w*/
node_name_regex = re.compile(r'^(\w+)(?:\((\w+)\))?$')

class Label(object):
    """
    Class for representing a node type, for example "Assignment" or
    "Expression". Each node type has a name, a formation rule and possibly
    another node type as parent.
    """
    def __init__(self, rule=None, parent=None):
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

class ListTree(Tree):
    """
    AST element for nodes that contain a variable number of other nodes. Its
    node type "rule" attribute defines what kind of node types are expected as
    children.
    """
    def __str__(self):
        children = map(str, self.children)
        return self.type_.output_template.format(', '.join(children))

class FixedTree(Tree):
    """
    AST element for nodes that contain a fixed number of other nodes. Its node
    type "rule" attribute define the type of each children, by position.

    The dictionary keys are numbers. A dictionary is used to disallow
    insertions and removals of elements.
    """
    def __str__(self):
        children = map(str, self.children)
        return self.type_.output_template.format(*children)

class ConstantLeaf(Leaf):
    """
    AST element containing a single string value.
    """
    def __str__(self):
        return self.type_.output_template.format(self.value)

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
        Converts an XML tree to a tree of ConstantLeaf, ListTree and FixedTree
        elements with their types appropriately set.
        """
        type_ = self.types[root.tag]

        if isinstance(type_.rule, str):
            # Literal type, rule is regex.
            return ConstantLeaf(type_, root.text)
        elif isinstance(type_.rule, Label):
            # List type, rule is child type.
            return ListTree(type_, map(self._convert_tree, root))
        else:
            # Fixed list type, rule is list of children type.
            return FixedTree(type_, map(self._convert_tree, root))

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
        process = Popen(['python', self.parser], stdout=PIPE, stdin=PIPE,
                        universal_newlines=True)
        stdout, stderr = process.communicate(text)
        return self.parse_xml(stdout)

    
def parse_grammar(rule_pairs):
    """
    Converts a list of (name, rule) keypairs into a dictionary
    {name: Label}. "name" can extend other names by specifying the parent in
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
            rule = [nodes[r] for r in rule.split()]

        nodes[name] = Label(rule, parent)

    return nodes

def merge_config(config):
    """
    From the configuration object for a given language, parses the grammar
    structure, defaults, hotkeys, styles and output and display templates.

    Returns the types dictionary {type_name: type_object} with types setup
    according to the configuration object.
    """
    types = parse_grammar(config.items('Composition Rules'))

    for name, type_ in types.items():
        if type_.rule is None:
            continue

        type_.default = ET.fromstring(config.get('Defaults', name))
        type_.hotkey = config.get('Hotkeys', name)
        type_.style = config.get('Style', name)

        type_.output_template = config.get('Output Templates', name)
        try:
            type_.display_template = config.get('Display Templates', name)
        except configparser.NoOptionError:
            type_.display_template = type_.output_template

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
    """
    Reads all language configurations in ./languages/ and returns a dictionary
    {name: Language}.
    """
    return {language: read_language(language)
            for language in os.listdir('languages')}

if __name__ == '__main__':
    text = open('test_files/1.json').read()
    print(read_language('json').parse(text))
