import pytest
from language import *

def test_name_regex():
    r = node_name_regex

    assert not r.match('')
    assert not r.match(' ')
    assert not r.match('$')
    assert not r.match('$a')

    assert r.match('n')
    assert r.match('name')
    assert r.match('name5')
    assert r.match('5name5')

    assert not r.match('name()')
    assert not r.match('name( )')
    assert not r.match('(name)')
    assert not r.match('$(name)')
    assert not r.match('name($)')
    assert not r.match('name(name )')
    assert not r.match('name( name)')

    assert r.match('name(n)')
    assert r.match('n(name)')
    assert r.match('n(n)')
    assert r.match('5name5(5name5)')

def test_node_type_inheritance():
    a = NodeType('a', None, None)
    b = NodeType('b', None, a)
    c = NodeType('c', None, b)
    d = NodeType('d', None, b)
    e = NodeType('e', None, a)

    assert a.extends(a)
    assert b.extends(b)
    assert not a.extends(None)
    assert not b.extends(None)

    assert b.extends(a)
    assert c.extends(a)
    assert c.extends(b)
    assert d.extends(a)
    assert d.extends(b)
    assert e.extends(a)

    assert not b.extends(c)
    assert not c.extends(d)
    assert not d.extends(c)
    assert not e.extends(b)

def test_serialization():
    type_a = NodeType('a', None, None)
    type_a.output_template = '%{}%'
    type_b = NodeType('b', None, None)
    type_b.output_template = '%{} {} {}%'

    assert str(StrNode('', type_a)) == '%%'
    assert str(StrNode('a', type_a)) == '%a%'
    assert str(StrNode('asdf', type_a)) == '%asdf%'

    assert str(ListNode([], type_a)) == '%%'
    assert str(ListNode([1], type_a)) == '%1%'
    assert str(ListNode([1, 2], type_a)) == '%1, 2%'

    assert str(DictNode({0: 'a'}, type_a)) == '%a%'
    assert str(DictNode({0: 'a', 1: 'b', 2: 'c'}, type_b)) == '%a b c%'

    assert str(ListNode([StrNode('a', type_a)], type_a)) == '%%a%%'
    assert str(DictNode({0: StrNode('a', type_a)}, type_a)) == '%%a%%'


pytest.main()
