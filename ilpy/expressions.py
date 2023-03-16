from __future__ import annotations

import ast
from typing import Any, Sequence

from ilpy import LinearConstraint, Relation


class Expression(ast.AST):
    """Base class for all expression nodes.

    Expressions allow ilpy to represent mathematical expressions in an
    intuitive syntax, and then convert to a native Constraint object.

    This class provides all of the operators and methods needed to build
    expressions. For example, to create the expression ``x + y``, you can
    write ``Variable('x') + Variable('y')``.

    Tip: you can use ``ast.dump`` to see the AST representation of an expression.
    Or, use ``print(expr)` to see the string representation of an expression.
    """

    def constraint(self) -> LinearConstraint:
        """Create a linear constraint from this expression."""
        return _expression_to_constraint(self)

    @staticmethod
    def _cast(obj: Any) -> Expression:
        """Cast object into an Expression."""
        return obj if isinstance(obj, Expression) else Constant(obj)

    def __str__(self) -> str:
        """Serialize this expression to string form."""
        return str(_ExprSerializer(self))

    # comparisons

    def __lt__(self, other: Expression | float) -> Compare:
        return Compare(self, [ast.Lt()], [other])

    def __le__(self, other: Expression | float) -> Compare:
        return Compare(self, [ast.LtE()], [other])

    def __eq__(self, other: Expression | float) -> Compare:  # type: ignore
        return Compare(self, [ast.Eq()], [other])

    def __ne__(self, other: Expression | float) -> Compare:  # type: ignore
        return Compare(self, [ast.NotEq()], [other])

    def __gt__(self, other: Expression | float) -> Compare:
        return Compare(self, [ast.Gt()], [other])

    def __ge__(self, other: Expression | float) -> Compare:
        return Compare(self, [ast.GtE()], [other])

    # binary operators
    # (note that __and__ and __or__ are reserved for boolean operators.)

    def __add__(self, other: Expression) -> BinOp:
        return BinOp(self, ast.Add(), other)

    def __radd__(self, other: Expression) -> BinOp:
        return BinOp(other, ast.Add(), self)

    def __sub__(self, other: Expression) -> BinOp:
        return BinOp(self, ast.Sub(), other)

    def __rsub__(self, other: Expression) -> BinOp:
        return BinOp(other, ast.Sub(), self)

    def __mul__(self, other: float) -> BinOp:
        return BinOp(self, ast.Mult(), other)

    def __rmul__(self, other: float) -> BinOp:
        return BinOp(other, ast.Mult(), self)

    def __truediv__(self, other: float) -> BinOp:
        return BinOp(self, ast.Div(), other)

    def __rtruediv__(self, other: float) -> BinOp:
        return BinOp(other, ast.Div(), self)

    # unary operators

    def __neg__(self) -> UnaryOp:
        return UnaryOp(ast.USub(), self)

    def __pos__(self) -> UnaryOp:
        # usually a no-op
        return UnaryOp(ast.UAdd(), self)


class Compare(Expression, ast.Compare):
    """A comparison of two or more values.

    `left` is the first value in the comparison, `ops` the list of operators,
    and `comparators` the list of values after the first element in the
    comparison.
    """

    def __init__(
        self,
        left: Expression,
        ops: Sequence[ast.cmpop],
        comparators: Sequence[Expression | float],
        **kwargs: Any,
    ) -> None:
        super().__init__(
            Expression._cast(left),
            ops,
            [Expression._cast(c) for c in comparators],
            **kwargs,
        )


class BinOp(Expression, ast.BinOp):
    """A binary operation (like addition or division).

    `op` is the operator, and `left` and `right` are any expression nodes.
    """

    def __init__(
        self,
        left: Expression | float,
        op: ast.operator,
        right: Expression | float,
        **kwargs: Any,
    ) -> None:
        super().__init__(Expression._cast(left), op, Expression._cast(right), **kwargs)


class UnaryOp(Expression, ast.UnaryOp):
    """A unary operation.

    `op` is the operator, and `operand` any expression node.
    """

    def __init__(self, op: ast.unaryop, operand: Expression, **kwargs: Any) -> None:
        super().__init__(op, Expression._cast(operand), **kwargs)


class Constant(Expression, ast.Constant):
    """A constant value.

    The `value` attribute contains the Python object it represents.
    types supported: int, float
    """

    def __init__(
        self, value: float | int, kind: str | None = None, **kwargs: Any
    ) -> None:
        if not isinstance(value, (float, int)):
            raise TypeError("Constants must be numbers")
        super().__init__(value, kind, **kwargs)


class Variable(Expression, ast.Name):
    """A variable.

    `id` holds the index as a string (becuase ast.Name requires a string).

    The special attribute `index` is added here for the purpose of storing
    the index of a variable in a solver's variable list: ``Variable('u', index=0)``
    """

    def __init__(self, id: str, index: int | None = None) -> None:
        self.index = index
        super().__init__(str(id), ctx=ast.Load())

    def __hash__(self) -> int:
        # allow use as dict key
        return id(self)


# conversion between ast comparison operators and ilpy relations
# TODO: support more less/greater than operators
OPERATOR_MAP: dict[type[ast.cmpop], Relation] = {
    ast.LtE: Relation.LessEqual,
    ast.Eq: Relation.Equal,
    ast.GtE: Relation.GreaterEqual,
}


