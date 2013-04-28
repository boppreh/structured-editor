"""
Package for the tabbed features of the GUI editor. Each tab is able to display
a different Editor instance and allows for most actions a user may try:
repositioning tabs, close buttons, hotkeys (Ctrl+W and Ctrl+T), etc. "save",
"save as", "open", "parse" and "new" actions are self contained.
"""
from PyQt4 import QtCore, QtGui

import os

from pyparsing import ParseException

from code_display import CodeDisplay
from core.editor import Editor


class CodeInput(QtGui.QDialog):
    """
    Dialog for inputing a program as text. The result is stored in the
    self.editor attribute, containing an entire Editor instance with no
    selected_file value.
    """
    def __init__(self, parent=None):
        super(CodeInput, self).__init__(parent)

        self.setWindowTitle("Source code input")

        self.textedit = QtGui.QPlainTextEdit(self)

        buttons = QtGui.QDialogButtonBox()
        buttons.setOrientation(QtCore.Qt.Horizontal)
        buttons.setStandardButtons(QtGui.QDialogButtonBox.Cancel |
                                   QtGui.QDialogButtonBox.Ok)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.textedit, 0, 0, 1, 1)
        layout.addWidget(buttons, 1, 0, 1, 1)

    def accept(self):
        try:
            text = str(self.textedit.toPlainText())
            self.editor = Editor.from_text(text)
            super(CodeInput, self).accept()
        except ParseException:
            QtGui.QMessageBox.critical(self, "Parsing error", "Could not parse the given text.")


class CustomTabBar(QtGui.QTabBar):
    """
    Class for a Tab Bar with more usability options, such as an unobtrusive
    close button on the current tab, support for closing tabs with the middle
    mouse button and reordering tabs.
    """
    def __init__(self, close_handler, *args, **kargs):
        super(CustomTabBar, self).__init__(*args, **kargs)
        self.setMovable(True)

        self.close_handler = close_handler
        self.previous_index = -1

        self.currentChanged.connect(self._update_tab)

    def close_tab(self, tab=None):
        """ Closes the tab at index "tab", if there is one. """
        if tab is None:
            tab = self.currentIndex()

        if tab != -1 and self.close_handler(tab):
            self.removeTab(tab)
            self._update_tab()

    def _update_tab(self, new_tab=None):
        self.hide_close_button(self.previous_index)
        self.show_close_button(self.currentIndex())

        self.previous_index = self.currentIndex()

        if self.count() > 1:
            self.show()
        else:
            self.hide()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.close_tab(self.tabAt(event.pos()))

        super(CustomTabBar, self).mouseReleaseEvent(event)

    def _make_close_button(self):
        style = QtGui.qApp.style()
        icon = style.standardIcon(style.SP_DockWidgetCloseButton)
        closeButton = QtGui.QPushButton(icon, '')
        closeButton.clicked.connect(self.close_tab)
        closeButton.resize(12, 12)
        closeButton.setFlat(True)
        return closeButton

    def add_close_button(self, tab):
        """ Adds a close button to the tab at index "tab". """
        self.setTabButton(tab, QtGui.QTabBar.RightSide,
                          self._make_close_button())

    def _get_close_button(self, tab):
        return self.tabButton(tab, QtGui.QTabBar.RightSide)

    def hide_close_button(self, tab):
        """ Hides the existing close button from the tab at index "tab". """
        if self._get_close_button(tab):
            self._get_close_button(tab).hide()

    def show_close_button(self, tab):
        """ Reveals the existing close button on the tab at index "tab". """
        if self._get_close_button(tab):
            self._get_close_button(tab).show()


