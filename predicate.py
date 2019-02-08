from dataclasses import dataclass

from first_order import Var, RelationInstance, FunctionInstance
from primitives import FreeClause, HornKB, HornClause, Implies, Or
from visitor import CanonicalizeVisitor, SubstVisitor, SkolemVisitor, GlobalizeVisitor, SimplifyVisitor, \
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
        components = clausify_visitor.visit(components).clauses

        return Predicate(components)


def unify(x, y, subst):
    if subst is None:
        return None
    elif x == y:
        return subst
    elif type(x) is Var:
        return unify_var(x, y, subst)
    elif type(y) is Var:
        return unify_var(y, x, subst)
    elif [type(x), type(y)] == [RelationInstance, RelationInstance]:
        return unify(x.relation_name, y.relation_name, unify(x.vars, y.vars, subst))
    elif [type(x), type(y)] == [FunctionInstance, FunctionInstance]:
        return unify(x.function_name, y.function_name, unify(x.arg, y.arg, subst))
    elif [type(x), type(y)] == [list, list] and len(x) == len(y):
        if not x:
            return subst
        return unify(x[0], y[0], unify(x[1:], y[1:], subst))
    elif [type(x), type(y)] == [tuple, tuple]:
        return unify(list(x), list(y), subst)
    else:
        return None


def unify_var(var, val, subst):
    if var == val:
        return subst
    elif var in subst:
        unify(subst[var], val, subst)
    elif type(val) is Var and val in subst:
        unify(var, val, subst)
    elif occurs(var, val, subst):
        return None
    subst = {**subst, **{var: val}}

    return subst


def occurs(var, x, subst):
    if var == x:
        return True
    elif x in subst:
        return occurs(var, subst[x], subst)
    elif type(x) is list:
        return occurs(var, x[0], subst) or occurs(var, x[1:], subst)
    return False


def rule_iter_for_goal(kb: HornKB, goal: HornClause):
    done = []
    for rule in kb:
        done += [rule]
        todo = [clause for clause in kb if clause not in done]
        todo_bodies = [term for clause in todo for term in [body_term for body_term in clause.body]]
        done_heads = [term for clause in done for term in [body_term for body_term in clause.head]]
        if ~goal in todo_bodies and goal in done_heads:
            goal_clause = prettify([clause for clause in done if goal == clause.head][0])
            offending_clause = prettify([clause for clause in todo if ~goal in clause.body][0])
            raise RuntimeError(f"cycle detected while trying to prove {goal}.\n"
                               f"There is at least one clause to analyze which has goal in its body (negated)\n"
                               f"cycle: {str(goal_clause)} (current) -> {str(offending_clause)} (todo) -> {str(goal_clause)}\n"
                               f"while having already analyzed a clause with goal in head\n"
                               f"already analyzed: {[str(c) for c in done]} \ntodo: {[str(c) for c in todo]}\n")
        yield rule


def backward_chain_query(kb: HornKB, query):
    return backward_chain_or(kb, query.head, {})


def backward_chain_or(kb: HornKB, goal, subst):
    for rule in rule_iter_for_goal(kb, goal):
        # body => head
        # FOL-BC-AND (KB , body, UNIFY (head, goal , θ))
        for new_subst in backward_chain_and(kb, rule.body, unify(rule.head, goal, subst)):
            yield new_subst


def subst_all(clause, subst):
    new_clause = clause
    for (body, new) in subst.items():
        subst_visitor = SubstVisitor(body, new)
        new_clause = subst_visitor.visit(new_clause)
    return new_clause


def backward_chain_and(kb: HornKB, goals, subst):
    if subst is None:
        return
    elif len(goals) == 0:
        yield subst
    else:
        for substs1 in backward_chain_or(kb, subst_all(~goals[0], subst), subst):
            for subst2 in backward_chain_and(kb, goals[1:], substs1):
                yield subst2


def solve(kb: HornKB, query):
    subst_gen = backward_chain_query(kb, query)

    for subst in subst_gen:
        return subst_all(FreeClause(list(query.terms)), subst)

    return None


def prettify(clause: HornClause):
    new_body = HornClause._make_or(clause.body)
    free_clause = FreeClause([Or(clause.head, ~new_body)])

    new_terms = []
    canonicalize = CanonicalizeVisitor()
    for term in free_clause.terms:
        if type(term) is Or:  # from Horn's, must be one positive and one negative
            if term.operand1.negate:
                new_terms += Implies(canonicalize.visit(term.operand1), term.operand2)
            else:
                new_terms += [Implies(canonicalize.visit(term.operand2), term.operand1)]
        else:
            new_terms += [term]

    return FreeClause(new_terms)
