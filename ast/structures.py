"""
Contains the high level abstract structures and lists for a parsed syntax
tree.
"""
from pyparsing import ParseResults

empty_wrapper = lambda node, text: text

class Node(object):
    abstract = True
    template = '<ABSTRACT NODE>'

    def __init__(self, contents):
        self.parent = None
        self.contents = contents
        self.str_wrapper = None
        self.dictionary = {}

        for item in contents:
            try:
                item.parent = self
            except AttributeError:
                print "Can't set parent on " + item

    def __getitem__(self, i):
        return self.contents[i]

    def __setitem__(self, index, item):
        assert self.can_insert(index, item)
        self.contents[index] = item
        item.parent = self

    def __len__(self):
        return len(self.contents)

    def index(self, item):
        return self.contents.index(item)

    def get_available_classes(self, index):
        main_class = self.get_expected_class(index)
        return main_class.__subclasses__() + [main_class]

    def can_insert(self, index, item):
        return isinstance(item, self.get_expected_class(index))

    def recurse(self, fn):
        fn(self)
        for item in self:
            if hasattr(item, 'recurse'):
                item.recurse(fn)
            else:
                fn(item)

    def render(self, wrapper=empty_wrapper):
        """
        Recursively renders itself and all children, calling 'wrapper' on
        each step, if available.
        """
        text_dictionary = {key: value.render(wrapper)
                           for key, value in self.dictionary.items()}
        text = self.template.format(**text_dictionary)
        return wrapper(self, text)


class Dummy(Node):
    template = '<{value}>'
    def __init__(self, value):
        Node.__init__(self, [])
        self.value = value
        self.dictionary = {'value': value}


class AbstractStructure(Node):
    """
    Structure with fixed number of known parts. Automatically cast children to
    the correct types and supplies an automatic string conversion through a
    class attribute 'template'.
    """
    subparts = []

    def __init__(self, toks=None):
        self.dictionary = {}
        self.selected_index = 0
        contents = []

        if toks == None:
            toks = [Dummy(name) for name, type in self.subparts]

        types = [type_ for name, type_ in self.subparts]
        contents = [self.cast_subpart(tok, type_) for tok, type_ in zip(toks, types)]
        Node.__init__(self, contents)

        names = [name for name, type_ in self.subparts]
        self.dictionary = dict(zip(names, self.contents))

    def cast_subpart(self, tok, type_):
        if isinstance(tok, type_):
            return tok
        else:
            return type_(tok)

    def get_expected_class(self, index):
        return self.subparts[index][1]


class StructureList(Node):
    """
    Structure with variable number of parts derived from the same type.
    Exposes the standard list functions len, index and bracket access
    (list[0]).

    Automatically sets the parent and selected_index attribute in itself and
    its children.
    """
    delimiter = ', '
    child_type = str
    template = '{children}'

    def __init__(self, contents=None):
        if not contents:
            contents = []

        # ParseResults don't play well with lists, overriding important methods
        # like index and remove with strings. Also, this depends on everyone
        # that calls StructureList with a parse results content to not store the
        # original parse results anywhere else.
        if contents.__class__ == ParseResults:
            contents = list(contents)

        self.parent = None
        self.selected_index = 0

        for item in contents:
            assert isinstance(item, self.child_type), '{} expected child with type {}, got {} ("{}").'.format(self.__class__, self.child_type, item.__class__, contents)
            assert hasattr(item, 'parent'), 'Expected child with parent attribute, got {} ("{}").'.format(item.__class__, item)

            item.parent = self

        Node.__init__(self, contents)

    def get_expected_class(self, index):
        return self.child_type

    def remove(self, item):
        item.parent = None
        self.contents.remove(item)

    def append(self, item):
        assert self.can_insert(len(self), item)
        item.parent = self
        self.contents.append(item)

    def insert(self, index, item):
        assert self.can_insert(len(self), item)
        item.parent = self
        return self.contents.insert(index, item)

    def render(self, wrapper=empty_wrapper):
        rendered_contents = [item.render(wrapper) for item in self.contents]
        joined_contents = self.delimiter.join(rendered_contents)
        text = self.template.format(children=joined_contents)
        return wrapper(self, text)


class Statement(AbstractStructure):
    template = 'ABSTRACT STATEMENT'


class Block(StructureList):
    """
    List of statements contained in a function declaration, control structure or
    the program root. Also called compound statement.
    """
    abstract = False
    child_type = Statement

    def render(self, wrapper=empty_wrapper):
        str_contents = [item.render(wrapper) for item in self.contents]

        rendered = []
        for line in str_contents:
            if line.count('\n') >= 2:
                rendered.append(line + '\n')
            else:
                rendered.append(line)

        rendered_text = ''.join(rendered).strip()
        if self.parent:
            rendered_text = rendered_text.replace('\n', '\n    ')
        else:
            rendered_text = rendered_text.replace('\n', '', 1)

        return wrapper(self, rendered_text)


class Expression(AbstractStructure):
    """ Abstract class for expressions that can be used as values. """
    template = 'ABSTRACT EXPRESSION'
