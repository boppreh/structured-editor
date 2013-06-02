from ConfigParser import RawConfigParser

class HtmlRendering(object):
    def __init__(self, root, selected=None):
        self.selected = selected

        self.config = RawConfigParser()
        self.config.read('theme.ini')

        self.node_dict = {}
        
        text = root.render(self._linked_template)
        background = self.config.get('Global', 'background')
        font = self.config.get('Global', 'font')

        template = """<body style="{}"><pre style="{}">{}</pre></body>"""
        self.html = template.format(background, font, text)

    def _node_style(self, node):
        """
        Returns the CSS to color the node according to its node type.
        """
        class_name = type(node).__name__.lower()
        try:
            return self.config.get('Structures', class_name)
        except:
            return self.config.get('Structures', 'default')

    def _span_tags(self, node):
        """
        Returns the opening and closing span tags containing the background
        style for the given node.
        """
        if self.selected is None or node.parent != self.selected.parent:
            return '', ''

        if node == self.selected:
            style = self.config.get('Selection', 'background')
        else:
            style = self.config.get('Selection', 'siblingsbackground')
        return '<span style="{}">'.format(style), '</span>'

    def _link_tags(self, node):
        """
        Returns the opening and closing link tags, with user-specified style,
        for the given node.
        """
        template = '<a href="{}" style="text-decoration: none; {}">'
        return template.format(node.node_id, self._node_style(node)), '</a>'

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
