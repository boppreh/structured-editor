from PyQt4 import QtCore, QtGui, QtWebKit
from core.editor import Editor
from ast.lua_parser import parseFile, parseString
from ast.structures import Node

from core.commands import *

navigation_hotkeys = {
           QtCore.Qt.Key_Left: SelectParent, 
           QtCore.Qt.Key_Right: SelectChild, 
           QtCore.Qt.Key_Up: SelectPrevSibling, 
           QtCore.Qt.Key_Down: SelectNextSibling, 

           QtCore.Qt.Key_H: SelectParent, 
           QtCore.Qt.Key_L: SelectChild, 
           QtCore.Qt.Key_K: SelectPrevSibling, 
           QtCore.Qt.Key_J: SelectNextSibling, 
          }

navigation_commands_with_labels = [
                        (SelectParent, 'Parent'),
                        (SelectChild, 'Child'),
                        (SelectNextSibling, 'Next'),
                        (SelectPrevSibling, 'Previous'),
                       ]

editing_hotkeys = {
           QtCore.Qt.Key_D: Delete,

           QtCore.Qt.Key_C: Copy,
           QtCore.Qt.Key_X: Cut,
           QtCore.Qt.Key_V: Paste,

           QtCore.Qt.Key_U: MoveUp,
           QtCore.Qt.Key_M: MoveDown,
          }

editing_commands_with_labels = [
                        (Delete, 'Delete'),
                        (Copy, 'Copy'),
                        (Cut, 'Cut'),
                        (Paste, 'Paste'),
                        (MoveUp, 'Move up'),
                        (MoveDown, 'Move down'),
                       ]

class CodeDisplay(QtWebKit.QWebView):
    """
    Class for displaying source code from an editor with selected nodes 
    highlighted. Text is rendered as HTML.
    """
    def __init__(self, selectionHandler, parent=None):
        super(CodeDisplay, self).__init__(parent)

        self.selectionHandler = selectionHandler
        self.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        self.linkClicked.connect(self.selected)

    def selected(self, url):
        self.selectionHandler(self.node_dict[int(url.toString())])

    def color_tag(self, color):
        return ('<span style="background-color: {}">'.format(color),
                '</span>')

    def add_link(self, node, text, color_tag_tuple):
        open_color, close_color = color_tag_tuple
        open = '<a href="{id}" style="color: #000000; text-decoration: none">'
        close = '</a>'

        self.node_count += 1
        node_id = self.node_count
        self.node_dict[node_id] = node

        beginning = close + open_color + open.format(id=node_id)
        ending = close + close_color + open

        return beginning + text.format(id=node_id) + ending

    def wrapper(self, node, text):
        if node == editor.selected:
            color = self.color_tag('#95CAFF')
        elif node.parent == editor.selected.parent:
            color = self.color_tag('#CECECE')
        else:
            color = ('', '')

        return self.add_link(node, text or ' ', color)

    def render(self, editor):
        """ Renders editor state in this text. """
        self.node_count = 0
        self.node_dict = {}
        text = editor.render(self.wrapper)
        self.setHtml('<pre><a>' + text + '</a></pre>')


class SourceCodeInput(QtGui.QDialog):
    """ Dialog for inputing a program as text. """
    def __init__(self, parent=None):
        super(SourceCodeInput, self).__init__(parent)

        self.setWindowTitle("Source code input")

        self.textedit = QtGui.QPlainTextEdit(self)

        buttons = QtGui.QDialogButtonBox()
        buttons.setOrientation(QtCore.Qt.Horizontal)
        buttons.setStandardButtons(QtGui.QDialogButtonBox.Cancel |
                                   QtGui.QDialogButtonBox.Ok)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.textedit, 0, 0, 1, 1)
        layout.addWidget(buttons, 1, 0, 1, 1)

    def getText(self):
        """ Returns the text entered by the user. """
        return str(self.textedit.toPlainText())


