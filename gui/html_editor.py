from PyQt4 import QtGui, QtWebKit
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QFileDialog
from ConfigParser import RawConfigParser
from time import time
from os.path import basename

from core.editor import Editor
from core.actions import Select

class GraphicalEditor(QtWebKit.QWebView, Editor):
    """
    Editor child with Qt graphical capabilities, such as save/save as dialogs
    and pretty name for showing to the user.
    """
    untitled_count = 0
    untitled_name_template = 'Untitled Document {}.lua'

    def __init__(self, root, selected_file, parent=None):
        QtWebKit.QWebView.__init__(self, parent)
        Editor.__init__(self, root, selected_file)

        if self.selected_file is None:
            GraphicalEditor.untitled_count += 1
            self.name = self.untitled_name_template.format(self.untitled_count)
        else:
            self.name = basename(self.selected_file)

    def can_close(self):
        if super(GraphicalEditor, self).can_close():
            return True
        else:
            return self._confirm_unsaved_changes()            

    def _confirm_unsaved_changes(self):
        message_template = 'Do you want to save changes to {}?'
        message = message_template.format(self.name)
        buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        result = QMessageBox.warning(self, 'Close confirmation',
                                     message, buttons=buttons)

        if result == QtGui.QMessageBox.Save:
            return self.save()
        elif result == QtGui.QMessageBox.Discard:
            return True
        elif result == QtGui.QMessageBox.Cancel:
            return False

    def save_as(self, path=None):
        """
        Saves the current editor contents into a file selected by the user.
        """
        if path is None:
            path = str(QFileDialog.getSaveFileName(self, 'Save as', self.name,
                                                   filter="*.lua"))

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
    def __init__(self, root, selected_file, refresh_handler=None, parent=None):
        super(HtmlEditor, self).__init__(root, selected_file, parent)

        self.refresh_handler = refresh_handler

        self.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        self.linkClicked.connect(self._selection_handler)

        self.lastClickTime = time()
        self.lastClickNode = None

        self.config = RawConfigParser()
        self.config.read('theme.ini')

    def node_style(self, node):
        """
        Returns the CSS to color the node according to its node type.
        """
        class_name = type(node).__name__.lower()
        try:
            return self.config.get('Structures', class_name)
        except:
            return self.config.get('Structures', 'default')

    def _selection_handler(self, url):
        """
        Select the node corresponding to the given url, or its parent when
        clicked multiple times.
        """
        node_id = int(basename(str(url.toString())))
        node_clicked = self.node_dict[node_id]
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

    def _span_tags(self, node):
        """
        Returns the opening and closing span tags containing the background
        style for the given node.
        """
        if node.parent == self.selected.parent:
            if node == self.selected:
                style = self.config.get('Selection', 'background')
            else:
                style = self.config.get('Selection', 'siblingsbackground')
            return '<span style="{}">'.format(style), '</span>'
        else:
            return '', ''

    def _link_tags(self, node):
        """
        Returns the opening and closing link tags, with user-specified style,
        for the given node.
        """
        template = '<a href="{}" style="text-decoration: none; {}">'
        return template.format(node.node_id, self.node_style(node)), '</a>'

    def _linked_template(self, node):
        """
        Returns the node's template with link and span tags added.
        """
        # Dictionary of all nodes and their corresponding urls, to be used when
        # the user clicks on any of the links.
        self.node_dict[node.node_id] = node

        if node.parent:
            parent_open, parent_close = self._link_tags(node.parent)
        else:
            parent_open, parent_close = '', ''

        open_a, close_a = self._link_tags(node)
        open_span, close_span = self._span_tags(node)

        try:
            template = self.config.get('Templates', type(node).__name__)
        except:
            template = node.template

        # Span tags change the background, but there's no background in empty
        # nodes. So we replace it with a single space.
        if open_span and len(node) == 0 and template == '{children}':
            template = '{children} '
        

        # Close parent's href tag to avoid nested links.
        return (parent_close + open_span + open_a +
                template +
                close_a + close_span + parent_open)

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
        self.node_dict = {}

        template = """<body style="{}"><pre style="{}">{}</pre></body>"""

        background = self.config.get('Global', 'background')
        font = self.config.get('Global', 'font')
        text = self.render_tree(self._linked_template)

        self.setHtml(template.format(background, font, text))

        self.refresh_handler()
