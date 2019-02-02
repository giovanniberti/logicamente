from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Literal:
    """A single propositional literal.
    This class is immutable. It supports the call operator to get the literal's value,
    and bitwise negation (~) to get a logically negated literal"""

    name: str
    negate: bool = False

    def __invert__(self):
        return Literal(self.name, not self.negate)

    def __str__(self):
        string = "Literal(name='"
        if self.negate:
            string += "¬"
        string += f"{self.name}')"

        return string

    def truename(self):
        name = ""
        if self.negate:
            name += "¬"
        name += self.name
        return name


@dataclass(frozen=True, init=False)
class Clause:
    """A `Clause` is a disjunction of literals.
    This class is immutable. It supports the call operator to get its logical value,
    bitwise negation (`~`) to get a logically negated clause, subtraction with Literal to remove a variable
    from the clause, and insiemistic inclusion (`in`) to check whether the clause contains a literal (`Literal`)."""

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
        string += " ∨ ".join([var.truename() for var in self.vars])
        string += ")"

        return string

    def __call__(self, *args, **kwargs):
        res = False
        for var in self.vars:
            res = res or var()

        return self.negate ^ res

    def __contains__(self, var: Literal):
        return var in self.vars

    def __sub__(self, other: Literal):
        return Clause(self.vars - {other}, self.negate)

    def __invert__(self):
        return Clause(self.vars, not self.negate)


@dataclass(init=False, frozen=True)
class HornClause(Clause):
    def __init__(self, vars=frozenset(), negate=False):
        super().__init__(vars, negate)

        if not HornClause.is_horn(vars):
            raise TypeError("Horn clauses must have only one positive literal")

        for var in self.vars:
            if not var.negate:
                object.__setattr__(self, 'head', var)

        object.__setattr__(self, 'body', [var for var in vars if var.negate])

    def from_clause(clause: Clause):
        return HornClause(clause.vars)

    def is_horn(vars=frozenset()):
        literals_state = [var.negate for var in vars]
        negated_literals = Counter(literals_state)

        return negated_literals[False] == 1


@dataclass(frozen=True, init=False)
class KB:
    """A `KB` is a set of `Clause`s; informally it represents a propositional clause in CNF
    (Conjunctive Normal Form). It supports the same operations of `Clause`,
    but applied to `Clause`s instead of `Literal`s"""

    clauses: frozenset

    def __init__(self, clauses=frozenset()):
        if type(clauses) not in [frozenset, set]:
            raise TypeError("clauses argument must be either set or frozenset!")

        object.__setattr__(self, "clauses", frozenset(clauses))

    def __str__(self):
        string = "("
        string += " ∧ ".join([str(clause) for clause in self.clauses])
        string += ")"

        return string

    def __call__(self, *args, **kwargs):
        res = True
        for clause in self.clauses:
            res = res and clause()

        return res

    def __contains__(self, clause: Clause):
        return clause in self.clauses

    def __add__(self, other: Clause):
        return KB(self.clauses.union({other}))

    def __sub__(self, other: Clause):
        return KB(self.clauses.difference({other}))

    def __iter__(self):
        return iter(self.clauses)


@dataclass(init=False, frozen=True)
class HornKB(KB):
    def __init__(self, clauses=frozenset()):
        for clause in clauses:
            if not HornClause.is_horn(clause.vars):
                raise TypeError("HornKB must be composed only of Horn clauses")

        horn_clauses = frozenset([HornClause.from_clause(clause) for clause in clauses])
        super().__init__(horn_clauses)

    def __add__(self, other: HornClause):
        clause = HornClause.from_clause(other)
        return HornKB(super().__add__(clause).clauses)
