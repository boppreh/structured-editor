from PyQt4 import QtCore, QtGui, QtWebKit

class Tabbed(QtGui.QTabWidget):
    def __init__(self, *args, **kargs):
        QtGui.QTabWidget.__init__(self, *args, **kargs)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.currentChanged.connect(self._update_tab)
        self.tabCloseRequested.connect(self._close_tab)
        QtGui.QShortcut('Ctrl+W', self,
                        lambda: self._close_tab(self.currentIndex()))

    def _update_tab(self, new_tab=None):
        for i in range(self.count()):
            button = self.tabBar().tabButton(i, QtGui.QTabBar.RightSide)
            if button:
                button.setVisible(i == self.currentIndex())

        self.tabBar().setVisible(self.count() > 1)

    def _close_tab(self, tab):
        self.removeTab(tab)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._close_tab(self.tabBar().tabAt(event.pos()))

        QtGui.QTabWidget.mouseReleaseEvent(self, event)

    def addTab(self, widget, title):
        QtGui.QTabWidget.addTab(self, widget, title)
        self._update_tab(-1)


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle('Structured Editor')

        self.addToolBar('Actions1').addAction('Action1')
        self.addToolBar('Actions2').addAction('Action2')

        self.setDockNestingEnabled(True)

        tabbed = Tabbed()
        self.setCentralWidget(tabbed)

        contents = QtWebKit.QWebView()
        contents.setHtml('<html>Hello World 1</html>')
        tabbed.addTab(contents, 'Tab1')
        contents = QtWebKit.QWebView()
        contents.setHtml('<html>Hello Rest 2</html>')
        tabbed.addTab(contents, 'Tab2')


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication([__file__])
    main_window = MainWindow()
    main_window.show()

    for path in sys.argv[1:]:
        print(path)
        #main_window.tabbedEditor.add(HtmlEditor.from_file(path))

    exit(app.exec_())
