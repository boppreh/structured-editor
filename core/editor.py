"""
Module for editing a program's source code interactively with a structured
editor.
"""
from ast.structures import Node
import re

class Editor(object):
    """
    Class for interactively editing a program source code.
    """
    def __init__(self, root):
        """
        Creates a new editor to edit _root_, with keyboard commands _commands_.

        root must be part of a tree, which will be displayed at every
        refresh. To indicate relations in the tree the nodes must implement
        __getitem__ (standard bracket access, like this[0]) and contain the
        attributes parent (pointing to the parent node) and selected_index
        (pointing to the default child index).

        commands must be a dict mapping single letters (hotkeys) to functions
        that take the current selected node as parameter and return the new
        selected node.
        """
        self.root = root
        self.selected = self.root
        self.clipboard = None

    def render(self, wrapper=None):
        """
        Returns the textual representation of the source code tree.
        Takes an extra, optional argument that tells how to format the selected
        node.
        """
        return self.root.render(wrapper)
