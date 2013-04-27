from PyQt4 import QtCore, QtGui

from update import update_and_restart, can_update

from tabbed_editor import TabbedEditor
from core.actions import *

navigation_hotkeys = {
                      "Left": SelectParent,
                      "Right": SelectChild,
                      "Up": SelectPrevSibling,
                      "Down": SelectNextSibling,
                     }

navigation_commands_with_labels = [
                                   (SelectParent, 'Parent'),
                                   (SelectChild, 'Child'),
                                   (SelectNextSibling, 'Next'),
                                   (SelectPrevSibling, 'Previous'),
                                  ]

editing_hotkeys = {
                   "Ctrl+D": Delete,

                   "Ctrl+C": Copy,
                   "Ctrl+X": Cut,
                   "Ctrl+V": Paste,

                   "Ctrl+U": MoveUp,
                   "Ctrl+M": MoveDown,
                  }

editing_commands_with_labels = [
                                (Delete, 'Delete'),
                                (Copy, 'Copy'),
                                (Cut, 'Cut'),
                                (Paste, 'Paste'),
                                (MoveUp, 'Move up'),
                                (MoveDown, 'Move down'),
                               ]

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

        node = editor.selected_node()
        if node is None:
            return

        index = node.selected_index
        for class_ in editor.selected_node().get_available_classes(index):
            if class_.abstract:
                continue

            button = QtGui.QPushButton(class_.__name__)
            button.pressed.connect(lambda class_=class_: self.handler(Insert(class_)))
            self.buttonsByCommand[class_] = button
            self.verticalLayout.addWidget(button)
            button.setEnabled(hasattr(editor.selected_node(), 'append'))


class MainEditorWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainEditorWindow, self).__init__()
        #self.setCentralWidget(self.display)
        self.tabbedEditor = TabbedEditor(self.refresh, self)

        self.setCentralWidget(self.tabbedEditor)

        self.editingWindow = CommandsWindow('Editing', self)
        self.editingWindow.addCommands(editing_commands_with_labels,
                                       editing_hotkeys, self.runCommand)

        self.navigationWindow = CommandsWindow('Navigation', self)
        self.navigationWindow.addCommands(navigation_commands_with_labels,
                                          navigation_hotkeys, self.runCommand)

        self.insertionWindow = InsertionWindow(self.runCommand, self)

        self.setDockNestingEnabled(True)

        self.createMenu()
        self.statusBar()

        self.setWindowTitle("Structured Editor")

        self.settings = QtCore.QSettings("TCC", "Editor Estruturado")
        self.restoreSettings()

        self.refresh()

    def createMenu(self):
        self.menubar = self.menuBar()

        def makeMenuAction(label, shortcut, statusTip, menu, handler):
            action = QtGui.QAction(label, self, shortcut=shortcut,
                                   statusTip=statusTip, triggered=handler)
            menu.addAction(action)
            return action

        fileMenu = self.menubar.addMenu('&File')
        makeMenuAction("&New", "Ctrl+N",
                       "Creates a new empty document.",
                       fileMenu, self.tabbedEditor.new)
        fileMenu.addSeparator()
        makeMenuAction("&Open...", "Ctrl+O",
                       "Open an existing source code file.",
                       fileMenu, self.tabbedEditor.open)
        makeMenuAction("&Parse text...", "",
                       "Open a source code text by typing it in a temporary "
                       "window.",
                       fileMenu, self.tabbedEditor.parse)
        fileMenu.addSeparator()
        makeMenuAction("&Save", "Ctrl+S",
                       "Save the current source code back to the file it came "
                       "from.",
                       fileMenu, self.tabbedEditor.save)
        makeMenuAction("&Save as...", "Ctrl+Alt+S",
                       "Save the current source code to a different file.",
                       fileMenu, self.tabbedEditor.save_as)
        fileMenu.addSeparator()
        makeMenuAction("&Quit", "Ctrl+Q",
                       "Close the application.",
                       fileMenu, self.close)

        editMenu = self.menubar.addMenu('&Edit')
        makeMenuAction("&Undo", "Ctrl+Z",
                       "Reverts the last change.",
                       editMenu, self.tabbedEditor.undo)
        makeMenuAction("&Redo", "Ctrl+Shift+Z",
                       "Executes the last change undone",
                       editMenu, self.tabbedEditor.redo)

        viewMenu = self.menubar.addMenu("&View")
        makeMenuAction("&Navigation window", "Alt+N",
                       "Show the navigation floating window.",
                       viewMenu, self.navigationWindow.show)
        makeMenuAction("&Editing window", "Alt+E",
                       "Show the editing floating window.",
                       viewMenu, self.editingWindow.show)
        makeMenuAction("&Insertion window", "Alt+I",
                       "Shows the insertion floating window",
                       viewMenu, self.insertionWindow.show)
        viewMenu.addSeparator()
        makeMenuAction("&Reset window state", "Alt+R",
                       "Reset the window and commands bar size and state back to the original settings.",
                       viewMenu, self.resetWindow)

        updatesMenu = self.menubar.addMenu("&Updates")

        if can_update('http://www.inf.ufsc.br/~lucasboppre/Editor.exe'):
            makeMenuAction("&Download latest version", "Alt+D",
                           "Tries to download the latest version from a remote server.",
                           updatesMenu, self.update)
        else:
            makeMenuAction("No updates available.", "",
                           "", updatesMenu, lambda: None).setEnabled(False)

    def update(self):
        reply = QtGui.QMessageBox.question(self, "Update", "Do you want to download the new version and restart the application?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.No:
            return

        class Updater(QtCore.QThread):
            def run(self):
                update_and_restart('http://www.inf.ufsc.br/~lucasboppre/Editor.exe')

        progressDialog = QtGui.QProgressDialog("Downloading latest version...",
                                               "", 0, 0, self)
        progressDialog.setCancelButton(None)
        progressBar = QtGui.QProgressBar(progressDialog)
        progressBar.setMinimum(0)
        progressBar.setMaximum(0)
        progressDialog.setBar(progressBar)
        progressDialog.show()
        updater = Updater()
        updater.finished.connect(progressDialog.close)
        updater.finished.connect(QtGui.QApplication.quit)
        updater.start()
        # Saving reference to avoid garbage collection.
        self.updater = updater

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

    def runCommand(self, command):
        self.tabbedEditor.execute(command)
        self.refresh()

    def refresh(self):
        self.tabbedEditor.refresh()

        self.navigationWindow.refresh(self.tabbedEditor)
        self.editingWindow.refresh(self.tabbedEditor)
        self.insertionWindow.refresh(self.tabbedEditor)

        title = '{} - Structured Editor'.format(self.tabbedEditor.label())
        self.setWindowTitle(title)
