import ast
import math
import operator
import re

from app.agent.tools.base import ToolExecution


_ALLOWED_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorTool:
    name = "calculator"

    @staticmethod
    def extract_expression(text: str) -> str | None:
        # Safe, intentionally small grammar. This is not Python execution.
        matches = re.findall(r"[0-9+\-*/%().\s]{3,}", text)
        candidates = [item.strip() for item in matches if any(ch.isdigit() for ch in item)]
        return max(candidates, key=len) if candidates else None

    def _evaluate(self, expression: str) -> float | int:
        if len(expression) > 200:
            raise ValueError("Expression is too long")

        tree = ast.parse(expression, mode="eval")

        def visit(node):
            if isinstance(node, ast.Expression):
                return visit(node.body)
            if isinstance(node, ast.Constant):
                if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                    raise ValueError("Only numeric values are allowed")
                return node.value
            if type(node) in _ALLOWED_BINARY:
                left = visit(node.left)
                right = visit(node.right)
                if type(node.op) in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                    raise ValueError("Division by zero")
                value = _ALLOWED_BINARY[type(node.op)](left, right)
                if isinstance(value, (int, float)) and math.isfinite(value):
                    return value
                raise ValueError("Invalid numeric result")
            if type(node) in _ALLOWED_UNARY:
                return _ALLOWED_UNARY[type(node.op)](visit(node.operand))
            raise ValueError("Unsupported expression")

        result = visit(tree)
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result

    def run(self, text: str) -> ToolExecution:
        expression = self.extract_expression(text)
        if not expression:
            return ToolExecution(
                name=self.name,
                input=text,
                output="No arithmetic expression found.",
                success=False,
            )
        try:
            result = self._evaluate(expression)
            return ToolExecution(
                name=self.name,
                input=expression,
                output=str(result),
            )
        except Exception as exc:
            return ToolExecution(
                name=self.name,
                input=expression,
                output=f"Calculator error: {exc}",
                success=False,
            )


calculator_tool = CalculatorTool()
