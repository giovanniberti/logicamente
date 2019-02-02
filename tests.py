import unittest
from primitives import Var, Clause


class PropositionalLogicTestCase(unittest.TestCase):

    def test_var_eval(self):
        a = Var("a", True)

        self.assertEqual(a(), True)

    def test_var_negate(self):
        a = Var("a", True)

        self.assertEqual((~a)(), False)

    def test_primitive_clause_contains(self):
        a = Var("a")
        b = Var("b")

        p = Clause({a, b})

        self.assertEqual(a in p, True)

    def test_primitive_clause_remove(self):
        a = Var("a")
        b = Var("b")

        p = Clause({a, b})
        p2 = Clause({a})

        self.assertEqual(p - b, p2)

    def test_primitive_clause_eval(self):
        a = Var("a", False)
        b = Var("b", True)

        p = Clause({a, b})

        self.assertEqual(p(), True)
