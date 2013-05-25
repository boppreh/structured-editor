from PyQt4 import QtCore, QtGui
from ConfigParser import RawConfigParser
import re
import string

from update import update_and_restart, can_update
from tabbed_editor import TabbedEditor
from core.actions import *

def class_label(node_type):
    return re.sub('(?<!^)([A-Z])', r' \1', node_type.__name__)


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
    def __init__(self, handler, hotkeys, parent):
        super(InsertionWindow, self).__init__('Insertion', parent)
        self.handler = handler
        self.buttonsByCommand = {}
        self.buttonsByLetter = {}
        self.hotkeys = hotkeys

        for letter in hotkeys:
            def shorcut_handler(letter=letter):
                if letter in self.buttonsByLetter:
                    self.buttonsByLetter[letter].animateClick()
            QtGui.QShortcut(letter, self, shorcut_handler)

    def addCommand(self, i, class_):
        hotkey = self.hotkeys[i]
        button = QtGui.QPushButton('{} - {}'.format(hotkey, class_label(class_)))
        self.verticalLayout.addWidget(button)

        button.pressed.connect(lambda c=class_: self.handler(Insert(c)))

        self.buttonsByCommand[class_] = button
        self.buttonsByLetter[hotkey] = button

    def refresh(self, editor):
        for button in self.buttonsByCommand.values():
            button.setParent(None)
        self.buttonsByCommand = {}

        try:
            parent = editor.selected.parent
            assert parent
        except:
            return

        index = parent.index(editor.selected)
        is_concrete = lambda(class_): (hasattr(class_, 'abstract') and
                                       not class_.abstract)
        classes = filter(is_concrete, parent.get_available_classes(index))
        for i, class_ in enumerate(classes):
            self.addCommand(i, class_)


class MainEditorWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainEditorWindow, self).__init__()
        #self.setCentralWidget(self.display)
        self.tabbedEditor = TabbedEditor(self.refresh, self)

        self.setCentralWidget(self.tabbedEditor)

        self.createDocks()
        self.createMenu()
        self.statusBar()

        self.setWindowTitle("Structured Editor")

        self.settings = QtCore.QSettings("TCC", "Editor Estruturado")
        self.restoreSettings()

    def createDocks(self):
        config = RawConfigParser()
        config.read('theme.ini')

        def ask_for_name(r, old_name):
            name, ok = QtGui.QInputDialog.getText(self, 'Rename',
                                                  'Enter a new name',
                                                  text=old_name)
            name = str(name)
            if not ok or name[0] in string.digits:
                return old_name

            allowed_chars = string.lowercase + string.digits + ' _'
            return filter(allowed_chars.__contains__, name.replace(' ', '_'))

        Rename.ask_for_name = ask_for_name

        def extractHotkeys(group, pairs):
            return {config.get(group, label): item for item, label in pairs}

        editing_label_pairs = [(Delete, 'Delete'),
                               (Copy, 'Copy'),
                               (Cut, 'Cut'),
                               (Paste, 'Paste'),
                               (MoveUp, 'Move up'),
                               (MoveDown, 'Move down'),
                               (Rename, 'Rename')]
        self.editingWindow = CommandsWindow('Editing', self)
        self.editingWindow.addCommands(editing_label_pairs,
                                       extractHotkeys('Editing Hotkeys',
                                                      editing_label_pairs),
                                       self.runCommand)

        movement_label_pairs = [(SelectParent, 'Parent'),
                                (SelectChild, 'Child'),
                                (SelectNextSibling, 'Next'),
                                (SelectPrevSibling, 'Previous')]
        self.navigationWindow = CommandsWindow('Navigation', self)
        self.navigationWindow.addCommands(movement_label_pairs,
                                          extractHotkeys('Movement Hotkeys',
                                                         movement_label_pairs),
                                          self.runCommand)

        insertionHotkeys = [value for i, value in
                            config.items('Insertion Hotkeys')]
        self.insertionWindow = InsertionWindow(self.runCommand,
                                               insertionHotkeys, self)

        self.setDockNestingEnabled(True)

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
        self.save_menu = makeMenuAction("&Save", "Ctrl+S",
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
        self.undo_menu = makeMenuAction("&Undo", "Ctrl+Z",
                                        "Reverts the last change.",
                                        editMenu, self.tabbedEditor.undo)
        self.redo_menu = makeMenuAction("&Redo", "Ctrl+Shift+Z",
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
        for i in range(self.tabbedEditor.count()):
            if not self.tabbedEditor.widget(i).can_close():
                event.ignore()
                return
        QtGui.QMainWindow.closeEvent(self, event)

    def runCommand(self, command):
        self.tabbedEditor.execute(command)

    def refresh(self):
        editor = self.tabbedEditor.editor()
        if not editor:
            return

        self.navigationWindow.refresh(self.tabbedEditor.editor())
        self.editingWindow.refresh(self.tabbedEditor.editor())
        self.insertionWindow.refresh(self.tabbedEditor.editor())

        title_template = '{} - Structured Editor'
        title = title_template.format(editor.name)
        self.setWindowTitle(title)

        self.statusBar().showMessage(class_label(type(editor.selected)))

        self.save_menu.setEnabled(self.tabbedEditor.can_save())
        self.undo_menu.setEnabled(self.tabbedEditor.can_undo())
        self.redo_menu.setEnabled(self.tabbedEditor.can_redo())
