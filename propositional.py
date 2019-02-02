from primitives import PrimitiveClause, Var


def unit_resolution(clause: PrimitiveClause, literal: Var) -> PrimitiveClause:
    """Unit resolution rule."""
    return clause - ~literal