class TabbedEditor(QtGui.QTabWidget):
    """
    Class for managing multiple editors with tabs. The current Editor instance
    can be accessed from the method editor(), and its selected node at
    selected_node() (note that "selected" is a function from the QTabWidget
    superclass).
    """
    def __init__(self, refreshHandler, parent):
        super(TabbedEditor, self).__init__(parent=parent)
        self.setTabBar(CustomTabBar(self._check_saved_changes))

        self.untitled_tab_count = 0

        self.refreshHandler = refreshHandler
        self.currentChanged.connect(self.refreshHandler)
        self.tabBar().tabCloseRequested.connect(self._check_saved_changes)

        QtGui.QShortcut('Ctrl+T', self, self.new)
        QtGui.QShortcut('Ctrl+W', self, self.tabBar().close_tab)

    def _check_saved_changes(self, tab):
        editor = self.widget(tab).editor
        if not editor.changed:
            return True

        label = self.tabText(tab)
        buttons = (QtGui.QMessageBox.Save |
                   QtGui.QMessageBox.Discard |
                   QtGui.QMessageBox.Cancel)
        message = 'Do you want to save changes to {}?'.format(label)
        result = QtGui.QMessageBox.warning(self, 'Close confirmation', message,
                                           buttons=buttons)

        if result == QtGui.QMessageBox.Save:
            if editor.file_selected:
                editor.save()
                return True
            else:
                path = str(QtGui.QFileDialog.getSaveFileName(self,
                                                             'Save as',
                                                             label,
                                                             filter="*.lua"))
                if path:
                    editor.save_as(path)
                    return True
                else:
                    return False
        elif result == QtGui.QMessageBox.Discard:
            return True
        elif result == QtGui.QMessageBox.Cancel:
            return False

    def _next_label(self):
        self.untitled_tab_count += 1
        return 'Untitled Document ' + str(self.untitled_tab_count)

    def label(self):
        return self.tabText(self.currentIndex())

    def editor(self):
        """
        Returns the current Editor instance or None if there are not tabs.
        """
        if self.currentWidget():
            return self.currentWidget().editor
        else:
            return None

    def selected_node(self):
        """
        Returns the selected node from the current editor or None if there are
        no tabs.
        """
        if self.editor():
            return self.editor().selected
        else:
            return None

    def _add_editor(self, editor, label=None):
        """
        Creates a new tab to contain a given editor and automatically switches
        focus to it. If the label is not provided, an Untitled Document X one
        will be provided.
        """
        label = label or self._next_label()

        display = CodeDisplay(editor, self.refreshHandler, None)
        display.refresh()

        self.addTab(display, label)
        # Return value of addTab is not reliable when some tabs have been
        # closed, so we calculate it on our own, assuming all tabs are open on
        # on the right end.
        tab = self.count() - 1
        self.tabBar().add_close_button(tab)
        self.setCurrentIndex(tab)

    def new(self, event=None):
        """
        Creates a new tab with an empty editor.
        """
        self._add_editor(Editor.from_text(''))

    def open(self, event=None):
        """
        Creates a new tab with the editor containing the code from a file
        selected by the user.
        """
        path = str(QtGui.QFileDialog.getOpenFileName(self, filter='*.lua'))
        if path:
            self._add_editor(Editor.from_file(path), os.path.basename(path))

    def save_as(self, editor=None, name=''):
        """
        Saves the current editor contents into a file selected by the user.
        """
        if editor is None:
            editor = self.editor()

        new_path = str(QtGui.QFileDialog.getSaveFileName(self, dir=name, filter="*.lua"))
        if new_path:
            self.editor().save_as(new_path)

    def save(self, event=None):
        """
        Saves the current editor contents into the file that it was loaded
        from.
        """
        self.editor().save()

    def undo(self, event=None):
        """
        Undoes the last operation in the current editor.
        """
        self.editor().undo()
        self.refreshHandler()

    def redo(self, event=None):
        """
        Redoes the last operation in the current editor.
        """
        self.editor().redo()
        self.refreshHandler()

    def parse(self, event=None):
        """
        Creates a new tab with the editor containing the code entered by the
        user in a dialog window (see tabbed_editor.CodeInput).
        """
        input_dialog = CodeInput()
        if input_dialog.exec_():
            self._add_editor(input_dialog.editor(), None)

    def execute(self, command):
        """
        Executes the given command on the current editor.
        """
        return self.editor().execute(command)

    def is_available(self, command):
        """
        Returns True if the given command can be executed on the current
        editor.
        """
        if self.editor():
            return self.editor().is_available(command)
        else:
            return False

    def refresh(self, event=None):
        """
        Refreshes the CodeDisplay instance inside the current tab.
        """
        if self.currentWidget() is None:
            return

        self.currentWidget().refresh()
