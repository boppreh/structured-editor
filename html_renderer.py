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
    linked_content = open_link + inner_content + close_link

    if node.type_.style:
        span_template = '<span style="{}">{}</span>'
        return span_template.format(node.type_.style, linked_content)
    else:
        return linked_content
