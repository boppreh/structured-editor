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

    def _span_tags(self, node):
        open_tag_template = '<span style="background-color: {};">'

        if node == self.editor.selected:
            return open_tag_template.format('#95CAFF'), '</span>'
        elif node.parent == self.editor.selected.parent:
            return open_tag_template.format('#CECECE'), '</span>'
        else:
            return '', ''

    def _link_tags(self, node):
        template = '<a href="{id}" style="{color}; text-decoration: none">'
        color = 'color: hsl({}, 100%, 20%)'.format(id(type(node)) % 255)
        return template.format(id=node.node_id, color=color), '</a>'

    def _linked_template(self, node):
        self.node_dict[node.node_id] = node

        if node.parent:
            # Close parent's href tag to avoid nested links.
            suffix, prefix = self._link_tags(node.parent)
        else:
            suffix, prefix = '', ''

        open_a, close_a = self._link_tags(node)
        open_span, close_span = self._span_tags(node)

        return (prefix + open_span + open_a +
                (node.template or ' ') +
                close_a + close_span + suffix)

    def _render_wrapper(self, node):
        return self._linked_template(node)

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
<pre style="font-family: 'Consolas', monospace; font-size: 16px;">{}</pre>
</body>
</html>"""
        self.setHtml(template.format(background_pattern, text))
