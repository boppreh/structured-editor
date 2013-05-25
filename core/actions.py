"""
Module for editor actions.
"""
from copy import deepcopy

class Action(object):
    """
    Base action type, capable of executing an arbitrary action on an editor and
    undoing it if necessary.
    """
    alters = False

    def _expanded_call(self, function, editor):
        parent = editor.selected.parent
        index = parent.index(editor.selected) if parent else -1
        return function(editor, editor.selected, parent, index)

    def is_available(self, editor):
        """
        Returns True if the action represented by this instance can be executed
        on the given editor.
        """
        return self._expanded_call(self._is_available, editor)

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
        if self.alters:
            self.previous_tree = deepcopy(editor.root)
            self.previous_selected = editor.selected
        return self._expanded_call(self._execute, editor)

    def rollback(self, editor):
        """
        Undoes the action done by execute, returning the item selected before
        the 'execute' call.
        """
        editor.root = self.previous_tree
        return self.previous_selected

    def _execute(self, editor, selected, parent, index):
        """
        Auxiliary function to be overridden by its subclasses. 'selected' and
        'parent' are just easy to access references, also accessible from the
        'editor' instance.

        Return value is passed to editor to become the new selected item.
        """
        pass



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


class MoveDown(SelectNextSibling):
    alters = True

    def _is_available(self, editor, selected, parent, index):
        return (SelectNextSibling._is_available(self, editor, selected, parent, index)
                and hasattr(parent, 'insert'))

    def _execute(self, editor, selected, parent, index):
        parent.remove(selected)
        parent.insert(index + 1, selected)
        return SelectNextSibling._execute(self, editor, selected, parent, index)

    
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
        copy = deepcopy(editor.clipboard)
        parent.add(index, copy)
        return copy


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


class Cut(Delete, Copy):
    alters = True

    def _execute(self, editor, selected, parent, index):
        Copy._execute(self, editor, selected, parent, index)
        return Delete._execute(self, editor, selected, parent, index)


class Insert(Action):
    alters = True

    def __init__(self, structure_class, before=False):
        self.structure_class = structure_class
        self.before = before

    def _is_available(self, editor, selected, parent, index):
        return parent and parent.can_insert(index, self.structure_class)

    def _execute(self, editor, selected, parent, index):
        new_item = self.structure_class.default()
        if self.before:
            parent.add_before(index, new_item)
        else:
            parent.add(index, new_item)
        return new_item.defaulted.pop(0)


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
        selected[0] = self.ask_for_name(selected[0])
        return selected
