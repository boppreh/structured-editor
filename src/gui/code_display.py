from PyQt4 import QtCore, QtGui, QtWebKit
from time import time
from core.actions import Select
from os.path import basename

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
        node_id = int(basename(str(url.toString())))
        node_clicked = self.node_dict[node_id]
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

    def _add_link(self, node, color_tag_tuple):
        open_color, close_color = color_tag_tuple
        #return open_color + text + close_color

        open = '<a href="{node_id}" style="color: #222222; text-decoration: none">'
        close = '</a>'

        self.node_dict[node.node_id] = node

        if node.parent:
            # Yep, it starts with a close link tag and ends with an opening link
            # tag. The goal is to eliminate nested link tags, so we close the
            # parent's whenever we start a new object and reopen again when we
            # finish.
            # Also, the color must be between the parent's tag and the child's
            # tag, to avoid invalid markup like <a><span></a></span>.
            beginning = close + open_color + open.format(node_id=node.node_id)
            ending = close + close_color + open.format(node_id=node.parent.node_id)
        else:
            # If there's no parent, no reason to perform the close/open/close
            # dance.
            beginning = open_color + open.format(node_id=node.node_id)
            ending = close + close_color

        return beginning + (node.template or ' ') + ending

    def _render_wrapper(self, node):
        if node == self.editor.selected:
            color_tags = self._color_tag('#95CAFF')
        elif node.parent == self.editor.selected.parent:
            color_tags = self._color_tag('#CECECE')
        else:
            color_tags = ('', '')

        return self._add_link(node, color_tags)

    def refresh(self):
        """ Renders editor state in this text. """
        self.node_dict = {}
        text = self.editor.render(self._render_wrapper)

        background_pattern = ('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAA'
                              'ASklEQVR42m1OywoAMAjy/381iG6douHAHWRCD6xMdPdGxB'
                              'LsM/NWoqoWTvgBmDiYmRsCOQIitCCV94JyUvn5gBN+AJf0l'
                              '3BTbvoAbKz5eYmRlT4AAAAASUVORK5CYII=')
        template = """<html>
<body style="background: url('data:image/png;base64,{}'), top left repeat;">
<pre>{}</pre>
</body>
</html>"""
        url = QtCore.QUrl.fromLocalFile(QtCore.QDir.current().absoluteFilePath('dummy.html'))
        self.setHtml(template.format(background_pattern, text), url)
