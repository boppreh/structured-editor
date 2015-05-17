from PyQt5 import QtGui, QtWidgets
import sys

from gui.window import MainEditorWindow
from gui.html_editor import HtmlEditor

app = QtWidgets.QApplication(sys.argv)
mainWin = MainEditorWindow()

files = sys.argv[1:] or [__file__]
for path in files:
    mainWin.tabbedEditor.add(HtmlEditor.from_file(path))

#mainWin.setWindowIcon(QtGui.QIcon('editor.ico'))
mainWin.show()
sys.exit(app.exec_())
