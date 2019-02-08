from collections import Counter

from first_order import Var, Exists, ForAll, RelationInstance, Quantifier, Function, FunctionInstance
from primitives import Literal, And, Or, FreeClause, Operator, Clause, KB, Implies, Iff, HornKB, \
    HornFreeClause, HornClause


def _qualname(obj):
    """Get the fully-qualified name of an object (including module)."""
    return obj.__module__ + '.' + obj.__qualname__


def _declaring_class(obj):
    """Get the name of the class that declared an object."""
    name = _qualname(obj)
    return name[:name.rfind('.')]


# Stores the actual visitor methods
_methods = {}


# Delegating visitor implementation
def _visitor_impl(self, arg):
    """Actual visitor method implementation."""
    method = _methods[(_qualname(type(self)), type(arg))]
    return method(self, arg)


# The actual @visitor decorator
def visitor(arg_type):
    """Decorator that creates a visitor method."""

    def decorator(fn):
        declaring_class = _declaring_class(fn)
        _methods[(declaring_class, arg_type)] = fn

        # Replace all decorated methods with _visitor_impl
        return _visitor_impl

    return decorator


class GroundVisitor:
    @visitor(Literal)
    def visit(self, _):
        return True

    @visitor(And)
    def visit(self, operator: And):
        return self.visit(operator.operand1) and self.visit(operator.operand2)

    @visitor(Or)
    def visit(self, operator):
        return self.visit(operator.operand1) and self.visit(operator.operand2)

    @visitor(Var)
    def visit(self, var):
        return False

    @visitor(FreeClause)
    def visit(self, clause):
        ground = False
        for term in clause.terms:
            ground |= self.visit(term)

        return ground

    @visitor(Exists)
    def visit(self, _):
        return False

    @visitor(ForAll)
    def visit(self, _):
        return False

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        ground = False
        for var in relation.vars:
            ground |= self.visit(var)

        return ground

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        return self.visit(function.arg)


class ImplicationsVisitor:

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(And)
    def visit(self, operator: And):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return And(op1, op2, operator.negate)

    @visitor(Or)
    def visit(self, operator):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return Or(op1, op2, operator.negate)

    @visitor(FreeClause)
    def visit(self, clause):
        terms = clause.terms

        new_terms = []
        for term in terms:
            new_terms += [self.visit(term)]

        return FreeClause(new_terms, clause.negate)

    @visitor(HornClause)
    def visit(self, clause):
        return self.visit(clause.to_free_clause())

    @visitor(Exists)
    def visit(self, quantifier: Quantifier):
        predicate = self.visit(quantifier.predicate)

        return Exists(quantifier.variable, predicate, quantifier.negate)

    @visitor(ForAll)
    def visit(self, quantifier):
        predicate = self.visit(quantifier.predicate)

        return ForAll(quantifier.variable, predicate, quantifier.negate)

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = [self.visit(var) for var in relation.vars]

        return RelationInstance(relation.relation_name, *vars, negate=relation.negate)

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        arg = self.visit(function.arg)

        return FunctionInstance(function.function_name, arg, function.negate)

    @visitor(Implies)
    def visit(self, implication: Implies):
        op1 = self.visit(implication.operand1)
        op2 = self.visit(implication.operand2)

        return Or(~op1, op2)

    @visitor(Iff)
    def visit(self, iff: Iff):
        op1 = self.visit(iff.operand1)
        op2 = self.visit(iff.operand2)

        return And(Implies(op1, op2), Implies(op2, op1))


class VarVisitor:
    @visitor(Literal)
    def visit(self, _):
        return []

    @visitor(And)
    def visit(self, operator):
        return self.visit(operator.operand1) + self.visit(operator.operand2)

    @visitor(Or)
    def visit(self, operator):
        return self.visit(operator.operand1) + self.visit(operator.operand2)

    @visitor(Var)
    def visit(self, var):
        return []

    @visitor(FreeClause)
    def visit(self, clause):
        return [var for term in clause.terms for var in self.visit(term)]

    @visitor(Exists)
    def visit(self, quantifier: Quantifier):
        return list({quantifier.variable}.union(set(self.visit(quantifier.predicate))))

    @visitor(ForAll)
    def visit(self, quantifier):
        return list({quantifier.variable}.union(set(self.visit(quantifier.predicate))))

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = []
        for var in relation.vars:
            vars += self.visit(var)

        return vars

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        return self.visit(function.arg)


