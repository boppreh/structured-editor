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
    def __init__(self, title):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle(title)
        self.setCentralWidget(Tabbed())
        self.untitled_count = 0
        QtGui.QShortcut('Ctrl+N', self, self.newDocument)
        self.toolbars = {}

    def addMenuAction(self, menu, action):
        raise NotImplemented()

    def addToolbarAction(self, toolbar_name, label, redo, undo=None):
        if toolbar_name not in self.toolbars:
            self.toolbars[toolbar_name] = self.addToolBar(toolbar_name)

        action = self.toolbars[toolbar_name].addAction(label)
        action.triggered.connect(redo)
        action.undo = undo

    def addDocument(self, text, label=None):
        if label is None:
            self.untitled_count += 1
            label = 'Untitled Document ' + str(self.untitled_count)

        contents = QtWebKit.QWebView()
        contents.setHtml(text)
        contents.undo_stack = QtGui.QUndoStack()
        return self.centralWidget().addTab(contents, label)

    def newDocument(self):
        self.addDocument('', None)


if __name__ == '__main__':
    import sys, os
    app = QtGui.QApplication([__file__])
    main_window = MainWindow('Structured Editor')
    main_window.addToolbarAction('Toolbar 1', 'A1', main_window.newDocument)
    main_window.addToolbarAction('Toolbar 1', 'A2', main_window.newDocument)
    main_window.addToolbarAction('Toolbar 2', 'B1', main_window.newDocument)
    main_window.addToolbarAction('Toolbar 2', 'B2', main_window.newDocument)

    for path in sys.argv[1:]:
        main_window.add(open(path).read(), os.path.basename(path))

    main_window.show()
    exit(app.exec_())
