import pytest
from actions import *
from tree import Tree

t1 = Tree()
t2 = Tree()
t3 = Tree()
t = Tree(children=[t1, t2, t3])


def test_simple_horizontal_movement():
    assert left(t) == t
    assert right(t) == t

    assert left(t1) == t1
    assert left(t2) == t1
    assert left(t3) == t2

    assert right(t1) == t2
    assert right(t2) == t3
    assert right(t3) == t3

def test_simple_vertical_movement():
    assert up(t1) == t
    assert up(t2) == t
    assert up(t3) == t
    assert up(t) == t

    assert down(t1) == t1
    assert down(t2) == t2
    assert down(t3) == t3
    assert down(t) == t1

pytest.main(__file__.replace('\\', '/'))