import unittest
from primitives import Var, PrimitiveClause


class PropositionalLogic(unittest.TestCase):

    def test_var_eval(self):
        a = Var("a", True)

        self.assertEqual(a(), True)

    def test_var_negate(self):
        a = Var("a", True)

        self.assertEqual((~a)(), False)

    def test_primitive_clause_contains(self):
        a = Var("a")
        b = Var("b")

        p = PrimitiveClause({a, b})

        self.assertEqual(a in p, True)

    def test_primitive_clause_remove(self):
        a = Var("a")
        b = Var("b")

        p = PrimitiveClause({a, b})
        p2 = PrimitiveClause({a})

        self.assertEqual(p - b, p2)

    def test_primitive_clause_eval(self):
        a = Var("a", False)
        b = Var("b", True)

        p = PrimitiveClause({a, b})

        self.assertEqual(p(), True)
