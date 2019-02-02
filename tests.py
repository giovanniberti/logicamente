import unittest
from primitives import Var, Clause


class PropositionalLogicTestCase(unittest.TestCase):

    def test_clause_contains(self):
        a = Var("a")
        b = Var("b")

        p = Clause({a, b})

        self.assertEqual(a in p, True)

    def test_clause_remove(self):
        a = Var("a")
        b = Var("b")

        p = Clause({a, b})
        p2 = Clause({a})

        self.assertEqual(p - b, p2)
