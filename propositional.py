from primitives import Clause, Var, KB


def unit_resolution(clause: Clause, literal: Var) -> Clause:
    """Unit resolution rule."""
    return clause - ~literal
