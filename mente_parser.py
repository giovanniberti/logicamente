from pyparsing import Word, alphanums, delimitedList, Group, Optional, cStyleComment, ZeroOrMore, Forward, nestedExpr

from first_order import Var, Relation, Exists
from primitives import Literal as Lit, FreeClause, Implies, And, HornClause
from visitor import FreeVarVisitor

upper = alphanums.upper() + "_"
lower = alphanums.lower() + "_"

identifier = Word(lower).setResultsName("name", listAllMatches=True)
variable = Word(upper).setResultsName("var_name", listAllMatches=True)
relation_par = Forward()
list_par = Forward().setResultsName("list")
parameter = variable ^ identifier ^ relation_par ^ list_par

comma_list = delimitedList(parameter)
head_tail_list = parameter.setResultsName("head") + "|" + variable.setResultsName("tail")
# list = "[" + (comma_list ^ head_tail_list) + "]"
list_parser = nestedExpr(opener="[", closer="]", content=comma_list)
list_par << list_parser

relation = Group(identifier.setResultsName("relation_name") + "(" + Optional(Group(delimitedList(parameter))
                                                                             .setResultsName(
    "parameters")) + ")").setResultsName("relation")
relation_par << relation

literal_relation = identifier.setResultsName("relation_name") + "(" + Group(delimitedList(identifier)) \
    .setResultsName("literals") + ")"

constant = Group(literal_relation ^ identifier).setResultsName("constant")

term = constant ^ relation

clause = Group(Group(term).setResultsName("head") + Optional(
    ":-" + Group(delimitedList(term)).setResultsName("body")) + ".").setResultsName("clause")
comment = cStyleComment

program = ZeroOrMore(clause).setResultsName("statements").ignore(comment)


def make_relation(relation_parse):
    name = relation_parse["relation_name"]
    relation = Relation(name)
    parameters = []

    parse_parameters = relation_parse.get("parameters", [])

    if parse_parameters:
        variables = list(parse_parameters.get("var_name", []))
        literals = list(parse_parameters.get("name", []))
        lists = list(parse_parameters.get("list", []))

        for par in parse_parameters:
            if par in variables:
                parameters += [Var(par)]
            elif par in literals:
                parameters += [Lit(par)]
            elif par in lists:
                rel_list = "list(" + ",".join([str(p) for p in par.asList()]) + ")"
                parameters += [parse_relation(rel_list)]
                pass
            else:
                parameters += [make_relation(par)]

    instance = relation(*parameters)

    return instance


def make_fact(fact_parse):
    if "name" in fact_parse.keys():
        return Lit(fact_parse["name"][0])
    else:
        name = fact_parse["relation_name"]
        relation = Relation(name)

        literals = []
        for literal in fact_parse["literals"]:
            literals += [Lit(literal)]

        return relation(*literals)


def make_body_term(term_parse):
    if "name" in term_parse:
        term = make_fact(term_parse)
    else:
        term = make_relation(term_parse)

    return term


def make_clause(head_parse, body_parse):
    if "constant" in head_parse:
        head = make_fact(head_parse["constant"])
    else:
        head = make_relation(head_parse["relation"])

    iter_body = iter(body_parse)

    first_parse = next(iter_body)
    body_clauses = make_body_term(first_parse)

    for term in iter_body:
        body_clauses = And(make_body_term(term), body_clauses)

    body = body_clauses

    vars_visitor = FreeVarVisitor()
    head_vars = vars_visitor.visit(head)
    body_vars = vars_visitor.visit(body)
    vars = set(head_vars + body_vars)

    clause = Implies(body, head)
    for var in vars:
        clause = Exists(var, clause)

    return FreeClause([clause])


def parse_relation(string):
    relation_parse = relation.parseString(string)["relation"]
    return make_relation(relation_parse)


def parse_var(string):
    return Var(variable.parseString(string)["var_name"])


def parse_lit(string):
    return Lit(identifier.parseString(string)["name"][0])


def parse_statement(statement_parse):
    head = statement_parse["head"]
    if "body" in statement_parse:
        body = statement_parse["body"]
        clause = make_clause(head, body)
        return clause
    else:
        if "constant" in head:
            instance = make_fact(head["constant"])
            return HornClause({instance})
        else:
            head = head["relation"]
            return HornClause({make_relation(head)})