class FreeVarVisitor:
    @visitor(Literal)
    def visit(self, _):
        return []

    @visitor(And)
    def visit(self, operator):
        return self.visit(operator.operand1) + self.visit(operator.operand2)

    @visitor(Or)
    def visit(self, operator):
        return self.visit(operator.operand1) + self.visit(operator.operand2)

    @visitor(Var)
    def visit(self, var):
        return [var]

    @visitor(FreeClause)
    def visit(self, clause):
        return [var for term in clause.terms for var in self.visit(term)]

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = []
        for var in relation.vars:
            vars += self.visit(var)

        return vars

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        return self.visit(function.arg)


class GlobalizeVisitor:
    i = 0
    var_visitor = VarVisitor()

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(And)
    def visit(self, operator: And):
        vars = self.var_visitor.visit(operator.operand1) + self.var_visitor.visit(operator.operand2)
        counter = Counter(vars)
        dups = [var for var in vars if counter[var] > 1]

        op1 = operator.operand1
        op2 = operator.operand2

        for var in set(dups):
            new_var = Var(f"x{self.i}")
            subst_visitor = SubstVisitor(var, new_var)
            op1 = subst_visitor.visit(op1)
            self.i += 1

            new_var = Var(f"x{self.i}")
            subst_visitor = SubstVisitor(var, new_var)
            op2 = subst_visitor.visit(op2)
            self.i += 1

        op1 = self.visit(op1)
        op2 = self.visit(op2)

        return And(op1, op2, operator.negate)

    @visitor(Or)
    def visit(self, operator):
        vars = self.var_visitor.visit(operator.operand1) + self.var_visitor.visit(operator.operand2)
        counter = Counter(vars)
        dups = [var for var in vars if counter[var] > 1]

        op1 = operator.operand1
        op2 = operator.operand2

        for var in set(dups):
            new_var = Var(f"x{self.i}")
            subst_visitor = SubstVisitor(var, new_var)
            op1 = subst_visitor.visit(op1)
            self.i += 1

            new_var = Var(f"x{self.i}")
            subst_visitor = SubstVisitor(var, new_var)
            op2 = subst_visitor.visit(op2)
            self.i += 1

        op1 = self.visit(op1)
        op2 = self.visit(op2)

        return Or(op1, op2, operator.negate)

    @visitor(FreeClause)
    def visit(self, clause):
        terms = clause.terms

        new_terms = []
        for term in terms:
            new_terms += [self.visit(term)]

        return FreeClause(new_terms, clause.negate)

    @visitor(Exists)
    def visit(self, quantifier: Quantifier):
        return quantifier

    @visitor(ForAll)
    def visit(self, quantifier):
        return quantifier

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        return relation

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        return function


class CanonicalizeVisitor:

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(And)
    def visit(self, operator):
        if operator.negate:
            return Or(self.visit(~operator.operand1), self.visit(~operator.operand2), not operator.negate)

        return And(self.visit(operator.operand1), self.visit(operator.operand2), operator.negate)

    @visitor(Or)
    def visit(self, operator):
        if operator.negate:
            return And(self.visit(~operator.operand1), self.visit(~operator.operand2), not operator.negate)

        return Or(self.visit(operator.operand1), self.visit(operator.operand2), operator.negate)

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(FreeClause)
    def visit(self, clause):
        new_terms = []
        for term in clause.terms:
            new_term = ~term if clause.negate else term
            new_terms += [self.visit(new_term)]

        return FreeClause(new_terms, False)

    @visitor(Exists)
    def visit(self, quantifier):
        if quantifier.negate:
            return ForAll(quantifier.variable, self.visit(~quantifier.predicate), not quantifier.negate)

        return Exists(quantifier.variable, self.visit(quantifier.predicate), quantifier.negate)

    @visitor(ForAll)
    def visit(self, quantifier):
        if quantifier.negate:
            return Exists(quantifier.variable, self.visit(~quantifier.predicate), not quantifier.negate)

        return ForAll(quantifier.variable, self.visit(quantifier.predicate), quantifier.negate)

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        return relation

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        return function


