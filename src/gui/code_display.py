from PyQt4 import QtCore, QtGui, QtWebKit
from time import time
from core.actions import Select

class CodeDisplay(QtWebKit.QWebView):
    """
    Class for displaying source code from an editor with selection_handler nodes 
    highlighted. Text is rendered as HTML.
    """
    def __init__(self, editor, refreshHandler, parent=None):
        super(CodeDisplay, self).__init__(parent)

        self.editor = editor
        self.refreshHandler = refreshHandler

        self.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        self.linkClicked.connect(self.selection_handler)

        self.lastClickTime = time()
        self.lastClickNode = None

    def selection_handler(self, url):
        node_clicked = self.node_dict[int(url.toString())]
        node_selected = node_clicked

        time_elapsed = time() - self.lastClickTime 

        # Figures out if the user is quickly clicking the same node,
        # trying to get to the parent.
        if node_clicked == self.lastClickNode and time_elapsed < 1.5:
            node_parent = self.editor.selected.parent
            if node_parent:
                node_selected = node_parent
            else:
                # If we circle back and select the most specific node, it
                # becomes confusing for the user that misclicks.
                node_selected = self.editor.selected

        self.lastClickNode = node_clicked
        self.lastClickTime = time()

        self.editor.execute(Select(node_selected))
        self.refreshHandler()

    def _color_tag(self, color):
        return ('<span style="background-color: {}">'.format(color),
                '</span>')

    def _add_link(self, node, text, color_tag_tuple):
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

    def _wrapper(self, node, text):
        if node == self.editor.selected:
            color_tags = self._color_tag('#95CAFF')
        elif node.parent == self.editor.selected.parent:
            color_tags = self._color_tag('#CECECE')
        else:
            color_tags = ('', '')

        return self._add_link(node, text or ' ', color_tags)

    def refresh(self):
        """ Renders editor state in this text. """
        self.node_count = 0
        self.node_dict = {}
        text = self.editor.render(self._wrapper)
        self.setHtml('<pre><a>' + text + '</a></pre>')


