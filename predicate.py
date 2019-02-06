from collections import Counter
from dataclasses import dataclass

from first_order import Quantifier, Var, ForAll, RelationInstance, FunctionInstance
from primitives import FreeClause, Clause, HornKB, HornFreeClause
from visitor import CanonicalizeVisitor, VarVisitor, SubstVisitor, SkolemVisitor, GlobalizeVisitor, SimplifyVisitor, \
    DistributeVisitor, ClausifyVisitor, ImplicationsVisitor


@dataclass
class Predicate:
    components: FreeClause = FreeClause([])

    def __str__(self):
        return str(self.components)

    def propositionalize(self):

        remove_implications = ImplicationsVisitor()
        components = remove_implications.visit(self.components)

        canonicalize = CanonicalizeVisitor()
        components = canonicalize.visit(components)

        globalize = GlobalizeVisitor()
        components = globalize.visit(components)

        skolem_visitor = SkolemVisitor()
        components = skolem_visitor.visit(components)

        simplify_visitor = SimplifyVisitor()
        components = FreeClause([simplify_visitor.visit(components)])

        distribute_visitor = DistributeVisitor()
        components = distribute_visitor.visit(components)

        clausify_visitor = ClausifyVisitor()
        components = clausify_visitor.visit(components)

        return Predicate(components)
