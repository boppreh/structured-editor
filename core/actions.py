"""
Module for editor actions.
"""
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
        self.previous_selected = editor.selected
        return self._expanded_call(self._execute, editor)

    def rollback(self, editor):
        """
        Undoes the action done by execute, returning the item selected before
        the 'execute' call.
        """
        self._rollback(editor)
        return self.previous_selected

    def _execute(self, editor, selected, parent, index):
        """
        Auxiliary function to be overridden by its subclasses. 'selected' and
        'parent' are just easy to access references, also accessible from the
        'editor' instance.

        Return value is passed to editor to become the new selected item.
        """
        pass

    def _rollback(self, editor, selected, parent):
        """
        Auxiliary function to be overridden by its subclasses. 'selected' and
        'parent' are just easy to access references, also accessible from the
        'editor' instance.

        Return value is ignored.
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


class SelectChild(Action):
    def _is_available(self, editor, selected, parent, index):
        return (len(selected) > 0 and selected[0].__class__ != str)

    def _execute(self, editor, selected, parent, index):
        return selected[0]


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
                and hasattr(selected, 'insert')
                and selected.can_insert(0,
                                        editor.clipboard))

    def _execute(self, editor, selected, parent, index):
        copy = deepcopy(editor.clipboard)
        selected.insert(0, copy)
        return copy


class Delete(Action):
    alters = True

    def _is_available(self, editor, selected, parent, index):
        return hasattr(parent, 'remove')

    def _execute(self, editor, selected, parent, index):
        self.parent = parent
        self.index = index
        self.removed = selected

        parent.remove(selected)
        if len(parent):
            return parent[min(len(parent) - 1, index)]
        else:
            return parent

    def _rollback(self, editor):
        self.parent.insert(self.index, self.removed)


class Cut(Delete, Copy):
    alters = True

    def _execute(self, editor, selected, parent, index):
        Copy._execute(self, editor, selected, parent, index)
        return Delete._execute(self, editor, selected, parent, index)


class Insert(Action):
    alters = True

    def __init__(self, structure_class):
        self.structure_class = structure_class

    def _is_available(self, editor, selected, parent, index):
        return (hasattr(selected, 'add')
                and parent.can_insert(index,
                                      self.structure_class))

    def _execute(self, editor, selected, parent, index):
        new_item = self.structure_class.default()
        parent.add(index, new_item)
        return new_item


class Select(Action):
    def __init__(self, node):
        self.node = node

    def _is_available(self, editor, selected, parent, index):
        return True

    def _execute(self, editor, selected, parent, index):
        return self.node
