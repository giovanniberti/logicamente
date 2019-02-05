from abc import ABC
from collections import Counter
from typing import FrozenSet, List


class Term(ABC):
    negate: bool

    def __init__(self, negate=False):
        object.__setattr__(self, "negate", negate)

    def __invert__(self):
        return Term(not self.negate)

    def __contains__(self, item):
        return self == item

    def __setattr__(self, key, value):
        raise AttributeError("Class is immutable")

    def __repr__(self):
        return f"Term{{negate={self.negate}}}"


class Literal(Term):
    """A single propositional literal.
    This class is immutable. It supports the call operator to get the literal's value,
    and bitwise negation (~) to get a logically negated literal"""

    name: str

    def __init__(self, name: str, negate: bool = False):
        super().__init__(negate)
        object.__setattr__(self, "name", name)

    def __invert__(self):
        return Literal(self.name, not self.negate)

    def __str__(self):
        string = ""
        if self.negate:
            string += "¬"
        string += f"{self.name}"

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

    terms: FrozenSet[Term]

    def __init__(self, terms=frozenset(), negate: bool = False):
        super().__init__(negate)

        if type(terms) not in [frozenset, set]:
            raise TypeError("terms argument must be either set or frozenset!")

        object.__setattr__(self, "terms", terms)

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        string += "("
        string += " ∨ ".join([str(term) for term in self.terms])
        string += ")"

        return string

    def __repr__(self):
        return f"Clause{{terms={self.terms}, negate={self.negate}}}"

    def __contains__(self, var: Term):
        res = False
        for v in self.terms:
            res = res or (var in v)
        return res

    def __sub__(self, other: Literal):
        return Clause(self.terms - {other}, self.negate)

    def __invert__(self):
        return Clause(self.terms, not self.negate)


class HornClause(Clause):
    def __init__(self, vars=frozenset(), negate=False):
        super().__init__(vars, negate)

        if not HornClause.is_horn(vars):
            raise TypeError("Horn clauses must have only one positive literal")

        for var in self.terms:
            if not var.negate:
                object.__setattr__(self, 'head', var)

        object.__setattr__(self, 'body', [var for var in vars if var.negate])

    def __repr__(self):
        return f"HornClause{{terms={self.terms}, negate={self.negate}}}"

    def from_clause(clause: Clause):
        return HornClause(clause.terms)

    def is_horn(vars: FrozenSet[Term]):
        for var in vars:
            if type(var) != Literal:
                raise TypeError("Horn clauses are propositional")

        literals_state = [var.negate for var in vars]
        negated_literals = Counter(literals_state)

        return negated_literals[False] == 1


class KB:
    """A `KB` is a set of `Clause`s; informally it represents a propositional clause in CNF
    (Conjunctive Normal Form). It supports the same operations of `Clause`,
    but applied to `Clause`s instead of `Literal`s"""

    clauses: FrozenSet[Clause]

    def __init__(self, clauses=frozenset()):
        if type(clauses) not in [frozenset, set]:
            raise TypeError("clauses argument must be either set or frozenset!")

        object.__setattr__(self, "clauses", clauses)

    def __str__(self):
        string = "("
        string += " ∧ ".join([str(clause) for clause in self.clauses])
        string += ")"

        return string

    def __repr__(self):
        return f"KB{{clauses={self.clauses}}}"

    def __contains__(self, clause: Clause):
        return clause in self.clauses

    def __add__(self, other: Clause):
        return KB(self.clauses.union({other}))

    def __sub__(self, other: Clause):
        return KB(self.clauses.difference({other}))

    def __iter__(self):
        return iter(self.clauses)


class HornKB(KB):
    def __init__(self, clauses=frozenset()):
        for clause in clauses:
            if not HornClause.is_horn(clause.vars):
                raise TypeError("HornKB must be composed only of Horn clauses")

        horn_clauses = frozenset([HornClause.from_clause(clause) for clause in clauses])
        super().__init__(horn_clauses)

    def __repr__(self):
        return f"HornKB{{clauses={self.clauses}}}"

    def __add__(self, other: HornClause):
        clause = HornClause.from_clause(other)
        return HornKB(super().__add__(clause).clauses)
