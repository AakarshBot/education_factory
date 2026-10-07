from __future__ import annotations

import ast
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from question import Question


class ValidationError(ValueError):
    pass


_ALLOWED_BINARY_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
}


def _evaluate(node: ast.AST) -> Fraction:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(str(node.value))

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINARY_OPS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ValidationError("division by zero")
        if isinstance(node.op, ast.Pow):
            if right.denominator != 1 or abs(right.numerator) > 12:
                raise ValidationError("unsupported exponent")
            return left ** right.numerator
        return _ALLOWED_BINARY_OPS[type(node.op)](left, right)

    raise ValidationError("unsupported expression")


def evaluate_math_expression(expression: str) -> Fraction:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValidationError("invalid expression") from exc
    return _evaluate(tree)


def parse_numeric_answer(answer: str) -> Fraction:
    cleaned = answer.strip().replace(",", "").replace("₹", "").replace("%", "")
    if not cleaned:
        raise ValidationError("empty numeric answer")

    if "/" in cleaned:
        parts = cleaned.split("/")
        if len(parts) == 2:
            try:
                return Fraction(int(parts[0].strip()), int(parts[1].strip()))
            except (ValueError, ZeroDivisionError) as exc:
                raise ValidationError("invalid fraction answer") from exc

    try:
        return Fraction(Decimal(cleaned))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError("answer is not numeric") from exc


def validate_math_answer(expression: str, correct_answer: str) -> None:
    expected = evaluate_math_expression(expression)
    actual = parse_numeric_answer(correct_answer)
    if expected != actual:
        raise ValidationError(
            f"answer mismatch: expression={expected}, answer={actual}"
        )


def validate_question(question: Question, *, math_expression: str | None = None) -> None:
    if question.subject.lower() == "maths" and math_expression is None:
        raise ValidationError("Maths questions require a machine-checkable expression")

    if question.subject.lower() == "maths":
        validate_math_answer(math_expression, question.correct_answer)

    if question.choices is not None:
        if len(question.choices) < 2:
            raise ValidationError("multiple-choice questions require at least two choices")
        if len(set(question.choices)) != len(question.choices):
            raise ValidationError("multiple-choice choices must be unique")
        if question.correct_answer not in question.choices:
            raise ValidationError("correct answer must be one of the choices")
