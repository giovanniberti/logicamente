from dataclasses import dataclass

from primitives import Literal, Clause, Term, FreeClause


@dataclass
class Relation:
    name: str

    def __call__(self, *args, **kwargs):
        return RelationInstance(self.name, *args)


class RelationInstance(Term):
    relation_name: str
    vars: list

    def __init__(self, relation_name: str, *vars, negate: bool = False):
        super().__init__(negate)
        object.__setattr__(self, "relation_name", relation_name)
        object.__setattr__(self, "vars", vars)

    def __contains__(self, item):
        present = False
        for var in self.vars:
            present |= item in var
        return present

    def __repr__(self):
        return f"RelationInstance{{name={self.relation_name}, vars={repr(self.vars)}, negate={self.negate}}}"

    def __str__(self):
        string = ""

        if self.negate:
            string += "¬"

        var_names = [str(var) for var in self.vars]
        string += f'{self.relation_name}({", ".join(var_names)})'

        return string

    def __invert__(self):
        return RelationInstance(self.relation_name, *self.vars, negate=not self.negate)

    def __eq__(self, other):
        return type(other) is RelationInstance and \
               self.relation_name == other.relation_name and \
               self.vars == other.vars and \
               self.negate == other.negate

    def __hash__(self):
        return hash(self.relation_name) ^ hash(self.negate) ^ hash("RelationName") ^ hash(self.vars)


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

    def __eq__(self, other):
        return type(other) is FunctionInstance and \
               self.function_name == other.function_name and \
               self.arg == other.arg and \
               self.negate == other.negate

    def __hash__(self):
        return hash(self.function_name) ^ hash(self.negate) ^ hash("FunctionInstance") ^ hash(self.arg)


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
