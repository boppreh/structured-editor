from PyQt4 import QtCore, QtGui, QtWebKit

class Tabbed(QtGui.QTabWidget):
    """
    Tabbed interface with focus on usability:
    - tabs can be moved
    - the currently focused tab has a close button
    - Ctrl+W closes the current tab
    - the user can middle-click on a tab to close it
    - the tab bar is hidden when there's only one tab
    - when a tab is open, change to it
    """
    def __init__(self, *args, **kargs):
        QtGui.QTabWidget.__init__(self, *args, **kargs)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.currentChanged.connect(self._update_tab)
        self.tabCloseRequested.connect(self._close_tab)
        QtGui.QShortcut('Ctrl+W', self,
                        lambda: self._close_tab(self.currentIndex()))

    def _update_tab(self, new_tab=None):
        self.setCurrentIndex(new_tab)
        for i in range(self.count()):
            button = self.tabBar().tabButton(i, QtGui.QTabBar.RightSide)
            if button:
                button.setVisible(i == new_tab)

        self.tabBar().setVisible(self.count() > 1)

    def _close_tab(self, tab):
        self.removeTab(tab)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._close_tab(self.tabBar().tabAt(event.pos()))

        QtGui.QTabWidget.mouseReleaseEvent(self, event)

    def addTab(self, widget, title):
        self._update_tab(QtGui.QTabWidget.addTab(self, widget, title))


class MainWindow(QtGui.QMainWindow):
    """
    Class for a multi-document window, if automatic handling of actions and
    tabs.
    """
    def __init__(self, title):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle(title)
        self.setCentralWidget(Tabbed())

        self.untitled_count = 0
        self.toolbars = {}

        QtGui.QShortcut('Ctrl+N', self, self.newDocument)
        QtGui.QShortcut('Ctrl+Z', self,
                        lambda: self.currentDocument().undo_stack.undo())
        QtGui.QShortcut('Ctrl+Shift+Z', self,
                        lambda: self.currentDocument().undo_stack.redo())

    def addMenuAction(self, menu, action):
        raise NotImplemented()

    def addToolbarAction(self, toolbar_name, label, redo, undo=None):
        """
        Adds a new action to the given toolbar. The toolbar is created if
        necessary. By specifying an "undo" action, the action becomes tied to
        the document and can be undone.
        """
        if toolbar_name not in self.toolbars:
            self.toolbars[toolbar_name] = self.addToolBar(toolbar_name)

        action = self.toolbars[toolbar_name].addAction(label)
        if undo:
            def execute():
                command = QtGui.QUndoCommand()
                command.redo = redo
                command.undo = undo
                self.currentDocument().undo_stack.push(command)
            action.triggered.connect(execute)
        else:
            action.triggered.connect(redo)

    def addDocument(self, text, label=None):
        """
        Opens a new document in a new tab, displaying the given text as HTML.
        """
        if label is None:
            self.untitled_count += 1
            label = 'Untitled Document ' + str(self.untitled_count)

        contents = QtWebKit.QWebView()
        contents.setHtml(text)
        contents.undo_stack = QtGui.QUndoStack()
        self.centralWidget().addTab(contents, label)
        return contents

    def newDocument(self):
        """
        Opens a new empty document in a new tab.
        """
        return self.addDocument('', None)

    def currentDocument(self):
        """
        Returns the currently focused HTML widget.
        """
        return self.centralWidget().currentWidget()


if __name__ == '__main__':
    import sys, os
    app = QtGui.QApplication([__file__])
    main_window = MainWindow('Structured Editor')
    def a():
        print 'a'
    def b():
        print 'b'
    main_window.addToolbarAction('Toolbar 1', 'A1', a, b)
    main_window.addToolbarAction('Toolbar 1', 'A2', main_window.newDocument)
    main_window.addToolbarAction('Toolbar 2', 'B1', main_window.newDocument)
    main_window.addToolbarAction('Toolbar 2', 'B2', main_window.newDocument)

    for path in sys.argv[1:]:
        main_window.add(open(path).read(), os.path.basename(path))

    main_window.show()
    exit(app.exec_())