class CommandsWindow(QtGui.QDockWidget):
    def __init__(self, title, parent):
        super(CommandsWindow, self).__init__(title, parent)

        verticalCommands = QtGui.QWidget(self)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setAlignment(QtCore.Qt.AlignTop)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)

        verticalCommands.setLayout(self.verticalLayout)
        self.setObjectName(title)
        self.setWidget(verticalCommands)

        self.show()
        self.reset()

    def makeCommandButton(self, command, label, layout, handler):
        button = QtGui.QPushButton(label)
        button.pressed.connect(lambda: handler(command))
        self.buttonsByCommand[command.__class__] = button
        layout.addWidget(button)

    def addCommands(self, commands_with_labels, hotkeys, handler):
        self.buttonsByCommand = {}

        for command_class, label in commands_with_labels:
            self.makeCommandButton(command_class(), label,
                                   self.verticalLayout, handler)

        for key, command_class in hotkeys.items():
            QtGui.QShortcut(key, self,
                            self.buttonsByCommand[command_class].animateClick)

    def refresh(self, editor):
        for command, button in self.buttonsByCommand.items():
            button.setEnabled(command().is_available(editor))

    def reset(self):
        self.parent().addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
        self.setFloating(False)


import re
class InsertionWindow(CommandsWindow):
    def __init__(self, handler, parent):
        super(InsertionWindow, self).__init__('Insertion', parent)
        self.handler = handler
        self.buttonsByCommand = {}

    def refresh(self, editor):
        for button in self.buttonsByCommand.values():
            button.setParent(None)
        self.buttonsByCommand = {}

        index = editor.selected.selected_index
        for class_ in editor.selected.get_available_classes(index):
            if class_.abstract:
                continue

            label = re.findall("'(.+?)'", str(class_))[0].split('.')[-1]
            button = QtGui.QPushButton(label)
            button.pressed.connect(lambda class_=class_: self.handler(Insert(class_)))
            self.buttonsByCommand[class_] = button
            self.verticalLayout.addWidget(button)
            button.setEnabled(hasattr(editor.selected, 'append'))


