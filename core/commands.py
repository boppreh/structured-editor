class Command(object):
    def is_available(self, editor):
        selected = editor.selected
        return self._is_available(editor, selected, selected.parent)

    def execute(self, editor):
        selected = editor.selected
        new_selected = self._execute(editor, selected, selected.parent)
        editor.selected = new_selected
        parent = new_selected.parent
        if parent:
            parent.selected_index = parent.index(new_selected)


class SelectNextSibling(Command):
    def _is_available(self, editor, selected, parent):
        return parent is not None and parent.selected_index < len(parent) - 1

    def _execute(self, editor, selected, parent):
        return parent[parent.selected_index + 1]


class SelectPrevSibling(Command):
    def _is_available(self, editor, selected, parent):
        return parent is not None and parent.selected_index > 0

    def _execute(self, editor, selected, parent):
        return parent[parent.selected_index - 1]


class SelectParent(Command):
    def _is_available(self, editor, selected, parent):
        return parent is not None

    def _execute(self, editor, selected, parent):
        return parent


class SelectChild(Command):
    def _is_available(self, editor, selected, parent):
        return (hasattr(selected, 'selected_index')
                and len(selected) > 0
                and selected[selected.selected_index].__class__ != str)

    def _execute(self, editor, selected, parent):
        return selected[selected.selected_index]


class MoveUp(SelectPrevSibling):
    def _is_available(self, editor, selected, parent):
        return (SelectPrevSibling._is_available(self, editor, selected, parent)
                and hasattr(parent, 'insert'))

    def _execute(self, editor, selected, parent):
        parent.remove(selected)
        parent.insert(parent.selected_index - 1, selected)
        return SelectPrevSibling._execute(self, editor, selected, parent)


class MoveDown(SelectNextSibling):
    def _is_available(self, editor, selected, parent):
        return (SelectNextSibling._is_available(self, editor, selected, parent)
                and hasattr(parent, 'insert'))

    def _execute(self, editor, selected, parent):
        parent.remove(selected)
        parent.insert(parent.selected_index + 1, selected)
        return SelectNextSibling._execute(self, editor, selected, parent)

    
from copy import deepcopy
class Copy(Command):
    def _is_available(self, editor, selected, parent):
        return True 

    def _execute(self, editor, selected, parent):
        from PyQt4 import QtGui
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(str(selected))

        editor.clipboard = deepcopy(selected)
        return selected


class Paste(Command):
    def _is_available(self, editor, selected, parent):
        return editor.clipboard is not None and hasattr(selected, 'insert') and selected.can_insert(selected.selected_index + 1, editor.clipboard)

    def _execute(self, editor, selected, parent):
        copy = deepcopy(editor.clipboard)
        selected.insert(selected.selected_index + 1, copy)
        return copy


class Delete(Command):
    def _is_available(self, editor, selected, parent):
        return hasattr(parent, 'remove')

    def _execute(self, editor, selected, parent):
        parent.remove(selected)
        if len(parent):
            return parent[min(len(parent) - 1, parent.selected_index)]
        else:
            return parent


class Cut(Delete, Copy):
    def _execute(self, editor, selected, parent):
        Copy._execute(self, editor, selected, parent)
        return Delete._execute(self, editor, selected, parent)


class Insert(Command):
    def __init__(self, structure_class):
        self.structure_class = structure_class

    def _is_available(self, editor, selected, parent):
        return hasattr(selected, 'append') and selected.can_insert(selected.selected_index + 1, self.structure_class)

    def _execute(self, editor, selected, parent):
        new_item = self.structure_class()
        selected.append(new_item)
        return new_item
