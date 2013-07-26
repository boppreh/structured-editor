import pytest
from actions import *
from tree import Tree

t1 = Tree()
t2 = Tree()
t3 = Tree()
t = Tree(children=[t1, t2, t3])


def test_simple_movement():
    assert left(t) == t
    assert right(t) == t

    assert left(t1) == t1
    assert left(t2) == t1
    assert left(t3) == t2

    assert right(t1) == t2
    assert right(t2) == t3
    assert right(t3) == t3

pytest.main(__file__.replace('\\', '/'))