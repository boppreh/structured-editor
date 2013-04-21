class Action(object):
    def execute(self, editor):
        self.previous_selected = editor.selected
        return self._execute(editor, editor.selected, editor.selected.parent)

    def rollback(self, editor):
        self._rollback(editor, editor.selected, editor.selected.parent)
        return self.previous_selected

    def _rollback(self, editor, selected, parent):
        pass


class SelectNextSibling(Action):
    def is_available(self, editor, selected, parent):
        return parent is not None and parent.selected_index < len(parent) - 1

    def _execute(self, editor, selected, parent):
        return parent[parent.selected_index + 1]


class SelectPrevSibling(Action):
    def is_available(self, editor, selected, parent):
        return parent is not None and parent.selected_index > 0

    def _execute(self, editor, selected, parent):
        return parent[parent.selected_index - 1]


class SelectParent(Action):
    def is_available(self, editor, selected, parent):
        return parent is not None

    def _execute(self, editor, selected, parent):
        return parent


class SelectChild(Action):
    def is_available(self, editor, selected, parent):
        return (hasattr(selected, 'selected_index')
                and len(selected) > 0
                and selected[selected.selected_index].__class__ != str)

    def _execute(self, editor, selected, parent):
        return selected[selected.selected_index]


class MoveUp(SelectPrevSibling):
    def is_available(self, editor, selected, parent):
        return (SelectPrevSibling.is_available(self, editor, selected, parent)
                and hasattr(parent, 'insert'))

    def _execute(self, editor, selected, parent):
        parent.remove(selected)
        parent.insert(parent.selected_index - 1, selected)
        return SelectPrevSibling._execute(self, editor, selected, parent)


class MoveDown(SelectNextSibling):
    def is_available(self, editor, selected, parent):
        return (SelectNextSibling.is_available(self, editor, selected, parent)
                and hasattr(parent, 'insert'))

    def _execute(self, editor, selected, parent):
        parent.remove(selected)
        parent.insert(parent.selected_index + 1, selected)
        return SelectNextSibling._execute(self, editor, selected, parent)

    
from copy import deepcopy
class Copy(Action):
    def is_available(self, editor, selected, parent):
        return True 

    def _execute(self, editor, selected, parent):
        from PyQt4 import QtGui
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(selected.render())

        editor.clipboard = deepcopy(selected)
        return selected


class Paste(Action):
    def is_available(self, editor, selected, parent):
        return editor.clipboard is not None and hasattr(selected, 'insert') and selected.can_insert(selected.selected_index + 1, editor.clipboard)

    def _execute(self, editor, selected, parent):
        copy = deepcopy(editor.clipboard)
        selected.insert(selected.selected_index + 1, copy)
        return copy


class Delete(Action):
    def is_available(self, editor, selected, parent):
        return hasattr(parent, 'remove')

    def _execute(self, editor, selected, parent):
        self.parent = parent
        self.selected_index = parent.selected_index
        self.removed = selected

        parent.remove(selected)
        if len(parent):
            return parent[min(len(parent) - 1, parent.selected_index)]
        else:
            return parent

    def _rollback(self, editor, selected, parent):
        self.parent.insert(self.selected_index, self.removed)


class Cut(Delete, Copy):
    def _execute(self, editor, selected, parent):
        Copy._execute(self, editor, selected, parent)
        return Delete._execute(self, editor, selected, parent)


class Insert(Action):
    def __init__(self, structure_class):
        self.structure_class = structure_class

    def is_available(self, editor, selected, parent):
        return hasattr(selected, 'append') and selected.can_insert(selected.selected_index + 1, self.structure_class)

    def _execute(self, editor, selected, parent):
        new_item = self.structure_class()
        selected.append(new_item)
        return new_item


class Select(Action):
    def __init__(self, node):
        self.node = node

    def is_available(self):
        return True

    def _execute(self, editor, selected, parent):
        return self.node
