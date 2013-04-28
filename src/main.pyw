from PyQt4 import QtGui
from core.editor import Editor
from gui.window import MainEditorWindow
import sys

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
#mainWin.setWindowIcon(QtGui.QIcon('editor.ico'))
mainWin.tabbedEditor._add_editor(Editor.from_text(test_program))
mainWin.show()
sys.exit(app.exec_())
