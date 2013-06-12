"""
Module for editing a program's source code interactively with a structured
editor.
"""
from ast import lua_parser, json_parser
from . import config

parsers = {'lua': lua_parser, 'json': json_parser}


class Editor(object):
    """
    Class for an abstract code editor. Supports execution of arbitrary actions,
    undo/redo, clipboard attribute (to be used by actions), node selection
    (single selection only for the moment) and rendering the tree with a
    user-specified function running on every node's text.
    """
    
    @classmethod
    def from_file(cls, path):
        language = path.rsplit('.')[-1]
        root = parsers[language].parse_string(open(path).read())
        return cls(root, language, path)

    @classmethod
    def from_string(cls, string, language):
        root = parsers[language].parse_string(string)
        return cls(root, language, None)

    @classmethod
    def new_empty(cls, language):
        return cls(parsers[language].new_empty(), language, None)

    def __init__(self, root, language, selected_file=None):
        """
        Initializes an editor from an existing root node, selecting the root
        node, with empty clipboard and undo/redo history.
        """
        self.root = root
        self.selected = root
        self.selected_file = selected_file
        self.structures = parsers[language].structures
        self.language = language

        self.clipboard = None
        self.past_history = []
        self.future_history = []
        self.last_saved_action = None

    def _file_wrapper(self, node):
        class_name = type(node).__name__.lower()
        try:
            return config.get('Templates', class_name)
        except:
            return node.template

    def save(self):
        """
        Saves the rendering of the current code tree (from root, not from
        selected node) to the file that originated this code.
        """
        assert self.selected_file is not None

        if self.past_history:
            self.last_saved_action = self.past_history[-1]

        with open(self.selected_file, 'w') as target_file:
            target_file.write(self.root.render(self._file_wrapper))

    def save_as(self, new_path):
        """
        Saves the rendering of the current code tree (from root, not from
        selected node) to an arbitrary given path, changing the file path for
        new saves to this new path.
        """
        self.selected_file = new_path
        self.save()

    def execute(self, action, save_history=True):
        """
        Executes a new action, allowing it to be reversed by undo. To avoid
        forking the action history, all actions undone and not redone are lost.

        Actions must have 'is_available', 'execute' and 'rollback' methods.
        """
        if action.alters:
            self.past_history.append((self.selected, action))
            self.future_history = []
            if len(self.past_history) > 1000:
                self.past_history = self.past_history[-1000:]

        self.selected = action.execute(self.selected)

    def is_available(self, action):
        """
        Checks if a given action can be executed with the current editor state.
        """
        return action.is_available(self.selected)

    def redo(self):
        """
        Re-executes the last undone action. This is not considered an action by
        itself.
        """
        self.selected, action = self.future_history.pop()
        self.past_history.append((self.selected, action))
        self.selected = action.execute(self.selected)

    def undo(self):
        """
        Rollbacks the last action done. This is not considered an action by
        itself.
        """
        self.selected, action = self.past_history.pop()
        self.future_history.append((self.selected, action))
        self.selected = action.rollback(self.selected)

    def can_save(self):
        """
        Returns true if this editor is able to directly save the current
        file. False in case it doesn't have info on the original file.
        """
        return self.selected_file is not None

    def can_undo(self):
        """
        Returns true if it's possible to undo an action with this editor.
        """
        return len(self.past_history) >= 1

    def can_redo(self):
        """
        Returns true if it's possible to redo an action with this editor.
        """
        return len(self.future_history) >= 1

    def can_close(self):
        """
        Returns a boolean value indicating if the editor can be closed. If
        there are unsaved changes, ask the user to save or discard.
        """
        is_sourced = self.selected_file is not None or len(self.root) == 0
        is_saved = (len(self.past_history) == 0 or
                    self.last_saved_action == self.past_history[-1])

        return is_sourced and is_saved
