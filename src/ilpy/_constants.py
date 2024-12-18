from enum import IntEnum, auto


class VariableType(IntEnum):
    Continuous = auto()
    Integer = auto()
    Binary = auto()


class Sense(IntEnum):
    Minimize = auto()
    Maximize = auto()


class Relation(IntEnum):
    LessEqual = auto()
    Equal = auto()
    GreaterEqual = auto()
