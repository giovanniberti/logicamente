from dataclasses import dataclass

from primitives import Literal, Clause, Term, FreeClause


@dataclass
class Relation:
    name: str

    def __call__(self, *args, **kwargs):
        if len(args) > 3:
            raise RuntimeError("wrong number of arguments in relation (three args max)")

        if len(args) == 2:
            return RelationInstance(self.name, args[0], args[1])
        elif len(args) == 3:
            return RelationInstance(self.name, args[0], args[1], args[2])


class RelationInstance(Term):
    relation_name: str
    var1: Term
    var2: Term

    def __init__(self, relation_name: str, var1: Term, var2: Term, negate: bool = False):
        super().__init__(negate)
        object.__setattr__(self, "relation_name", relation_name)
        object.__setattr__(self, "var1", var1)
        object.__setattr__(self, "var2", var2)

    def __contains__(self, item: Literal):
        return item in self.var1 or item in self.var2

    def __repr__(self):
        return f"RelationInstance{{name={self.relation_name}, var1={repr(self.var1)}, var2={repr(self.var2)}, " \
               f"negate={self.negate}}} "

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        return string + f"{self.relation_name}({self.var1}, {self.var2})"

    def __invert__(self):
        return RelationInstance(self.relation_name, self.var1, self.var2, not self.negate)


@dataclass
class Function:
    name: str

    def __call__(self, *args, **kwargs):
        if len(args) != 1:
            raise RuntimeError("wrong number of arguments in function (one argument required)")

        return FunctionInstance(self.name, args[0])


class Var(Term):
    name: str

    def __init__(self, name: str, negate: bool = False):
        super().__init__(negate)
        object.__setattr__(self, "name", name)

    def __repr__(self):
        return f"Var{{name={self.name}, negate={self.negate}}}"

    def __str__(self):
        return f"{self.name}"

    def __eq__(self, other):
        return type(other) is Var and self.name == other.name

    def __hash__(self):
        return hash(self.name) ^ hash(self.negate) ^ hash("Var")

    def __contains__(self, item):
        return type(item) is Var and self.name == item.name

    def __invert__(self):
        return Var(self.name, not self.negate)


class FunctionInstance(Term):
    function_name: str
    arg: Term

    def __init__(self, function_name, arg, negate=False):
        super().__init__(negate)
        object.__setattr__(self, "function_name", function_name)
        object.__setattr__(self, "arg", arg)

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        return string + f"{self.function_name}({self.arg})"

    def __repr__(self):
        return f"FunctionInstance{{name={self.function_name}, var1={repr(self.arg)}, negate={self.negate}}}"

    def __contains__(self, item):
        return item in self.arg

    def __invert__(self):
        return FunctionInstance(self.function_name, self.arg, not self.negate)


@dataclass(init=False, frozen=True)
class Quantifier(Term):
    variable: Var
    predicate: FreeClause

    def __init__(self, variable: Var, predicate, negate: bool = False):
        super().__init__(negate)
        object.__setattr__(self, "variable", variable)
        object.__setattr__(self, "predicate", predicate)

        if type(variable) is not Var:
            raise TypeError(f"You must use `Var`s for variables. Actual type: {type(variable)}")

        if variable not in predicate:
            raise TypeError("Quantifier variable not present in predicate")

    def __contains__(self, item):
        return item in self.predicate


class Exists(Quantifier):
    def __str__(self):
        string = "("

        if self.negate:
            string += "¬"

        return string + f"∃ {self.variable.name} {self.predicate})"

    def __invert__(self):
        return Exists(self.variable, self.predicate, not self.negate)


class ForAll(Quantifier):
    def __str__(self):
        string = "("

        if self.negate:
            string += "¬"

        return string + f"∀ {self.variable.name} {self.predicate})"

    def __invert__(self):
        return ForAll(self.variable, self.predicate, not self.negate)
