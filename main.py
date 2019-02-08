import sys
import unittest

from mente_parser import program, clause as clause_parser, parse_statement
from predicate import Predicate, solve
from primitives import HornKB, HornClause, And
from tests import PropositionalLogicTestCase


def main():
    path = input("input file: ")
    parser = program.parseFile(path, parseAll=True)

    superclause = []
    statements = parser.get("statements", [])

    if not statements:
        print("Empty input file. Exiting...")
        return

    for statement in parser["statements"]:
        superclause += [parse_statement(statement)]

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

    query_input = input("input query: ") + "."
    query = parse_statement(clause_parser.parseString(query_input)["clause"])

    result = solve(hkb, query)

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
