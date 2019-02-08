from abc import ABC, abstractmethod
from collections import Counter
from typing import FrozenSet, List


class Term(ABC):
    negate: bool

    def __init__(self, negate=False):
        object.__setattr__(self, "negate", negate)

    @abstractmethod
    def __invert__(self):
        pass

    def __contains__(self, item):
        return self == item

    def __setattr__(self, key, value):
        raise AttributeError("Class is immutable")

    def __repr__(self):
        return f"Term{{negate={self.negate}}}"

    def __iter__(self):
        return iter({self})


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

    def __repr__(self):
        return f"Literal{{name={self.name}, negate={self.negate}}}"

    def __contains__(self, item):
        return type(item) is Literal and self.name == item.name

    def __eq__(self, other):
        return type(other) is Literal and self.name == other.name and self.negate == other.negate

    def __hash__(self):
        return hash(self.negate) ^ hash(self.name) ^ hash("Literal")


class Operator(Term, ABC):
    operand1: Term
    operand2: Term

    def __init__(self, operand1, operand2, negate=False):
        super().__init__(negate)
        object.__setattr__(self, "operand1", operand1)
        object.__setattr__(self, "operand2", operand2)

    def __contains__(self, item: Term):
        return item in self.operand1 or item in self.operand2


class Or(Operator):
    def __invert__(self):
        return Or(self.operand1, self.operand2, not self.negate)

    def __repr__(self) -> str:
        return f"Or{{operand1={repr(self.operand1)}, operand2={repr(self.operand2)}}}"

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        return string + f"({self.operand1} ∨ {self.operand2})"


class And(Operator):
    def __invert__(self):
        return And(self.operand1, self.operand2, not self.negate)

    def __repr__(self) -> str:
        return f"And{{operand1={repr(self.operand1)}, operand2={repr(self.operand2)}}}"

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        return string + f"({self.operand1} ∧ {self.operand2})"


class Implies(Operator):
    def __invert__(self):
        return Implies(self.operand1, self.operand2, not self.negate)

    def __repr__(self):
        return f"Implies{{operand1={repr(self.operand1)}, operand2={repr(self.operand2)}}}"

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        return string + f"({self.operand1} ⇒ {self.operand2})"


class Iff(Operator):
    def __invert__(self):
        return Iff(self.operand1, self.operand2, not self.negate)

    def __repr__(self):
        return f"Implies{{operand1={repr(self.operand1)}, operand2={repr(self.operand2)}}}"

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        return string + f"({self.operand1} ⇔ {self.operand2})"


class FreeClause(Term):
    terms: List[Term]

    def __init__(self, terms, negate: bool = False):
        super().__init__(negate)
        object.__setattr__(self, "terms", terms)

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        string += "("
        string += "".join([str(term) for term in self.terms])

        return string + ")"

    def __repr__(self):
        return f"FreeClause{{terms={repr(self.terms)}, negate={repr(self.negate)}}}"

    def __contains__(self, var: Term):
        res = False
        for v in self.terms:
            res = res or (var in v)
        return res

    def __invert__(self):
        return FreeClause(self.terms, not self.negate)


class HornFreeClause(FreeClause):
    def __init__(self, terms, negate: bool = False):
        super().__init__(terms, negate)

        if not HornFreeClause.is_horn(terms):
            raise TypeError("Free Horn clauses must have only one positive literal")

        for term in self.terms:
            if not term.negate:
                object.__setattr__(self, 'head', term)

        object.__setattr__(self, 'body', [term for term in terms if term.negate])

    def __repr__(self):
        return f"HornFreeClause{{terms={repr(self.terms)}, negate={repr(self.negate)}}}"

    def is_horn(terms):
        literals_state = [term.negate for term in terms]
        negated_literals = Counter(literals_state)

        return negated_literals[False] == 1

    def from_clause(clause: FreeClause):
        return HornFreeClause(clause.terms, clause.negate)


class Clause(Term):
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
        return f"Clause{{terms={repr(self.terms)}, negate={repr(self.negate)}}}"

    def __contains__(self, var: Term):
        res = False
        for v in self.terms:
            res = res or (var in v)
        return res

    def __add__(self, other):
        new = Clause(self.terms)
        if type(other) is Clause:
            if self.negate != other.negate:
                raise ValueError("Can't add together two clauses with different polarity")

            new = Clause(self.terms.union(other.terms))
        else:
            new = Clause(self.terms.union(other))

        return new

    def __sub__(self, other: Literal):
        return Clause(self.terms - {other}, self.negate)

    def __invert__(self):
        return Clause(self.terms, not self.negate)

    def __eq__(self, other):
        return isinstance(other, Clause) and self.negate == other.negate and self.terms == other.terms

    def __hash__(self):
        return hash(self.negate) ^ hash(tuple(self.terms)) ^ hash("Clause")

    def to_free_clause(self):
        terms = Clause._make_or(self.terms)

        return FreeClause([terms], negate=self.negate)

    @staticmethod
    def _make_or(terms):
        terms = list(terms)
        if len(terms) <= 1:
            return terms[0]
        if len(terms) == 2:
            return Or(terms[0], terms[1])
        else:
            return Or(terms[0], Clause._make_or(terms[1:]))



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

    def __eq__(self, other):
        return super().__eq__(other)

    def __hash__(self):
        return super.__hash__(self)

    def from_clause(clause: Clause):
        return HornClause(clause.terms)

    def is_horn(vars: FrozenSet[Term]):
        return HornFreeClause.is_horn(vars)


class KB:
    """A `KB` is a set of `Clause`s; informally it represents a propositional clause in CNF
    (Conjunctive Normal Form). It supports the same operations of `Clause`,
    but applied to `Clause`s instead of `Literal`s"""

    clauses: FrozenSet[Clause]
    negate: bool = False

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

    def __add__(self, other):
        new = KB(self.clauses)
        for term in iter(other):
            new = KB(new.clauses.union(term))

        return new

    def __sub__(self, other: Clause):
        return KB(self.clauses.difference({other}))

    def __iter__(self):
        return iter(self.clauses)

    def to_free_clause(self):
        terms = KB._make_and(self.clauses)

        return FreeClause([terms])

    @staticmethod
    def _make_and(terms):
        terms = list(terms)
        if len(terms) <= 1:
            return terms[0]
        if len(terms) == 2:
            return And(terms[0], terms[1])
        else:
            return And(terms[0], KB._make_and(terms[1:]))


class HornKB(KB):
    def __init__(self, clauses=frozenset()):
        for clause in clauses:
            if not HornFreeClause.is_horn(clause.terms):
                raise TypeError("HornKB must be composed only of Horn clauses")

        horn_clauses = frozenset([HornClause.from_clause(clause) for clause in clauses])
        super().__init__(horn_clauses)

    def __repr__(self):
        return f"HornKB{{clauses={self.clauses}}}"

    def __add__(self, other):
        if not HornFreeClause.is_horn(other):
            raise ValueError("Cannot add non-Horn clause to HornKB")

        new = HornKB(self.clauses)
        for term in iter(other):
            new = HornKB(new.clauses.union(term))

        return new
