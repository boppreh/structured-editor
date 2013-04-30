from PyQt4 import QtCore, QtGui, QtWebKit
from ConfigParser import RawConfigParser, NoOptionError
from time import time
from core.actions import Select
from os.path import basename

from ast.structures import *
from ast.lua_structures import *

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

        self.config = RawConfigParser()
        self.config.read('color_scheme.ini')
        self.config.read('display_templates.ini')

    def node_style(self, node):
        """
        Returns the CSS to color the node according to its node type.
        """
        class_name = type(node).__name__.lower()
        try:
            return self.config.get('Styles', class_name)
        except NoOptionError:
            return self.config.get('Styles', 'default')
        except:
            return 'color: #222222;'

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
        open_tag_template = '<span style="{}">'

        if node == self.editor.selected:
            style = self.config.get('Styles', 'selectednodebackground')
            return open_tag_template.format(style), '</span>'
        elif node.parent == self.editor.selected.parent:
            style = self.config.get('Styles', 'siblingsbackground')
            return open_tag_template.format(style), '</span>'
        else:
            return '', ''

    def _link_tags(self, node):
        template = '<a href="{}" style="text-decoration: none; {}">'
        return template.format(node.node_id, self.node_style(node)), '</a>'

    def _linked_template(self, node):
        self.node_dict[node.node_id] = node

        if node.parent:
            # Close parent's href tag to avoid nested links.
            suffix, prefix = self._link_tags(node.parent)
        else:
            suffix, prefix = '', ''

        open_a, close_a = self._link_tags(node)
        open_span, close_span = self._span_tags(node)

        try:
            template = self.config.get('Templates', type(node).__name__)
        except:
            template = node.template

        return (prefix + open_span + open_a +
                template +
                close_a + close_span + suffix)

    def _render_wrapper(self, node):
        return self._linked_template(node)

    def refresh(self):
        """ Renders editor state in this text. """
        self.node_dict = {}
        text = self.editor.render(self._render_wrapper)

        template = """<html>
<body style="{}">
<pre style="font-family: 'Consolas', 'Bitstream Vera Sans Mono', monospace; font-size: 14px;">{}</pre>
</body>
</html>"""
        background = self.config.get('Styles', 'background')
        self.setHtml(template.format(background, text))
