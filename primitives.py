from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class Var:
    """A single propositional literal.
    This class is immutable. It supports the call operator to get the literal's value,
    and bitwise negation (~) to get a logically negated literal"""

    name: str
    value: bool = False
    negate: bool = False

    def __call__(self, *args, **kwargs):
        return self.value

    def __invert__(self):
        return Var(self.name, not self.value, not self.negate)

    def __str__(self):
        string = "Var(name='"
        if self.negate:
            string += "¬"
        string += f"{self.name}', value={self.value})"

        return string


@dataclass(frozen=True, init=False)
class PrimitiveClause:
    """A `PrimitiveClause` is a disjunction of literals.
    This class is immutable. It supports the call operator to get its logical value,
    bitwise negation (`~`) to get a logically negated clause, subtraction with Var to remove a variable
    from the clause, and insiemistic inclusion (`in`) to check whether the clause contains a literal (`Var`)."""

    vars: frozenset
    negate: bool

    def __init__(self, vars=frozenset(), negate=False):
        if type(vars) not in [frozenset, set]:
            raise TypeError("vars argument must be either set or frozenset!")

        object.__setattr__(self, 'vars', frozenset(vars))
        object.__setattr__(self, 'negate', negate)

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        string += "("
        string += " ∨ ".join([var.name for var in self.vars])
        string += ")"

        return string

    def __call__(self, *args, **kwargs):
        res = False
        for var in self.vars:
            res = res or var()

        return self.negate ^ res

    def __contains__(self, var: Var):
        return var in self.vars

    def __sub__(self, other: Var):
        return PrimitiveClause(self.vars - {other}, self.negate)

    def __invert__(self):
        return PrimitiveClause(self.vars, not self.negate)


@dataclass(frozen=True, init=False)
class Clause:
    """A `Clause` is a set of `PrimitiveClause`s; informally it represents a propositional clause in CNF
    (Conjunctive Normal Form). It supports the same operations of `PrimitiveClause`,
    but applied to `PrimitiveClause`s instead of `Var`s"""

    primitive_clauses: frozenset

    def __init__(self, primitive_clauses=frozenset()):
        if type(primitive_clauses) not in [frozenset, set]:
            raise TypeError("primitive_clauses argument must be either set or frozenset!")

        object.__setattr__(self, "primitive_clauses", frozenset(primitive_clauses))

    def __str__(self):
        string = "("
        string += " ∧ ".join([str(clause) for clause in self.primitive_clauses])
        string += ")"

        return string

    def __call__(self, *args, **kwargs):
        res = True
        for clause in self.primitive_clauses:
            res = res and clause()

        return res

    def __contains__(self, pclause: PrimitiveClause):
        return pclause in self.primitive_clauses

    def __add__(self, other: PrimitiveClause):
        return Clause(self.primitive_clauses.union({other}))

    def __sub__(self, other: PrimitiveClause):
        return Clause(self.primitive_clauses.difference({other}))


class KB:
    clauses: Set[Clause]

    def __init__(self, clauses: Set[Clause]):
        self.clauses = clauses
