from PyQt4 import QtGui
import sys

from gui.window import MainEditorWindow
from gui.html_editor import HtmlEditor

#test_program = """a = 5"""

app = QtGui.QApplication(sys.argv)
mainWin = MainEditorWindow()

files = sys.argv[1:] or ["test_files/full.lua"]
if files:
    for path in files:
        mainWin.tabbedEditor.add(HtmlEditor.from_file(path))

#mainWin.setWindowIcon(QtGui.QIcon('editor.ico'))
mainWin.show()
sys.exit(app.exec_())
