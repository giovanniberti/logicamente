import sys
import unittest

from mente_parser import program, make_fact, make_clause, parse_lit, make_relation, parse_relation
from predicate import Predicate, solve, subst_all
from primitives import HornKB, HornClause, And
from tests import PropositionalLogicTestCase


def main():
    path = "./underground_1"
    parser = program.parseFile(path, parseAll=True)

    superclause = []
    statements = parser.get("statements", [])

    if not statements:
        print("Empty input file. Exiting...")
        return

    for statement in parser["statements"]:
        head = statement["head"]

        if "body" in statement:
            body = statement["body"]
            clause = make_clause(head, body)
            superclause += [clause]
        else:
            if "constant" in head:
                instance = make_fact(head["constant"])
                superclause += [HornClause({instance})]
            else:
                head = head["relation"]
                superclause += [HornClause({make_relation("head")})]

    # Generate free clause with and of elements in superclause
    free_clause = superclause[0]
    clause_iter = iter(superclause)
    next(clause_iter)

    for clause in clause_iter:
        free_clause = And(clause, free_clause)

    p = Predicate(free_clause).propositionalize()
    hkb = HornKB(set())
    for clause in p.components:
        hkb += HornClause.from_clause(clause)

    # query = parse_relation("nearby(leicester_square,charing_cross)")
    # query = parse_relation("connected(leicester_square,charing_cross,northern)")
    # query = parse_lit("q")

    query = parse_relation(input("input query: "))

    query_clause = HornClause(set(query))
    result = solve(hkb, query_clause)

    print(f'backward_chain{{ {query} }}: '
          f'{result is not None}')
    if result is not None:
        print(f'result: {result}')
    pass


def run_tests():
    suite = unittest.TestSuite()
    suite.addTest(PropositionalLogicTestCase('test_clause_contains'))
    suite.addTest(PropositionalLogicTestCase('test_clause_remove'))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        main()
