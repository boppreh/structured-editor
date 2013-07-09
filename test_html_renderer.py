import pytest
from html_renderer import render
from language import ListNode, DictNode, StrNode, NodeType

def make_type(display_template, style=''):
    type_ = NodeType()
    type_.style = style
    type_.display_template = display_template
    return type_

single_type = make_type('{}')
double_type = make_type('{}-{}')

def test_simplest():
    root = StrNode('value', single_type)
    assert render(root) == 'value'

def test_recursion():
    tree = ListNode([
                     StrNode('value1', single_type),
                     DictNode({
                               0: ListNode([], single_type),
                               1: StrNode('value2', single_type),
                              }, double_type),
                     ListNode([StrNode('value3', single_type)], single_type),
                    ], single_type)

    assert render(tree[0]) == 'value1'
    assert render(tree[1]) == '-value2'
    assert render(tree[2]) == 'value3'
    assert render(tree) == 'value1, -value2, value3'


pytest.main()
