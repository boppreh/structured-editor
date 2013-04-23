"""
Module for editing a program's source code interactively with a structured
editor.
"""
from ast import lua_parser

class Editor(object):
    """
    Class for an abstract code editor. Supports execution of arbitrary actions,
    undo/redo, clipboard attribute (to be used by actions), node selection
    (single selection only for the moment) and rendering the tree with a
    user-specified function running on every node's text.
    """
    @staticmethod
    def from_text(text):
        """
        Creates a new Editor instance taking the root node from the parsed
        text.
        """
        return Editor(lua_parser.parseString(text), None)

    @staticmethod
    def from_file(path):
        """
        Creates a new Editor instance from the given file. The editor can then
        'save' and 'save_as' to export the edited code.
        """
        return Editor(lua_parser.parseFile(path), path)

    def __init__(self, root, selected_file=None):
        """
        Initializes an editor from an existing root node, selecting the root
        node, with empty clipboard and undo/redo history.
        """
        self.root = root
        self.selected = root
        self.file_selected = selected_file
        self.clipboard = None
        self.past_history = []
        self.future_history = []

    def save(self):
        """
        Saves the rendering of the current code tree (from root, not from
        selected node) to the file that originated this code.
        """
        with open(self.file_selected, 'w') as target_file:
            target_file.write(self.render())

    def save_as(self, new_path):
        """
        Saves the rendering of the current code tree (from root, not from
        selected node) to an arbitrary given path, changing the file path for
        new saves to this new path.
        """
        self.file_selected = new_path
        self.save()

    def _update_selected(self, new_selected):
        """
        Changes the currently selected node, updating the parent's
        selected_index value if it has a parent.

        The selected_index is stored in the node itself so it can be restored
        when the user navigates back to it.
        """
        self.selected = new_selected

        parent = self.selected.parent
        if parent:
            parent.selected_index = parent.index(self.selected)

    def execute(self, action):
        """
        Executes a new action, allowing it to be reversed by undo. To avoid
        forking the action history, all actions undone and not redone are lost.

        Actions must have 'is_available', 'execute' and 'rollback' methods.
        """
        self._update_selected(action.execute(self))
        self.past_history.append(action)
        self.future_history = []

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
        self.past_history.append(self.future_history.pop(0))
        self._update_selected(self.past_history[-1].execute(self))

    def undo(self):
        """
        Rollbacks the last action done. This is not considered an action by
        itself.
        """
        self.future_history.insert(0, self.past_history.pop())
        self._update_selected(self.future_history[0].rollback(self))

    def render(self, wrapper=None):
        """
        Returns the textual representation of the entire tree (not just the
        selected node).

        'wrapper' should be a function that takes a node's reference and its
        basic rendering and returns the complete rendering of that node.
        """
        return self.root.render(wrapper)
