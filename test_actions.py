import pytest
from actions import *
from tree import Tree

def make_tree():
    return Tree(children=[Tree(children=[Tree(), Tree(), Tree()]),
                          Tree(children=[Tree(), Tree()]),
                          Tree(children=[])])


def test_horizontal_movement():
    t = make_tree()

    assert left(t) == t
    assert left(t[0]) == t[0]
    assert left(t[1]) == t[0]
    assert left(t[2]) == t[1]

    assert right(t) == t
    assert right(t[0]) == t[1]
    assert right(t[1]) == t[2]
    assert right(t[2]) == t[2]

def test_vertical_movement():
    t = make_tree()

    assert up(t) == t
    assert up(t[0]) == t
    assert up(t[1]) == t
    assert up(t[2]) == t

    assert down(t) == t[0]
    assert down(t[0]) == t[0][0]
    assert down(t[1]) == t[1][0]
    assert down(t[2]) == t[2]

def test_replace():
    t = make_tree()

    t1 = Tree()
    t2 = Tree()
    t3 = Tree()

    old1 = t[0]
    old2 = t[1]
    old3 = t[2]

    assert replace(t, t) == t
    assert replace(t[0], t[0]) == t[0]

    assert replace(t[0], t1) == t1
    assert t[0] == t1
    assert t[1] == old2
    assert t[2] == old3

    assert replace(t[1], t2) == t2
    assert t[0] == t1
    assert t[1] == t2
    assert t[2] == old3

    assert replace(t[2], t3) == t3
    assert t[0] == t1
    assert t[1] == t2
    assert t[2] == t3

    assert replace(t, t1) == t1
    

pytest.main(__file__.replace('\\', '/'))