def _get_relation(expr: Expression) -> Relation | None:
    seen_compare = False
    relation: Relation | None = None
    for sub in ast.walk(expr):
        if isinstance(sub, Compare):
            if seen_compare:
                raise ValueError("Only single comparisons are supported")

            op_type = type(sub.ops[0])
            try:
                relation = OPERATOR_MAP[op_type]
            except KeyError as e:
                raise ValueError(f"Unsupported comparison operator: {op_type}") from e
            seen_compare = True
    return relation


def _expression_to_constraint(expr: Expression) -> LinearConstraint:
    """Convert an expression to a `LinearConstraint`."""
    constraint = LinearConstraint()
    if relation := _get_relation(expr):
        constraint.set_relation(relation)
    for var, coefficient in _get_coefficients(expr).items():
        if var is None:
            # None is the constant term, which is the right hand side of the
            # comparison.
            constraint.set_value(-coefficient)
        elif coefficient != 0:
            if var.index is None:
                raise ValueError(
                    "All variables in a constraint expression must have an index"
                )
            constraint.set_coefficient(var.index, coefficient)
    return constraint


def _get_coefficients(
    expr: Expression | ast.expr,
    coeffs: dict[Variable | None, float] | None = None,
    scale: int = 1,
) -> dict[Variable | None, float]:
    """Get the coefficients of a linear expression.

    The coefficients are returned as a dictionary mapping Variable to coefficient.
    The key `None` is used for the constant term.

    Note also that expressions on the right side of a comparison are negated,
    (so that the comparison is effectively against zero.)

    Args:
        expr: The expression to get the coefficients of.
        coeffs: The dictionary to add the coefficients to. If not given, a new
            dictionary is created.
        scale: The scale to apply to the coefficients. This is used to negate
            expressions on the right side of a comparison or scale for multiplication.

    Example:

        >>> u = Variable('u')
        >>> v = Variable('v')
        >>> _get_coefficients(2 * u - 5 * v <= 7)
        {u: 2, v: -5, None: -7}

        coefficients are simplified in the process:
        >>> _get_coefficients(2 * u - (u + 2 * u) <= 7)
        {u: -1, None: -7}
    """
    if coeffs is None:
        coeffs = {}

    if isinstance(expr, Compare):
        if len(expr.ops) != 1:
            raise ValueError("Only single comparisons are supported")
        _get_coefficients(expr.left, coeffs)
        # negate the right hand side of the comparison
        _get_coefficients(expr.comparators[0], coeffs, -1)

    elif isinstance(expr, BinOp):
        if isinstance(expr.op, (ast.Mult, ast.Div)):
            if isinstance(expr.right, Constant):
                e = expr.left
                v = expr.right.value
            elif isinstance(expr.left, Constant):
                e = expr.right
                v = expr.left.value
            else:
                # XXX: will we ever need multiplication by a variable?
                raise ValueError("Multiplication must be by a constant")
            scale *= 1 / v if isinstance(expr.op, ast.Div) else v
            _get_coefficients(e, coeffs, scale)
        else:
            _get_coefficients(expr.left, coeffs, scale)
            if isinstance(expr.op, (ast.USub, ast.Sub)):
                scale = -scale
            _get_coefficients(expr.right, coeffs, scale)
    elif isinstance(expr, UnaryOp):
        if isinstance(expr.op, ast.USub):
            scale = -scale
        _get_coefficients(expr.operand, coeffs, scale)
    elif isinstance(expr, Constant):
        coeffs.setdefault(None, 0)
        coeffs[None] += expr.value * scale
    elif isinstance(expr, Variable):
        coeffs.setdefault(expr, 0)
        coeffs[expr] += scale
    else:
        raise ValueError(f"Unsupported expression type: {type(expr)}")

    return coeffs


class _ExprSerializer(ast.NodeVisitor):
    """Serializes an :class:`Expression` into a string.

    Used above in `Expression.__str__`.
    """

    OP_MAP: dict[type[ast.operator] | type[ast.cmpop] | type[ast.unaryop], str] = {
        # ast.cmpop
        ast.Eq: "==",
        ast.Gt: ">",
        ast.GtE: ">=",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.LtE: "<=",
        # ast.operator
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        # ast.unaryop
        ast.UAdd: "+",
        ast.USub: "-",
    }

    def __init__(self, node: Expression | None = None) -> None:
        self._result: list[str] = []

        def write(*params: ast.AST | str) -> None:
            for item in params:
                if isinstance(item, ast.AST):
                    self.visit(item)
                elif item:
                    self._result.append(item)

        self.write = write

        if node is not None:
            self.visit(node)

    def __str__(self) -> str:
        return "".join(self._result)

    def visit_Variable(self, node: Variable) -> None:  # type: ignore
        self.write(node.id)

    def visit_Constant(self, node: ast.Constant) -> None:
        self.write(repr(node.value))

    def visit_Compare(self, node: ast.Compare) -> None:
        self.visit(node.left)
        for op, right in zip(node.ops, node.comparators):
            self.write(f" {self.OP_MAP[type(op)]} ", right)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        opstring = f" {self.OP_MAP[type(node.op)]} "
        args: list[ast.AST | str] = [node.left, opstring, node.right]
        if isinstance(node.op, ast.Mult):
            if isinstance(node.left, ast.BinOp):
                args[:1] = ["(", node.left, ")"]
            if isinstance(node.right, ast.BinOp):
                args[2:] = ["(", node.right, ")"]
        self.write(*args)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        sym = self.OP_MAP[type(node.op)]
        self.write(sym, " " if sym.isalpha() else "", node.operand)
