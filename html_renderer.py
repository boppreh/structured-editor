from language import ListNode, DictNode, StrNode

def render(node, link=''):
    if isinstance(node, StrNode):
        replacements = (str.__str__(node),)
    elif isinstance(node, ListNode):
        replacements = (', '.join(map(render, node)),)
    elif isinstance(node, DictNode):
        replacements = map(render, node.values())

    inner_content = node.type_.display_template.format(*replacements)

    return inner_content
