from collections import defaultdict

from primitives import Clause, Var, HornKB, HornClause


def unit_resolution(clause: Clause, literal: Var) -> Clause:
    """Unit resolution rule."""
    return clause - ~literal


def forward_chaining_solve(knowledge_base: HornKB, query: Var) -> bool:
    """Propositional logic entailment check with forward chaining.
    (Answers to question: knowledge_base ⊨? query)"""

    knowledge_base = HornKB(knowledge_base.clauses)
    count = {clause: len(clause.body) for clause in knowledge_base}
    inferred = defaultdict(bool)
    knowns = [clause.head for clause in knowledge_base]

    while knowns:
        p = knowns.pop()

        if p == query:
            return True
        if not inferred[p]:
            inferred[p] = True

            clauses_with_p = [clause for clause in knowledge_base if p in clause]

            for clause in clauses_with_p:
                count[clause] -= 1

                if count[clause] == 0:
                    knowns += [HornClause.from_clause(clause).head]

    return False
