from dataclasses import dataclass
from primitives import Literal


@dataclass
class Relation:
    name: str

    def __call__(self, *args, **kwargs):
        if len(args) != 2:
            raise RuntimeError("wrong number of arguments in relation (two arguments required)")

        return RelationInstance(self.name, args[0], args[1])


@dataclass
class RelationInstance:
    relation_name: str
    var1: Literal
    var2: Literal


@dataclass
class Function:
    name: str

    def __call__(self, *args, **kwargs):
        if len(args) != 1:
            raise RuntimeError("wrong number of arguments in function (one argument required)")

        return FunctionInstance(self.name, args[0])


@dataclass
class FunctionInstance:
    function_name: str
    arg: object
