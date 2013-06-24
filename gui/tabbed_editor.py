"""
Package for the tabbed features of the GUI editor. Each tab is able to display
a different Editor instance and allows for most actions a user may try:
repositioning tabs, close buttons, hotkeys (Ctrl+W and Ctrl+T), etc. "save",
"save as", "open", "parse" and "new" actions are self contained.
"""
from PyQt4 import QtCore, QtGui

from pyparsing import ParseException

from gui.html_editor import HtmlEditor

class CodeInput(QtGui.QDialog):
    """
    Dialog for inputing a program as text. The result is stored in the
    self.editor attribute, containing an entire Editor instance with no
    selected_file value.
    """
    def __init__(self, base_text='', parent=None):
        super(CodeInput, self).__init__(parent)

        self.setWindowTitle("Source code input")

        self.textedit = QtGui.QPlainTextEdit(self)
        self.textedit.setPlainText(base_text)

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
            self.editor = HtmlEditor.from_string(text, 'lua')
            super(CodeInput, self).accept()
        except ParseException:
            QtGui.QMessageBox.critical(self, "Parsing error", "Could not parse the given text.")


class CustomTabBar(QtGui.QTabBar):
    """
    Class for a Tab Bar with more usability options, such as an unobtrusive
    close button on the current tab, support for closing tabs with the middle
    mouse button and reordering tabs.
    """
    def __init__(self, close_tab, *args, **kargs):
        super(CustomTabBar, self).__init__(*args, **kargs)
        self.setMovable(True)

        self.close_tab = close_tab
        self.previous_index = -1

        self.currentChanged.connect(self._update_tab)
        self.tabCloseRequested.connect(self.close_tab)

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
    def __init__(self, refresh_handler=None, parent=None):
        super(TabbedEditor, self).__init__(parent=parent)
        self.setTabBar(CustomTabBar(self.close_tab))

        self.untitled_tab_count = 0

        self.refresh_handler = refresh_handler
        self.currentChanged.connect(self.refresh_handler)

        QtGui.QShortcut('Ctrl+T', self, self.new)
        QtGui.QShortcut('Ctrl+W', self, self.tabBar().close_tab)

    def editor(self):
        """
        Returns the current editor instance.
        """ 
        return self.widget(self.currentIndex())

    def close_tab(self, tab=None):
        """ Closes the tab at index "tab", if there is one. """
        if tab is None:
            tab = self.currentIndex()

        if tab != -1 and self.widget(tab).can_close():
            self.removeTab(tab)
            self.tabBar()._update_tab()
            return True
        else:
            return False

    def add(self, editor):
        """
        Creates a new tab to contain a given editor and automatically switches
        tab to it.
        """
        editor.refresh_handler = self.refresh_handler
        editor.refresh()

        # The return value of addTab is not reliable when some tabs have been
        # closed, so we calculate it on our own, assuming all tabs are open on
        # on the right end.
        tab = self.count()
        self.addTab(editor, editor.name)
        self.tabBar().add_close_button(tab)
        self.setCurrentIndex(tab)

    def new(self, language='lua'):
        """
        Creates a new tab with an empty editor.
        """
        self.add(HtmlEditor.new_empty(language))

    def open(self, event=None):
        """
        Creates a new tab with the editor containing the code from a file
        selected by the user.
        """
        filters = 'Lua files (*.lua);;JSON files (*.json);;All files (*.*)';
        path = str(QtGui.QFileDialog.getOpenFileName(self, filter=filters))
        if path is not None:
            self.add(HtmlEditor.from_file(path))

    def parse(self, event=None):
        """
        Creates a new tab with the editor containing the code entered by the
        user in a dialog window (see tabbed_editor.CodeInput).
        """
        input_dialog = CodeInput()
        if input_dialog.exec_():
            self.add(input_dialog.editor)
