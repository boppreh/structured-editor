"""
Contains the high level abstract structures and lists for a parsed syntax
tree.
"""
from pyparsing import ParseResults
from copy import deepcopy

empty_wrapper = lambda node: node.template

class Node(object):
    abstract = True
    count = 0
    defaulted = []

    @classmethod
    def _default(cls):
        return cls()

    @classmethod
    def default(cls):
        new = cls._default()
        Node.defaulted.append(new)
        return new

    def __init__(self, contents, parent=None):
        self.node_id = Node.count
        Node.count += 1

        self.contents = contents
        self.parent = parent

        for item in contents:
            try:
                item.parent = self
            except AttributeError:
                pass
                #print "Can't set parent on " + item

    def __deepcopy__(self, memo):
        return type(self)([deepcopy(item, memo) for item in self.contents])

    def __getitem__(self, i):
        return self.contents[i]

    def __setitem__(self, index, item):
        assert self.can_insert(index, item)
        self.contents[index] = item
        if type(item) != str:
            item.parent = self

    def __len__(self):
        return len(self.contents)

    def index(self, item):
        try:
            return self.contents.index(item)
        except ValueError:
            return -1

    def cast_subpart(self, tok, type_):
        if isinstance(tok, type_):
            return tok
        elif tok.__class__ == ParseResults:
            return type_(tok)
        else:
            raise TypeError("{} can't cast {} into {} ({})".format(self.__class__.__name__, tok.__class__.__name__, type_.__name__, repr(tok)))

    def get_available_classes(self, index):
        main_class = self.get_expected_class(index)
        def subclasses(class_):
            return [class_] + sum(map(subclasses, class_.__subclasses__()), [])
        return subclasses(main_class)

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
        raise NotImplementedError()

    def __str__(self):
        return self.render()


class StaticNode(Node):
    """
    Structure with fixed number of known parts. Automatically cast children to
    the correct types and supplies an automatic string conversion through a
    class attribute 'template'.
    """
    subparts = []
    template = '<Abstract Static Node>'

    def __init__(self, toks=None):
        if toks == None:
            toks = [type_.default() for name, type_ in self.subparts]

        contents = [self.cast_subpart(tok, part[1])
                    for tok, part in zip(toks, self.subparts)]

        Node.__init__(self, contents)

    def get_expected_class(self, index):
        return self.subparts[index][1]

    def render(self, wrapper=empty_wrapper):
        """
        Recursively renders itself and all children, calling 'wrapper' on
        each step, if available.
        """
        dictionary = {}
        for content, subpart in zip(self.contents, self.subparts):
            name, type_ = subpart
            dictionary[name] = content.render(wrapper)

        return wrapper(self).format(**dictionary)

    def add(self, index, item):
        assert self.can_insert(index, item)
        item.parent = self
        self.contents[index] = item

    def add_before(self, index, item): self.add(index, item)

class DynamicNode(Node):
    """
    Structure with variable number of parts derived from the same type.
    Exposes the standard list functions len, index and bracket access
    (list[0]).

    Automatically sets the parent attribute in itself and its children.
    """
    delimiter = ', '
    child_type = str
    template = '{children}'

    def __init__(self, contents=None):
        if not contents:
            contents = []

        # ParseResults don't play well with lists, overriding important methods
        # like index and remove with strings. Also, this depends on everyone
        # that calls DynamicNode with a parse results content to not store the
        # original parse results anywhere else.
        if contents.__class__ == ParseResults:
            contents = list(contents)

        contents = [self.cast_subpart(i, self.child_type) for i in contents]
        Node.__init__(self, contents)

    def get_expected_class(self, index):
        return self.child_type

    def remove(self, item):
        item.parent = None
        self.contents.remove(item)

    def add(self, index, item):
        return self.insert(index + 1, item)

    def add_before(self, index, item):
        return self.insert(index, item)

    def insert(self, index, item):
        assert self.can_insert(index, item)
        item.parent = self
        return self.contents.insert(index, item)

    def render(self, wrapper=empty_wrapper):
        rendered_contents = [item.render(wrapper) for item in self.contents]
        joined_contents = self.delimiter.join(rendered_contents)
        return wrapper(self).format(children=joined_contents)


class Statement(StaticNode):
    template = 'ABSTRACT STATEMENT'


class Block(DynamicNode):
    """
    List of statements contained in a function declaration, control structure or
    the program root. Also called compound statement.
    """
    abstract = False
    child_type = Statement
    template = '{children}'

    def render(self, wrapper=empty_wrapper):
        str_contents = [item.render(wrapper) for item in self.contents]
        for i, item in enumerate(str_contents):
            if '\n' in item and i < len(self) - 1:
                str_contents[i] += '\n'

        rendered_text = '\n' + '\n'.join(str_contents).strip()
        if self.parent:
            rendered_text = rendered_text.replace('\n', '\n    ')
        else:
            rendered_text = rendered_text.replace('\n', '', 1)

        return wrapper(self).format(children=rendered_text)
