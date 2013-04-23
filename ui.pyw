from PyQt4 import QtCore, QtGui, QtWebKit
from core.editor import Editor
from ast.lua_parser import parseFile, parseString
from pyparsing import ParseException

from core.actions import *

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
        #return open_color + text + close_color

        open = '<a href="{id}" style="color: #000000; text-decoration: none">'
        close = '</a>'

        self.node_count += 1
        node_id = self.node_count
        self.node_dict[node_id] = node

        # Yep, it starts with a close link tag and ends with an opening link
        # tag without id. The goal is to eliminate nested link tags, so we
        # close the parent's whenever we start a new object and reopen
        # again when we finish. Since we don't know the parent id, leave it as
        # a template for it to fill.
        # Also, the color must be between the parent's tag and the child's tag,
        # to avoid invalid markup like <a><span></a></span>.
        beginning = close + open_color + open.format(id=node_id)
        ending = close + close_color + open

        # Here the parent fills the template left by its children.
        return beginning + text.format(id=node_id) + ending

    def wrapper(self, node, text):
        if node == editor.selected:
            color_tags = self.color_tag('#95CAFF')
        elif node.parent == editor.selected.parent:
            color_tags = self.color_tag('#CECECE')
        else:
            color_tags = ('', '')

        return self.add_link(node, text or ' ', color_tags)

    def render(self, editor):
        """ Renders editor state in this text. """
        self.node_count = 0
        self.node_dict = {}
        text = editor.render(self.wrapper)
        self.setHtml('<pre><a>' + text + '</a></pre>')


class CodeInput(QtGui.QDialog):
    """ Dialog for inputing a program as text. """
    def __init__(self, parent=None):
        super(CodeInput, self).__init__(parent)

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

    def accept(self):
        try:
            self.root = parseString(self.getText())
            super(CodeInput, self).accept()
        except ParseException:
            QtGui.QMessageBox.critical(self, "Parsing error", "Could not parse the given text.")


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

    def makeCommandButton(self, command_class, label, layout, handler):
        button = QtGui.QPushButton(label)
        button.pressed.connect(lambda: handler(command_class()))
        self.buttonsByCommand[command_class] = button
        layout.addWidget(button)

    def addCommands(self, commands_with_labels, hotkeys, handler):
        self.buttonsByCommand = {}

        for command_class, label in commands_with_labels:
            self.makeCommandButton(command_class, label,
                                   self.verticalLayout, handler)

        for key, command_class in hotkeys.items():
            QtGui.QShortcut(key, self,
                            self.buttonsByCommand[command_class].animateClick)

    def refresh(self, editor):
        for command, button in self.buttonsByCommand.items():
            button.setEnabled(editor.is_available(command()))

    def reset(self):
        self.parent().addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
        self.setFloating(False)


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

            button = QtGui.QPushButton(class_.__name__)
            button.pressed.connect(lambda class_=class_: self.handler(Insert(class_)))
            self.buttonsByCommand[class_] = button
            self.verticalLayout.addWidget(button)
            button.setEnabled(hasattr(editor.selected, 'append'))


class MainEditorWindow(QtGui.QMainWindow):
    def __init__(self, editor):
        super(MainEditorWindow, self).__init__()

        self.editor = editor

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

        def makeMenuAction(label, shortcut, statusTip, handler, menu):
            menu.addAction(QtGui.QAction(label, self, shortcut=shortcut,
                                         statusTip=statusTip, triggered=handler))

        fileMenu = self.menubar.addMenu('&File')
        makeMenuAction("&New", "Ctrl+N", "Creates a new empty document.", self.new, fileMenu)
        fileMenu.addSeparator()
        makeMenuAction("&Open...", "Ctrl+O", "Open an existing source code file.", self.open, fileMenu)
        makeMenuAction("&Parse text...", "Ctrl+T", "Open a source code text by typing it in a temporary window.", self.parseText, fileMenu)
        fileMenu.addSeparator()
        makeMenuAction("&Save", "Ctrl+S", "Save the current source code back to the file it came from.", self.save, fileMenu)
        makeMenuAction("&Save as...", "Ctrl+Alt+S", "Save the current source code to a different file.", self.saveAs, fileMenu)
        fileMenu.addSeparator()
        makeMenuAction("&Quit", "Ctrl+Q", "Close the application.", self.close, fileMenu)

        editMenu = self.menubar.addMenu('&Edit')
        makeMenuAction("&Undo", "Ctrl+Z", "Reverts the last change.", self.undo, editMenu)
        makeMenuAction("&Redo", "Ctrl+Shift+Z", "Executes the last change undone", self.redo, editMenu)

        viewMenu = self.menubar.addMenu("&View")
        makeMenuAction("&Navigation window", "Alt+N", "Show the navigation floating window.", self.navigationWindow.show, viewMenu)
        makeMenuAction("&Editing window", "Alt+E", "Show the editing floating window.", self.editingWindow.show, viewMenu)
        makeMenuAction("&Insertion window", "Alt+I", "Shows the insertion floating window", self.insertionWindow.show, viewMenu)
        viewMenu.addSeparator()
        makeMenuAction("&Reset window state", "Alt+R",
                            "Reset the window and commands bar size and state back to the original settings.", self.resetWindow, viewMenu)

        #updatesMenu = self.menubar.addMenu("&Updates")
        #makeMenuAction("&Check for updates", "Alt+U", "Tries to download the latests version.", self.checkUpdates, updatesMenu)

    def undo(self, event=None):
        self.editor.undo()
        self.refresh()

    def redo(self, event=None):
        self.editor.redo()
        self.refresh()

    def new(self, event=None):
        self.editor = Editor.from_text("")
        self.refresh()

    def open(self, event=None):
        path_selected = str(QtGui.QFileDialog.getOpenFileName(self, filter='*.lua'))
        
        if not path_selected:
            return

        self.editor = Editor.from_file(path_selected)
        self.refresh()

    def parseText(self, event=None):
        input_dialog = CodeInput()

        if not input_dialog.exec_():
            # User cancelled the action.
            return

        self.editor = Editor(input_dialog.root, None)
        self.refresh()

    def saveAs(self, event=None):
        new_path = str(QtGui.QFileDialog.getSaveFileName(self, filter="*.lua"))
        self.editor.save_as(new_path)

    def save(self, event=None):
        self.editor.save()

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
        self.editor.execute(Select(node))
        self.refresh()

    def runCommand(self, command):
        editor.execute(command)
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
    #test_program = """a = 5"""

    app = QtGui.QApplication(sys.argv)
    editor = Editor.from_text(test_program)
    mainWin = MainEditorWindow(editor)
    mainWin.show()
    sys.exit(app.exec_())