class SubstVisitor:

    def __init__(self, body, subst):
        self.body = body
        self.subst = subst

    @visitor(Literal)
    def visit(self, literal):
        if self.body == literal:
            return self.subst
        return literal

    @visitor(Var)
    def visit(self, var):
        if self.body == var:
            return self.subst
        return var

    @visitor(And)
    def visit(self, operator: And):
        op1 = operator.operand1
        op2 = operator.operand2

        if self.body == op1:
            op1 = self.subst
        if self.body == op2:
            op2 = self.subst
        if self.body in op1:
            op1 = self.visit(op1)
        if self.body in op2:
            op2 = self.visit(op2)
        return And(op1, op2, operator.negate)

    @visitor(Or)
    def visit(self, operator):
        op1 = operator.operand1
        op2 = operator.operand2

        if self.body == op1:
            op1 = self.subst
        if self.body == op2:
            op2 = self.subst
        if self.body in op1:
            op1 = self.visit(op1)
        if self.body in op2:
            op2 = self.visit(op2)
        return Or(op1, op2, operator.negate)

    @visitor(FreeClause)
    def visit(self, clause):
        terms = clause.terms

        if self.body == clause:
            return self.subst
        if self.body in clause:
            new_terms = []
            for term in terms:
                new_terms += [self.visit(term)]

            return FreeClause(new_terms, clause.negate)

        return clause

    @visitor(Exists)
    def visit(self, quantifier: Quantifier):
        variable = quantifier.variable
        predicate = quantifier.predicate

        if self.body == variable:
            variable = self.subst

        if self.body in predicate:
            predicate = self.visit(predicate)

        return Exists(variable, predicate, quantifier.negate)

    @visitor(ForAll)
    def visit(self, quantifier):
        variable = quantifier.variable
        predicate = quantifier.predicate

        if self.body == variable:
            variable = self.subst

        if self.body in predicate:
            predicate = self.visit(predicate)

        return ForAll(variable, predicate, quantifier.negate)

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = []
        for var in relation.vars:
            if self.body in var:
                vars += [self.visit(var)]
            else:
                vars += [var]

        return RelationInstance(relation.relation_name, *vars, negate=relation.negate)

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        arg = function.arg

        if self.body in arg:
            arg = self.visit(arg)

        return FunctionInstance(function.function_name, arg, function.negate)


class SkolemVisitor:

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(And)
    def visit(self, operator: And):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return And(op1, op2, operator.negate)

    @visitor(Or)
    def visit(self, operator):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return Or(op1, op2, operator.negate)

    @visitor(FreeClause)
    def visit(self, clause):
        terms = clause.terms

        new_terms = []
        for term in terms:
            new_terms += [self.visit(term)]

        return FreeClause(new_terms, clause.negate)

    @visitor(Exists)
    def visit(self, quantifier: Quantifier):
        new_exists = self.visit(quantifier.predicate)

        if quantifier.negate:
            new_exists = ~new_exists
        return new_exists

    @visitor(ForAll)
    def visit(self, quantifier):
        skolem_function_visitor = SkolemFunctionVisitor(quantifier.variable)
        predicate = skolem_function_visitor.visit(quantifier.predicate)

        if quantifier.negate:
            predicate = ~predicate

        return predicate

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars_ = [self.visit(var) for var in relation.vars]

        return RelationInstance(relation.relation_name, *vars_, negate=relation.negate)

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        arg = self.visit(function.arg)

        return FunctionInstance(function.function_name, arg, function.negate)


