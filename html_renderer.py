from language import ListNode, DictNode, StrNode

def render(node, link='/'):
    open_link = '<a href="{}">'.format(link)
    close_link = '</a>'

    if isinstance(node, StrNode):
        replacements = (str.__str__(node),)
    else:
        replacements = []
        for i in xrange(len(node)):
            child_text = render(node[i], link + str(i) + '/')
            replacements.append(close_link + child_text + open_link)

        if isinstance(node, ListNode):
            replacements = [', '.join(replacements)]

    inner_content = node.type_.display_template.format(*replacements)
    if node.type_.style:
        span_template = '<span style="{}">{}</span>'
        inner_content = span_template.format(node.type_.style, inner_content)

    return open_link + inner_content + close_link
