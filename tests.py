import unittest
from primitives import Literal, Clause


class PropositionalLogicTestCase(unittest.TestCase):

    def test_clause_contains(self):
        a = Literal("a")
        b = Literal("b")

        p = Clause({a, b})

        self.assertEqual(a in p, True)

    def test_clause_remove(self):
        a = Literal("a")
        b = Literal("b")

        p = Clause({a, b})
        p2 = Clause({a})

        self.assertEqual(p - b, p2)
