from language import ListNode, DictNode, StrNode

def render(node, link=''):
    if isinstance(node, StrNode):
        replacements = (str.__str__(node),)
    elif isinstance(node, ListNode):
        replacements = (', '.join(map(render, node)),)
    elif isinstance(node, DictNode):
        replacements = map(render, node.values())

    open_link = '<a href="{}">'.format(link)
    close_link = '</a>'

    inner_content = node.type_.display_template.format(*replacements)

    return open_link + inner_content + close_link
