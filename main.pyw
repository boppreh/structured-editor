from PyQt4 import QtGui
import sys

from gui.window import MainEditorWindow
from gui.html_editor import HtmlEditor

test_program = """
function allwords ()
    local line = io.read()
    local pos = 1
    return function ()
        while line do  
            local s, e = string.find(line, "%w+", pos)
            if s then   
                pos = e
                return string.sub(line, s, e) 
            else
                line = io.read()
                pos = 1        
                return false
            end
        end
        return nil        
    end
end


for word in allwords() do
    print(word)
end
"""
#test_program = """a = 5"""

app = QtGui.QApplication(sys.argv)
mainWin = MainEditorWindow()

files = sys.argv[1:]
if files:
    for path in files:
        mainWin.tabbedEditor.add(HtmlEditor.from_file(path))
else:
    mainWin.tabbedEditor.add(HtmlEditor.from_string(test_program, 'lua'))

#mainWin.setWindowIcon(QtGui.QIcon('editor.ico'))
mainWin.show()
sys.exit(app.exec_())
