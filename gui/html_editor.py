from PyQt5 import QtWebKit, QtCore
from PyQt5.QtWebKitWidgets import QWebView, QWebPage
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from time import time
from os import path
from sys import argv

from core.editor import Editor
from core.actions import Select
from core.html_renderer import LinkedRendering

class GraphicalEditor(Editor):
    """
    Editor child with Qt graphical capabilities, such as save/save as dialogs
    and pretty name for showing to the user.
    """
    untitled_count = 0
    untitled_name_template = 'Untitled Document {}.{}'

    def __init__(self, root, language, selected_file):
        Editor.__init__(self, root, language, selected_file)

        self.web = QWebView()
        self.web.setAcceptDrops(False)

        if self.selected_file is None:
            GraphicalEditor.untitled_count += 1
            template = self.untitled_name_template
            self.name = template.format(self.untitled_count, self.ext)
        else:
            self.name = path.basename(self.selected_file)

    def can_close(self):
        if super(GraphicalEditor, self).can_close():
            return True
        else:
            return self._confirm_unsaved_changes()            

    def _confirm_unsaved_changes(self):
        message_template = 'Do you want to save changes to {}?'
        message = message_template.format(self.name)
        buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        result = QMessageBox.warning(self.web, 'Close confirmation',
                                     message, buttons=buttons)

        if result == QMessageBox.Save:
            return self.save()
        elif result == QMessageBox.Discard:
            return True
        elif result == QMessageBox.Cancel:
            return False

    def save_as(self, path=None):
        """
        Saves the current editor contents into a file selected by the user.
        """
        if path is None:
            path = QFileDialog.getSaveFileName(self, 'Save as', self.name,
                                               filter='*.' + self.ext)

        if path:
            Editor.save_as(self, path)
            return True
        else:
            return False

    def save(self):
        """
        Saves the current editor into the original file or, if there isn't
        one, into a file selected by the user.
        """
        if self.can_save():
            super(GraphicalEditor, self).save()
            return True
        else:
            return self.save_as()


class HtmlEditor(GraphicalEditor):
    """
    Graphical editor that displays the code in HTML, allowing the user to click
    on the text to select nodes.
    """
    def __init__(self, root, language, selected_file, refresh_handler=None):
        super(HtmlEditor, self).__init__(root, language, selected_file)

        self.refresh_handler = refresh_handler

        self.web.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.web.linkClicked.connect(self._selection_handler)

        self.lastClickTime = time()
        self.lastClickNode = None

        style_css = path.abspath(path.join(path.dirname(argv[0]), 'config', 'style.css'))
        self.style_watcher = QtCore.QFileSystemWatcher(self.web)
        self.style_watcher.addPath(style_css)
        self.style_watcher.fileChanged.connect(self.style_updated)

        self.web.page().settings().setMaximumPagesInCache(0)
        self.web.page().settings().setObjectCacheCapacities(0, 0, 0)

        self.web.page().mainFrame().contentsSizeChanged.connect(self._auto_scroll)

    def _auto_scroll(self, contents_size):
        self.web.page().mainFrame().scrollToAnchor(str(self.selected.node_id))

    def style_updated(self, path):
        self.web.setHtml(self.rendering.html)
        
    def _selection_handler(self, url):
        """
        Select the node corresponding to the given url, or its parent when
        clicked multiple times.
        """
        node_id = int(path.basename(url.toString()))
        node_clicked = self.rendering.node_dict[node_id]
        node_selected = node_clicked

        time_elapsed = time() - self.lastClickTime 

        # Figures out if the user is quickly clicking the same node,
        # trying to get to the parent.
        if node_clicked == self.lastClickNode and time_elapsed < 1.5:
            node_parent = self.selected.parent
            if node_parent:
                node_selected = node_parent
            else:
                # If we circle back and select the most specific node, it
                # becomes confusing for the user that misclicks.
                node_selected = self.selected

        self.lastClickNode = node_clicked
        self.lastClickTime = time()

        self.execute(Select(node_selected))

    def execute(self, action):
        super(HtmlEditor, self).execute(action)
        self.refresh()

    def undo(self):
        super(HtmlEditor, self).undo()
        self.refresh()

    def redo(self):
        super(HtmlEditor, self).redo()
        self.refresh()

    def refresh(self):
        """
        Renders tree state in HTML.
        """
        self.rendering = LinkedRendering(self.root, self.selected)
        self.web.setHtml(self.rendering.html)
        self.refresh_handler()
