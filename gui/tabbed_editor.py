from PyQt4 import QtCore, QtGui

import os

from pyparsing import ParseException

from code_display import CodeDisplay
from core.editor import Editor


class CodeInput(QtGui.QDialog):
    """ Dialog for inputing a program as text. """
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

    def getText(self):
        """ Returns the text entered by the user. """
        return str(self.textedit.toPlainText())

    def accept(self):
        try:
            self.editor = Editor.from_text(self.getText())
            super(CodeInput, self).accept()
        except ParseException:
            QtGui.QMessageBox.critical(self, "Parsing error", "Could not parse the given text.")


class CustomTabBar(QtGui.QTabBar):   
    def __init__(self, *args, **kargs):
        super(CustomTabBar, self).__init__(*args, **kargs)

        self.previous_index = -1

        self.currentChanged.connect(self._update_tab)

    def close_tab(self, tab=None):
        if tab is None:
            tab = self.currentIndex()

        if tab != -1:
            self.removeTab(tab)
            self._update_tab()

    def _update_tab(self, new_tab=None):
        self.hide_close_button(self.previous_index)
        self.show_close_button(self.currentIndex())

        self.previous_index = self.currentIndex()

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
        #closeButton.setShortcut('Ctrl+W')
        closeButton.setFlat(True)
        return closeButton

    def add_close_button(self, tab):
        self.setTabButton(tab, QtGui.QTabBar.RightSide,
                          self._make_close_button())

    def _get_close_button(self, tab):
        return self.tabButton(tab, QtGui.QTabBar.RightSide)

    def hide_close_button(self, tab):
        if self._get_close_button(tab):
            self._get_close_button(tab).hide()

    def show_close_button(self, tab):
        if self._get_close_button(tab):
            self._get_close_button(tab).show()


class TabbedEditor(QtGui.QTabWidget):
    def __init__(self, refreshHandler, parent):
        super(TabbedEditor, self).__init__(parent=parent)
        self.setMovable(True)
        self.setTabBar(CustomTabBar())

        self.untitled_tab_count = 0

        self.refreshHandler = refreshHandler

        QtGui.QShortcut('Ctrl+T', self, self.new)
        QtGui.QShortcut('Ctrl+W', self, self.tabBar().close_tab)

    def _next_label(self):
        self.untitled_tab_count += 1
        return 'Untitled Document ' + str(self.untitled_tab_count)

    def editor(self):
        if self.currentWidget():
            return self.currentWidget().editor
        else:
            return None

    def selected_node(self):
        if self.editor():
            return self.editor().selected
        else:
            return None

    def _add_editor(self, editor, label=None):
        label = label or self._next_label()

        display = CodeDisplay(editor, self.refreshHandler, None)
        display.refresh()

        self.addTab(display, label)
        tab = self.count() - 1
        self.tabBar().add_close_button(tab)
        self.setCurrentIndex(tab)
        return tab

    def new(self, event=None):
        tab = self._add_editor(Editor.from_text(''))
        self.setCurrentIndex(tab)
        self.refreshHandler()

    def open(self, event=None):
        path = str(QtGui.QFileDialog.getOpenFileName(self, filter='*.lua'))
        if path:
            self._add_editor(Editor.from_file(path), os.path.basename(path))
            self.refreshHandler()

    def save_as(self, event=None):
        new_path = str(QtGui.QFileDialog.getSaveFileName(self, filter="*.lua"))
        if new_path:
            self.editor().save_as(new_path)
            self.refreshHandler()

    def save(self, event=None):
        self.editor().save()
        self.refreshHandler()

    def undo(self, event=None):
        self.editor().undo()
        self.refreshHandler()

    def redo(self, event=None):
        self.editor().redo()
        self.refreshHandler()

    def parse(self, event=None):
        input_dialog = CodeInput()
        if input_dialog.exec_():
            self._add_editor(input_dialog.editor(), None)
            self.refreshHandler()

    def execute(self, command):
        return self.editor().execute(command)

    def is_available(self, command):
        if self.editor():
            return self.editor().is_available(command)
        else:
            return False

    def refresh(self, event=None):
        if self.currentWidget() is None:
            return

        self.currentWidget().refresh()
