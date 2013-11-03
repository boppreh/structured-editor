import sip
sip.setapi('QString', 2)

from PyQt4 import QtGui
import sys

from gui.window import MainEditorWindow
from gui.html_editor import HtmlEditor

app = QtGui.QApplication(sys.argv)
mainWin = MainEditorWindow()

files = sys.argv[1:] or ["test_files/full.lua"]
for path in files:
    mainWin.tabbedEditor.add(HtmlEditor.from_file(path))

#mainWin.setWindowIcon(QtGui.QIcon('editor.ico'))
mainWin.show()
sys.exit(app.exec_())