class SkolemFunctionVisitor:
    skolems = 0

    def __init__(self, variable):
        self.variable = variable

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(And)
    def visit(self, operator: And):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return And(op1, op2, operator.negate)

    @visitor(Or)
    def visit(self, operator):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return Or(op1, op2, operator.negate)

    @visitor(FreeClause)
    def visit(self, clause):
        terms = clause.terms

        new_terms = []
        for term in terms:
            new_terms += [self.visit(term)]

        return FreeClause(new_terms, clause.negate)

    @visitor(Exists)
    def visit(self, quantifier: Quantifier):
        skolem = Function(f"skolem_{self.skolems}")
        self.skolems += 1

        subst_visitor = SubstVisitor(quantifier.variable, skolem(self.variable))
        new_predicate = subst_visitor.visit(quantifier.predicate)

        if quantifier.negate:
            new_predicate = ~new_predicate
        return new_predicate

    @visitor(ForAll)
    def visit(self, quantifier):
        skolem_function_visitor = SkolemFunctionVisitor(quantifier.variable)
        predicate = skolem_function_visitor.visit(quantifier.predicate)

        if quantifier.negate:
            predicate = ~predicate

        return predicate

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = [self.visit(var) for var in relation.vars]

        return RelationInstance(relation.relation_name, *vars, negate=relation.negate)

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        arg = self.visit(function.arg)

        return FunctionInstance(function.function_name, arg, function.negate)


class SimplifyVisitor:

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(And)
    def visit(self, operator: And):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return And(op1, op2, operator.negate)

    @visitor(Or)
    def visit(self, operator):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return Or(op1, op2, operator.negate)

    @visitor(FreeClause)
    def visit(self, clause):
        """Key assumption: `FreeClause' terms has a tree structure, we can unpack the first term"""
        first_term = self.visit(clause.terms[0])

        if clause.negate:
            first_term = ~first_term

        return first_term

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = [self.visit(var) for var in relation.vars]

        return RelationInstance(relation.relation_name, *vars, negate=relation.negate)

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        arg = self.visit(function.arg)

        return FunctionInstance(function.function_name, arg, function.negate)


class DistributeVisitor:

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(And)
    def visit(self, operator: And):
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return And(op1, op2, operator.negate)

    @visitor(Or)
    def visit(self, operator: Operator):
        new_op = operator
        if And in [type(new_op.operand1), type(new_op.operand2)]:
            if type(new_op.operand1) is And:
                new_op = And(Or(self.visit(new_op.operand2), self.visit(new_op.operand1.operand1)),
                             Or(self.visit(new_op.operand2), self.visit(new_op.operand1.operand2)))

            if type(new_op.operand2) is And:
                new_op = And(Or(self.visit(new_op.operand1), self.visit(new_op.operand2.operand1)),
                             Or(self.visit(new_op.operand1), self.visit(new_op.operand2.operand2)))

            op1 = self.visit(new_op.operand1)
            op2 = self.visit(new_op.operand2)

            return And(op1, op2, new_op.negate)

        return new_op

    @visitor(FreeClause)
    def visit(self, clause: FreeClause):
        terms = clause.terms

        new_terms = []
        for term in terms:
            new_terms += [self.visit(term)]

        return FreeClause(new_terms, clause.negate)

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = [self.visit(var) for var in relation.vars]

        return RelationInstance(relation.relation_name, *vars, negate=relation.negate)

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        arg = self.visit(function.arg)

        return FunctionInstance(function.function_name, arg, function.negate)


class ClausifyVisitor:

    @visitor(Literal)
    def visit(self, literal):
        return literal

    @visitor(Var)
    def visit(self, var):
        return var

    @visitor(And)
    def visit(self, operator: And):
        new_kb = KB(set())
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        new_kb += op1
        new_kb += op2

        return new_kb

    @visitor(Or)
    def visit(self, operator: Operator):
        new = Clause(set(), operator.negate)
        op1 = self.visit(operator.operand1)
        op2 = self.visit(operator.operand2)

        return new + op1 + op2

    @visitor(FreeClause)
    def visit(self, clause: FreeClause):
        terms = clause.terms

        new_terms = set()
        for term in terms:
            new_terms |= {self.visit(term)}

        return KB() + new_terms

    @visitor(RelationInstance)
    def visit(self, relation: RelationInstance):
        vars = [self.visit(var) for var in relation.vars]

        return Clause({RelationInstance(relation.relation_name, *vars, negate=relation.negate)})

    @visitor(FunctionInstance)
    def visit(self, function: FunctionInstance):
        arg = self.visit(function.arg)

        return Clause({FunctionInstance(function.function_name, arg, function.negate)})
