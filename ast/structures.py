"""
Contains the high level abstract structures and lists for a parsed syntax
tree.
"""
from pyparsing import ParseResults

class Node(object):
    abstract = True
    global_dict = {}
    count = 0
    template = '<ABSTRACT NODE>'
    href_template = '<a href="{}" style="color: #000000; text-decoration: none">'

    def __init__(self, contents):
        self.parent = None
        self.contents = contents
        self.str_wrapper = None

        Node.count += 1
        self.id = Node.count

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

    def update_template(self):
        pass

    def format(self, template, dictionary):
        href = self.href_template.format(self.id)
        insert_links = lambda t: '</a>' + str(t) + href
        dictionary = {name: insert_links(value) for name, value in dictionary.items()}
        return href + template.format(**dictionary) + '</a>'

    def __str__(self):
        Node.global_dict[self.id] = self

        self.update_template()
        unindented_text = self.format(self.template, self.dictionary)
        text = unindented_text.replace('\t', Block.indentation)

        if self.str_wrapper:
            return self.str_wrapper(text)
        else:
            return text


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
    
    def update_template(self):
        str_contents = map(str, self.contents)
        joined_contents = self.delimiter.join(str_contents)
        indented_contents = joined_contents.replace('\t', Block.indentation)
        self.dictionary = {'children': indented_contents}

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


class Statement(AbstractStructure):
    template = 'ABSTRACT STATEMENT'


class Block(StructureList):
    """
    List of statements contained in a function declaration, control structure or
    the program root. Also called compound statement.
    """
    abstract = False

    child_type = Statement
    delimiter = '\n\t'
    template = '\t{children}'

    identationNumber = -1
    indentation = ''

    @staticmethod
    def increaseIndentation():
        Block.identationNumber += 1
        Block.indentation = Block.identationNumber * '    '

    @staticmethod
    def decreaseIdentation():
        Block.identationNumber -= 1
        Block.indentation = Block.identationNumber * '    '

    def __str__(self):
        try:
            Block.increaseIndentation()
            return super(Block, self).__str__()
        finally:
            Block.decreaseIdentation()


class Expression(AbstractStructure):
    """ Abstract class for expressions that can be used as values. """
    template = 'ABSTRACT EXPRESSION'
