"""
Module for editing a program's source code interactively with a structured
editor.
"""
from ConfigParser import RawConfigParser

from ast.structures import empty_wrapper

class Editor(object):
    """
    Class for an abstract code editor. Supports execution of arbitrary actions,
    undo/redo, clipboard attribute (to be used by actions), node selection
    (single selection only for the moment) and rendering the tree with a
    user-specified function running on every node's text.
    """
    def __init__(self, root, selected_file=None):
        """
        Initializes an editor from an existing root node, selecting the root
        node, with empty clipboard and undo/redo history.
        """
        self.root = root
        self.selected = root
        self.selected_file = selected_file

        self.clipboard = None
        self.past_history = []
        self.future_history = []
        self.changed = False

        self.config = RawConfigParser()
        self.config.read('output_format.ini')

    def _file_wrapper(self, node):
        class_name = type(node).__name__.lower()
        try:
            return self.config.get('Templates', class_name)
        except:
            return node.template

    def save(self):
        """
        Saves the rendering of the current code tree (from root, not from
        selected node) to the file that originated this code.
        """
        assert self.selected_file is not None

        with open(self.selected_file, 'w') as target_file:
            target_file.write(self.render_tree(self._file_wrapper))

    def save_as(self, new_path):
        """
        Saves the rendering of the current code tree (from root, not from
        selected node) to an arbitrary given path, changing the file path for
        new saves to this new path.
        """
        self.selected_file = new_path
        self.save()

    def execute(self, action):
        """
        Executes a new action, allowing it to be reversed by undo. To avoid
        forking the action history, all actions undone and not redone are lost.

        Actions must have 'is_available', 'execute' and 'rollback' methods.
        """
        if action.alters:
            self.past_history.append((self.selected, action))
            self.future_history = []
            self.changed = True
            if len(self.past_history) > 1000:
                self.past_history = self.past_history[-1000:]

        self.selected = action.execute(self)

    def is_available(self, action):
        """
        Checks if a given action can be executed with the current editor state.
        """
        return action.is_available(self)

    def redo(self):
        """
        Re-executes the last undone action. This is not considered an action by
        itself.
        """
        self.selected, action = self.future_history.pop()
        self.past_history.append((self.selected, action))
        self.selected = action.execute(self)

    def undo(self):
        """
        Rollbacks the last action done. This is not considered an action by
        itself.
        """
        self.selected, action = self.past_history.pop()
        self.future_history.append((self.selected, action))
        self.selected = action.rollback(self)

    def render_tree(self, wrapper=empty_wrapper):
        """
        Returns the textual representation of the entire tree (not just the
        selected node).

        'wrapper': lambda node: node.template

        'wrapper' should be a function to change the node template before
        rendering. It takes the node as parameter and returns the new template.
        The default wrapper just returns the node.template unchanged.
        """
        return self.root.render(wrapper)
