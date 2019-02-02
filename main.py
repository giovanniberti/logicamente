import sys
import unittest

from tests import PropositionalLogicTestCase


def main():
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
