from . import config
import re
from os import path
from sys import argv

class HtmlRendering(object):
    def __init__(self, root, selected=None):
        self.selected = selected
        template = """<html>
        <head>
            <link href="file:/{}" type="text/css" rel="stylesheet"/>
        </head>
        <body><pre>{}</pre></body>
</html>"""
        css = path.abspath(path.join(path.dirname(argv[0]), 'config', 'style.css'))
        self.html = template.format(css, root.render(self._process_node))

    def _span_tags(self, node):
        """
        Returns the opening and closing span tags containing the background
        style for the given node.
        """
        classes = [type(node).__name__.lower()]
        if node == self.selected:
            classes.append('selected')
        elif node.parent == self.selected.parent:
            classes.append('sibling')

        return '<span class="{}">'.format(' '.join(classes)), '</span>'

    def _make_parts(self, node):
        """
        Returns the parts (open tags, literal template, close tags) for
        the given node.
        """
        open_span, close_span = self._span_tags(node)

        class_name = type(node).__name__
        template = config.get('Display Templates', class_name, node.template)

        # Span tags change the background, but there's no background in empty
        # nodes. So we replace it with a single space.
        if open_span and len(node) == 0 and re.match(r'^\{\w+\}$', template):
            template += ' '

        return (open_span, template, close_span)

    def _process_node(self, node):
        """
        Returns the full template for the given node.
        """
        return ''.join(self._make_parts(node))

class LinkedRendering(HtmlRendering):
    def __init__(self, root, selected=None):
        self.node_dict = {}
        super(LinkedRendering, self).__init__(root, selected)

    def _link_tags(self, node):
        """
        Returns the opening and closing link tags, with user-specified style,
        for the given node.
        """
        template = '<a id="{id}" href="{id}">'
        return template.format(id=node.node_id), '</a>'

    def _make_parts(self, node):
        """
        Returns the node's template with link and span tags added.
        """
        parts = super(LinkedRendering, self)._make_parts(node)
        open_span, template, close_span = parts

        # Dictionary of all nodes and their corresponding urls, to be used when
        # the user clicks on any of the links.
        self.node_dict[node.node_id] = node

        if node.parent:
            parent_open, parent_close = self._link_tags(node.parent)
        else:
            parent_open, parent_close = '', ''

        open_a, close_a = self._link_tags(node)

        # Close parent's href tag to avoid nested links.
        return (parent_close, open_span, open_a,
                template,
                close_a, close_span, parent_open)
