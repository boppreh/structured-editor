import sys, json, collections

try:
    str_type = basestring
except NameError:
    str_type = str

def convert(node):
    if isinstance(node, str_type):
        type_ = 'string'
        value = node
    elif isinstance(node, bool):
        type_ = 'bool'
        value = node
    elif node is None:
        type_ = 'null'
        value = 'null'
    elif isinstance(node, int) or isinstance(node, float):
        type_ = 'number'
        value = str(node)
    else:
        convert_compound(node)
        return

    print('<{type}>{value}</{type}>'.format(type=type_, value=value))

def convert_compound(node):
    if isinstance(node, list):
        print('<array>')
        for child in node:
            convert(child)
        print('</array>')
    elif isinstance(node, dict):
        print('<object>')
        for key, child in node.items():
            print('<assignment>')
            convert(key)
            convert(child)
            print('</assignment>')
        print('</object>')


if len(sys.argv) > 1:
    text = open(sys.argv[1]).read()
else:
    text = sys.stdin.read()

convert(json.loads(text, object_pairs_hook=collections.OrderedDict))