"""
Module for editor actions.
"""
class Action(object):
    """
    Base action type, capable of executing an arbitrary action on an editor and
    undoing it if necessary.
    """
    alters = False

    def _expand(self, editor):
        """
        Returns a triple (selected, parent, index), useful for easy access to
        those properties from an editor.
        """
        selected = editor.selected
        parent = selected.parent
        return (selected, parent, parent.index(selected) if parent else -1)

    def is_available(self, editor):
        """
        Returns True if the action represented by this instance can be executed
        on the given editor.
        """
        return self._is_available(editor, *self._expand(editor))

    def _is_available(self, editor, selected, parent, index):
        """
        Auxiliary function to be overridden by its subclasses. 'selected' and
        'parent' are just easy to access references, also accessible from the
        'editor' instance.
        """
        pass

    def execute(self, editor):
        """
        Executes an action on an editor, remembering the previously selected
        item in case it needs to be rolled back. Returns the node that should
        be new selected item.
        """
        self.selected, self.parent, self.index = self._expand(editor)
        return self._execute(editor, self.selected, self.parent, self.index)

    def rollback(self, editor):
        """
        Undoes the action done by execute, returning the item selected before
        the 'execute' call.
        """
        self._rollback(editor, self.selected, self.parent, self.index)
        return self.selected

    def _execute(self, editor, selected, parent, index):
        """
        Auxiliary function to be overridden by its subclasses. 'selected' and
        'parent' are just easy to access references, also accessible from the
        'editor' instance.

        Return value is passed to editor to become the new selected item.
        """
        pass

    def _rollback(self, editor, selected, parent, index):
        """
        Auxiliary function to be overridden by its subclasses. 'selected' and
        'parent' are just easy to access references, also accessible from the
        'editor' instance.

        Return value is ignored.
        """
        raise NotImplementedError(str(self))


class SelectNextSibling(Action):
    def _is_available(self, editor, selected, parent, index):
        return parent is not None and index < len(parent) - 1

    def _execute(self, editor, selected, parent, index):
        return parent[index + 1]


class SelectPrevSibling(Action):
    def _is_available(self, editor, selected, parent, index):
        return parent is not None and index > 0

    def _execute(self, editor, selected, parent, index):
        return parent[index - 1]


class SelectParent(Action):
    def _is_available(self, editor, selected, parent, index):
        return parent is not None

    def _execute(self, editor, selected, parent, index):
        return parent


from ast import structures
class SelectChild(Action):
    def _is_available(self, editor, selected, parent, index):
        if len(selected) == 0:
            return hasattr(selected, 'insert')
        else:
            return selected[0].__class__ != str

    def _execute(self, editor, selected, parent, index):
        if len(selected):
            return selected[0]
        else:
            return structures.Node([], selected)


class NextUnfilled(Action):
    def _is_available(self, editor, selected, parent, index):
        return len(set(selected.defaulted) - set([selected])) > 0

    def _execute(self, editor, selected, parent, index):
        defaulted = selected.defaulted
        index = defaulted.index(selected) if selected in defaulted else 0
        return defaulted.pop((index + 1) % len(defaulted))


class MoveUp(SelectPrevSibling):
    alters = True

    def _is_available(self, editor, selected, parent, index):
        return (SelectPrevSibling._is_available(self, editor, selected, parent, index)
                and hasattr(parent, 'insert'))

    def _execute(self, editor, selected, parent, index):
        parent.remove(selected)
        parent.insert(index - 1, selected)
        return SelectPrevSibling._execute(self, editor, selected, parent, index)

    def _rollback(self, editor, selected, parent, index):
        parent.remove(selected)
        parent.insert(index, selected)


class MoveDown(SelectNextSibling):
    alters = True

    def _is_available(self, editor, selected, parent, index):
        return (SelectNextSibling._is_available(self, editor, selected, parent, index)
                and hasattr(parent, 'insert'))

    def _execute(self, editor, selected, parent, index):
        parent.remove(selected)
        parent.insert(index + 1, selected)
        return SelectNextSibling._execute(self, editor, selected, parent, index)

    def _rollback(self, editor, selected, parent, index):
        parent.remove(selected)
        parent.insert(index, selected)

    
from copy import deepcopy
class Copy(Action):
    def _is_available(self, editor, selected, parent, index):
        return True 

    def _execute(self, editor, selected, parent, index):
        from PyQt4 import QtGui, QtCore
        clipboard = QtGui.QApplication.clipboard()
        mime = QtCore.QMimeData()
        mime.setText(selected.render())
        try:
            mime.setHtml(editor.page().currentFrame().toHtml())
        except AttributeError:
            print 'Could not copy HTML.'
        clipboard.setMimeData(mime)

        editor.clipboard = deepcopy(selected)
        return selected


class Paste(Action):
    alters = True

    def _is_available(self, editor, selected, parent, index):
        return (editor.clipboard is not None
                and parent is not None
                and parent.can_insert(index, editor.clipboard))

    def _execute(self, editor, selected, parent, index):
        if not hasattr(self, 'copy'):
            self.copy = deepcopy(editor.clipboard)
        parent.add(index, self.copy)
        return self.copy

    def _rollback(self, editor, selected, parent, index):
        parent.remove(self.copy)


class Delete(Action):
    alters = True

    def _is_available(self, editor, selected, parent, index):
        return hasattr(parent, 'remove')

    def _execute(self, editor, selected, parent, index):
        parent.remove(selected)
        if len(parent):
            return parent[min(len(parent) - 1, index)]
        else:
            return parent

    def _rollback(self, editor, selected, parent, index):
        parent.insert(index, selected)


class Cut(Delete, Copy):
    alters = True

    def _execute(self, editor, selected, parent, index):
        Copy._execute(self, editor, selected, parent, index)
        return Delete._execute(self, editor, selected, parent, index)


class Insert(Action):
    alters = True

    def __init__(self, structure_class, before=False):
        self.new_item = structure_class.default()
        self.before = before

    def _is_available(self, editor, selected, parent, index):
        return parent and parent.can_insert(index, type(self.new_item))

    def _execute(self, editor, selected, parent, index):
        if not hasattr(parent, 'remove'):
            self.replaced_value = parent[index]

        if self.before:
            parent.add_before(index, self.new_item)
        else:
            parent.add(index, self.new_item)
        return self.new_item

    def _rollback(self, editor, selected, parent, index):
        if hasattr(parent, 'remove'):
            parent.remove(self.new_item)
        else:
            parent[index] = self.replaced_value


class Select(Action):
    def __init__(self, node):
        self.node = node

    def _is_available(self, editor, selected, parent, index):
        return True

    def _execute(self, editor, selected, parent, index):
        return self.node


class Rename(Action):
    alters = True
    ask_for_name = lambda self, old_name: 'new_name'

    def _is_available(self, editor, selected, parent, index):
        return len(selected) == 1 and type(selected[0]) == str

    def _execute(self, editor, selected, parent, index):
        self.old_name = selected[0]
        if not hasattr(self, 'new_name'):
            self.new_name = self.ask_for_name(selected[0], selected.alphabet)
        selected[0] = self.new_name
        return selected

    def _rollback(self, editor, selected, parent, index):
        selected[0] = self.old_name
