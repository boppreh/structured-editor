"""
Module for editing a program's source code interactively with a structured
editor.
"""
class Editor(object):
    def __init__(self, root):
        self.root = root
        self.selected = root
        self.clipboard = None
        self.past_history = []
        self.future_history = []

    def update_selected(self, new_selected):
        self.selected = new_selected

        parent = self.selected.parent
        if parent:
            parent.selected_index = parent.index(self.selected)

    def execute(self, action):
        self.update_selected(action.execute(self))
        self.past_history.append(action)
        self.future_history = []

    def is_available(self, action):
        return action.is_available(self, self.selected, self.selected.parent)

    def redo(self):
        self.past_history.append(self.future_history.pop(0))
        self.update_selected(self.past_history[-1].execute(self))

    def undo(self):
        self.future_history.insert(0, self.past_history.pop())
        self.update_selected(self.future_history[0].rollback(self))

    def render(self, wrapper=None):
        return self.root.render(wrapper)
