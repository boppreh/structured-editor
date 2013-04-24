import unittest

from lua_parser import *
from lua_structures import *
from structures import *

class TestSpecificParsing(unittest.TestCase):
    """ Tests with specific syntactic structures in mind.  """
    def compare(self, string1, string2, ignored=''):
        """
        Asserts that 'string1' is equal to 'string2' when ignoring the chars in
        'ignored'.
        """
        for char in ignored:
            string1 = string1.replace(char, '')
            string2 = string2.replace(char, '')

        self.assertEqual(string1, string2)

    def do_simple_test(self, test_string, ignored=None):
        """
        Tests if the given test string can be parsed and rendered back
        correctly, ignoring the chars in 'ignored' from the rendering.
        """
        if ignored is None:
            ignored = '\n ()'
        root = parseString(test_string)
        self.compare(root.render(), test_string, ignored=ignored)

    def test_empty_program(self):
        root = parseString('')
        self.assertIsNotNone(root)
        self.assertIsInstance(root, Block)
        self.assertEqual(len(root), 0)
        self.compare(root.render(), '')

    def test_simple_statement(self):
        root = parseString('a = 1')
        self.assertIsNotNone(root)
        self.assertIsInstance(root, Block)
        self.assertEqual(len(root), 1)
        self.assertIsInstance(root[0], Assignment)
        self.compare(root.render(), 'a = 1')

    def test_simple_operation(self):
        self.do_simple_test('a = 1 + 1', '')
        self.do_simple_test('a = -1', '')

    def test_nested_operations(self):
        self.do_simple_test('a = (1 + 1) * 3 + 5 / (2 * 3)', '()')

    def test_empty_function_declaration(self):
        self.do_simple_test('function p() end', '\n ')

    def test_function_declaration(self):
        self.do_simple_test('function p(s, a) print(s) end', '\n ')

    def test_nested_function_declaration(self):
        self.do_simple_test('function p(a, b) function p(c) end end', '\n ')

    def test_ellipsis(self):
        self.do_simple_test('function p(a, ...) end', '\n ')

    def test_dot_method_access(self):
        self.do_simple_test('i = a.n()', '\n ')

    def test_multiple_dot_method_access(self):
        self.do_simple_test('i = a.n.l()', '\n ')

    def test_colon_method_access(self):
        self.do_simple_test('i = a:n()', '\n ')

    def test_dot_colon_method_access(self):
        self.do_simple_test('i = a.a:n()', '\n ')

    def test_chained_method(self):
        self.do_simple_test('i = a.a:n()()', '\n ')

    def test_while(self):
        self.do_simple_test('while s do end', '\n ')

    def test_forin(self):
        self.do_simple_test('for n in l do end', '\n ')

    def test_simple_if(self):
        self.do_simple_test('if c then end', '\n ')

    def test_elseif(self):
        self.do_simple_test('if c then elseif c then end', '\n ')

    def test_else(self):
        self.do_simple_test('if c then else end', '\n ')

    def test_if_elseif_else(self):
        self.do_simple_test('if c then elseif c then else end', '\n ')

if __name__ == '__main__':
    unittest.main()