class MainEditorWindow(QtGui.QMainWindow):
    def __init__(self, editor, file_selected):
        super(MainEditorWindow, self).__init__()

        self.editor = editor
        self.file_selected = file_selected

        self.editingWindow = CommandsWindow('Editing', self)
        self.editingWindow.addCommands(editing_commands_with_labels,
                                       editing_hotkeys, self.runCommand)

        self.navigationWindow = CommandsWindow('Navigation', self)
        self.navigationWindow.addCommands(navigation_commands_with_labels,
                                          navigation_hotkeys, self.runCommand)

        self.insertionWindow = InsertionWindow(self.runCommand, self)

        self.createMenu()
        self.statusBar()

        self.display = CodeDisplay(self.selectNode)
        self.setCentralWidget(self.display)

        self.setWindowTitle("Structured Editor")

        self.settings = QtCore.QSettings("TCC", "Editor Estruturado")
        self.restoreSettings()

        self.refresh()

    def createMenu(self):
        self.menubar = self.menuBar()
        fileMenu = self.menubar.addMenu('&File')

        def makeMenuAction(label, shortcut, statusTip, handler, menu):
            menu.addAction(QtGui.QAction(label, self, shortcut=shortcut,
                                         statusTip=statusTip, triggered=handler))

        makeMenuAction("&New...", "Ctrl+N", "Creates a new empty document.", self.new, fileMenu)
        makeMenuAction("&Open...", "Ctrl+O", "Open an existing source code file.", self.open, fileMenu)
        makeMenuAction("&Parse text...", "Ctrl+T", "Open a source code text by typing it in a temporary window.", self.parseText, fileMenu)
        fileMenu.addSeparator()
        makeMenuAction("&Save", "Ctrl+S", "Save the current source code back to the file it came from.", self.save, fileMenu)
        makeMenuAction("&Save as...", "Ctrl+Alt+S", "Save the current source code to a different file.", self.saveAs, fileMenu)
        fileMenu.addSeparator()
        makeMenuAction("&Quit", "Ctrl+Q", "Close the application.", self.close, fileMenu)

        viewMenu = self.menubar.addMenu("&View")
        makeMenuAction("&Navigation window", "Alt+N", "Show the navigation floating window.", self.navigationWindow.show, viewMenu)
        makeMenuAction("&Editing window", "Alt+E", "Show the editing floating window.", self.editingWindow.show, viewMenu)
        makeMenuAction("&Insertion window", "Alt+I", "Shows the insertion floating window", self.insertionWindow.show, viewMenu)
        viewMenu.addSeparator()
        makeMenuAction("&Reset window state", "Alt+R",
                            "Reset the window and commands bar size and state back to the original settings.", self.resetWindow, viewMenu)

        #updatesMenu = self.menubar.addMenu("&Updates")
        #makeMenuAction("&Check for updates", "Alt+U", "Tries to download the latests version.", self.checkUpdates, updatesMenu)

    def new(self, event=None):
        path_selected = None
        self.editor = Editor(parseString(""))
        self.refresh()

    def open(self, event=None):
        path_selected = str(QtGui.QFileDialog.getOpenFileName(self, filter='*.lua'))
        
        if not path_selected:
            return

        self.file_selected = path_selected
        self.editor = Editor(parseFile(self.file_selected))
        self.refresh()

    def parseText(self, event=None):
        input_dialog = SourceCodeInput()

        if not input_dialog.exec_():
            # User cancelled the action.
            return

        try:
            root = parseString(input_dialog.getText())
        except:
            QtGui.QMessageBox.critical(self, "Parsing error", "Could not parse the given text.")
            return

        self.editor = Editor(root)
        self.refresh()

    def saveAs(self, event=None):
        self.file_selected = str(QtGui.QFileDialog.getSaveFileName(self, filter="*.lua"))
        self.save()

    def save(self, event=None):
        if not self.file_selected:
            return

        with open(self.file_selected, 'w') as target_file:
            target_file.write(self.editor.render())

    def checkUpdates(self, event=None):
        reply = QtGui.QMessageBox.question(self, "Update", "Do you want to download the new version and restart the application?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.No:
            return

        import urllib, os
        urllib.urlretrieve ("http://www.inf.ufsc.br/~lucasboppre/Editor.exe", "Editor_new.exe")
        os.remove('Editor.exe')
        os.rename('Editor_new.exe', 'Editor.exe')
        os.execv('Editor.exe', [''])

    def resetWindow(self, event=None):
        self.navigationWindow.reset()
        self.editingWindow.reset()

        self.settings.clear()
        self.settings.sync()
        self.restoreSettings()

    def restoreSettings(self):
        # Bug: when the geometry is empty, the commands bar is not shown by default.
        # This is a workaround that detects if there are settings saved and, if not,
        # forces the display of the commands bar.
        if len(self.settings.value("geometry").toByteArray()) == 0:
            self.editingWindow.show()
            self.navigationWindow.show()

        self.restoreGeometry(self.settings.value("geometry").toByteArray())
        self.restoreState(self.settings.value("state").toByteArray())

    def closeEvent(self, event):
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('state', self.saveState())
        QtGui.QMainWindow.closeEvent(self, event)

    def selectNode(self, node):
        self.editor.selected = node
        self.refresh()

    def runCommand(self, command):
        command.execute(self.editor)
        self.refresh()

    def refresh(self):
        self.display.render(self.editor)

        selected_class = str(self.editor.selected.__class__).split('.')[-1][:-2]
        self.statusBar().showMessage(selected_class)

        self.navigationWindow.refresh(self.editor)
        self.editingWindow.refresh(self.editor)
        self.insertionWindow.refresh(self.editor)

if __name__ == '__main__':
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

    app = QtGui.QApplication(sys.argv)
    editor = Editor(parseString(test_program))
    mainWin = MainEditorWindow(editor, None)
    mainWin.show()
    sys.exit(app.exec_())
