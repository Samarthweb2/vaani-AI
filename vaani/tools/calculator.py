"""Safe mathematical calculation tool for Vaani AI."""

import ast
import math
import operator
import re
from typing import Dict, Any, Union
from vaani.tools.base import BaseTool, ToolResult


# Supported safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Supported math functions
SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "pow": math.pow,
    "abs": abs,
    "round": round,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "factorial": math.factorial,
}

SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def safe_eval_ast(node: Union[ast.AST, Any]) -> Union[int, float]:
    """Recursively evaluate an AST expression safely without arbitrary code execution."""
    if isinstance(node, ast.Expression):
        return safe_eval_ast(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.Name):
        if node.id in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[node.id]
        raise ValueError(f"Unknown variable or constant: {node.id}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            left = safe_eval_ast(node.left)
            right = safe_eval_ast(node.right)
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            operand = safe_eval_ast(node.operand)
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
            args = [safe_eval_ast(arg) for arg in node.args]
            return SAFE_FUNCTIONS[node.func.id](*args)
        raise ValueError(f"Unsupported function call: {ast.dump(node.func)}")
    else:
        raise ValueError(f"Unsupported syntax expression: {type(node)}")


class CalculatorTool(BaseTool):
    """Tool for evaluating arithmetic and mathematical expressions."""

    name: str = "calculator"
    description: str = "Evaluates mathematical expressions, arithmetic, percentages, and basic algebra."
    icon: str = "🧮"

    CALC_TRIGGER_PATTERNS = [
        re.compile(r"(\d+\s*[\+\-\*\/\^%]\s*\d+)", re.IGNORECASE),
        re.compile(r"\b(calculate|compute|math|what is|solve)\b.*[\d\+\-\*\/\^%]", re.IGNORECASE),
        re.compile(r"\b(\d+(\.\d+)?)\s*percent\s*(of)?\s*(\d+(\.\d+)?)", re.IGNORECASE),
        re.compile(r"\b(sqrt|square root|factorial)\b", re.IGNORECASE),
    ]

    def can_handle(self, query: str) -> bool:
        """Check if the query is asking for a math calculation."""
        for pattern in self.CALC_TRIGGER_PATTERNS:
            if pattern.search(query):
                return True
        return False

    def extract_expression(self, query: str) -> str:
        """Extract or clean the mathematical expression from natural text."""
        # Handle percentage: "20 percent of 500" -> "(20 / 100) * 500"
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:of)?\s*(\d+(?:\.\d+)?)", query, re.IGNORECASE)
        if pct_match:
            pct_val = pct_match.group(1)
            base_val = pct_match.group(2)
            return f"({pct_val} / 100) * {base_val}"

        # Handle square root: "square root of 144" or "sqrt of 144"
        sqrt_match = re.search(r"(?:square root of|sqrt of|sqrt)\s*(\d+(?:\.\d+)?)", query, re.IGNORECASE)
        if sqrt_match:
            return f"sqrt({sqrt_match.group(1)})"

        # Look for explicit math expressions like 125 * 84 or 45 + 18 / 2
        expr_match = re.search(r"([\d\.\s\+\-\*\/\(\)\^%]{3,})", query)
        if expr_match:
            expr = expr_match.group(1).strip()
            # Replace ^ with **
            expr = expr.replace("^", "**")
            # Replace x with * if between numbers e.g. 5 x 6
            expr = re.sub(r"(\d)\s*[xX]\s*(\d)", r"\1 * \2", expr)
            return expr

        return query.strip()

    def execute(self, query: str) -> ToolResult:
        expr = self.extract_expression(query)
        try:
            tree = ast.parse(expr, mode="eval")
            result = safe_eval_ast(tree)

            # Format nicely (e.g. 432.0 -> 432)
            if isinstance(result, float) and result.is_integer():
                result_formatted = str(int(result))
            elif isinstance(result, float):
                result_formatted = f"{result:.4f}".rstrip("0").rstrip(".")
            else:
                result_formatted = str(result)

            return ToolResult(
                tool_name=self.name,
                input_data=expr,
                output_data=f"{expr} = {result_formatted}",
                success=True
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                input_data=expr,
                output_data=f"Calculation error: {e}",
                success=False,
                error=str(e)
            )
