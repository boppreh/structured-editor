from PyQt4 import QtCore, QtGui

import os

from code_display import CodeDisplay
from core.editor import Editor

class TabbedEditor(QtGui.QTabWidget):
    def __init__(self, refreshHandler, parent):
        super(TabbedEditor, self).__init__(parent=parent)
        self.setMovable(True)

        self.editor = None
        self.selected_node = None

        self.previous_index = -1

        self.refreshHandler = refreshHandler

        self.currentChanged.connect(self._updateTab)

    def _make_close_button(self):
        style = QtGui.qApp.style() 
        icon = style.standardIcon(style.SP_DockWidgetCloseButton) 
        closeButton = QtGui.QPushButton(icon, '') 
        closeButton.clicked.connect(self.close)
        closeButton.resize(12, 12)
        #closeButton.setShortcut('Ctrl+W')
        closeButton.setFlat(True)
        return closeButton

    def close(self, event=None):
        if self.currentIndex() != -1:
            self.removeTab(self.currentIndex())

    def _nextLabel(self):
        return 'Untitled Document ' + str(self.count() + 1)

    def _addEditor(self, editor, label=None):
        label = label or self._nextLabel()

        display = CodeDisplay(editor, self.refreshHandler, None)
        display.refresh()

        tab = self.addTab(display, label)
        self.tabBar().setTabButton(tab,
                                   QtGui.QTabBar.RightSide,
                                   self._make_close_button())

        return tab

    def get_tab_button(self, tab_index):
        return self.tabBar().tabButton(tab_index, QtGui.QTabBar.RightSide)

    def _updateTab(self, event=None):
        if self.currentWidget() is None:
            self.editor = None
            self.selected_node = None
            self.previous_index = -1
            return

        self.editor = self.currentWidget().editor
        self.selected_node = self.editor.selected

        if self.get_tab_button(self.currentIndex()):
            self.get_tab_button(self.currentIndex()).show()

        if self.previous_index != -1 and self.get_tab_button(self.previous_index):
            self.get_tab_button(self.previous_index).hide()

        self.previous_index = self.currentIndex()

    def refresh(self, event=None):
        if self.currentWidget() is None:
            return

        self.currentWidget().refresh()

    def new(self, event=None):
        self.setCurrentIndex(self._addEditor(Editor.from_text('')))
        self.refreshHandler()

    def open(self, event=None):
        path = str(QtGui.QFileDialog.getOpenFileName(self, filter='*.lua'))
        if path:
            self._addEditor(Editor.from_file(path), os.path.basename(path))
            self.refreshHandler()

    def save_as(self, event=None):
        new_path = str(QtGui.QFileDialog.getSaveFileName(self, filter="*.lua"))
        if new_path:
            self.editor.save_as(new_path)
            self.refreshHandler()

    def save(self, event=None):
        self.editor.save()
        self.refreshHandler()

    def undo(self, event=None):
        self.editor.undo()
        self.refreshHandler()

    def redo(self, event=None):
        self.editor.redo()
        self.refreshHandler()

    def parse(self, event=None):
        input_dialog = CodeInput()
        if input_dialog.exec_():
            self._add_Editor(Editor(input_dialog.root, None))
            self.refreshHandler()

    def execute(self, command):
        return self.editor.execute(command)

    def is_available(self, command):
        if self.editor:
            return self.editor.is_available(command)
        else:
            return False
