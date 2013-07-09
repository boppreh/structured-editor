import pytest
import re
from html_renderer import render
from language import ListNode, DictNode, StrNode, NodeType

def make_type(display_template, style=''):
    type_ = NodeType()
    type_.style = style
    type_.display_template = display_template
    return type_

def render_text(tree):
    return re.sub('<[^>]+>', '', render(tree))

single_type = make_type('{}')
double_type = make_type('{}-{}')

def test_simplest():
    root = StrNode('value', single_type)
    assert render_text(root) == 'value'

def test_recursion():
    tree = ListNode([
                     StrNode('value1', single_type),
                     DictNode({
                               0: ListNode([], single_type),
                               1: StrNode('value2', single_type),
                              }, double_type),
                     ListNode([StrNode('value3', single_type)], single_type),
                    ], single_type)

    assert render_text(tree[0]) == 'value1'
    assert render_text(tree[1]) == '-value2'
    assert render_text(tree[2]) == 'value3'
    assert render_text(tree) == 'value1, -value2, value3'

def test_single_link():
    tree = StrNode('value', single_type)
    assert render(tree, 'link') == '<a href="link">value</a>'

def test_nested_links():
    tree = ListNode([StrNode('value', single_type)], single_type)
    assert render(tree, 'link/') == '<a href="link/"></a><a href="link/0/">value</a><a href="link/"></a>'

def test_really_nested_links():
    tree = ListNode([
                     StrNode('value1', single_type),
                     DictNode({
                               0: ListNode([], single_type),
                               1: StrNode('value2', single_type),
                              }, double_type),
                     ListNode([StrNode('value3', single_type)], single_type),
                    ], single_type)
    assert render(tree) == """<a href="/"></a><a href="/0/">value1</a><a href="/">, </a><a href="/1/"></a><a href="/1/0/"></a><a href="/1/">-</a><a href="/1/1/">value2</a><a href="/1/"></a><a href="/">, </a><a href="/2/"></a><a href="/2/0/">value3</a><a href="/2/"></a><a href="/"></a>"""

def test_simple_style():
    tree = StrNode('value', make_type('{}', 'style'))
    assert render(tree) == '<span style="style"><a href="/">value</a></span>'

def test_nested_style():
    type1 = make_type('{}', 'style1')
    type2 = make_type('{}', 'style2')
    tree = ListNode([StrNode('value', type2)], type1)
    assert render(tree) == '<span style="style1"><a href="/"></a><span style="style2"><a href="/0/">value</a></span><a href="/"></a></span>'


pytest.main()
