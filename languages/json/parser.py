import sys, json, collections

def convert(node):
    if isinstance(node, basestring):
        type_ = 'str'
        value = node
    elif isinstance(node, bool):
        type_ = 'bool'
        value = node == 'true'
    elif node is None:
        type_ = 'none'
        value = 'none'
    elif isinstance(node, int):
        type_ = 'int'
        value = str(node)
    else:
        convert_compound(node)
        return

    print('<{type}>{value}</{type}>'.format(type=type_, value=value))

def convert_compound(node):
    if isinstance(node, list):
        print('<list>')
        for child in node:
            convert(child)
        print('</list>')
    elif isinstance(node, dict):
        print('<dict>')
        for key, child in node.items():
            convert(key)
            convert(child)
        print('</dict>')


if len(sys.argv) > 1:
    text = open(sys.argv[1]).read()
else:
    text = sys.stdin.read()
convert(json.loads(text, object_pairs_hook=collections.OrderedDict))
