"""Safe Python execution tool for Vaani AI."""

import io
import re
import sys
from typing import Dict, Any
from vaani.tools.base import BaseTool, ToolResult


class PythonRunnerTool(BaseTool):
    """Tool for executing short Python code snippets or algorithmic computations."""

    name: str = "python_runner"
    description: str = "Runs Python scripts, algorithms, data manipulations, and returns stdout."
    icon: str = "🐍"

    PYTHON_TRIGGERS = [
        re.compile(r"\b(run python|execute python|eval python|python code|script|run code)\b", re.IGNORECASE),
        re.compile(r"```python[\s\S]*?```", re.IGNORECASE),
        re.compile(r"\b(def\s+\w+|import\s+\w+|for\s+\w+\s+in\s+range)\b", re.IGNORECASE),
    ]

    def can_handle(self, query: str) -> bool:
        """Check if the query explicitly asks to run Python code."""
        for pattern in self.PYTHON_TRIGGERS:
            if pattern.search(query):
                return True
        return False

    def extract_code(self, query: str) -> str:
        """Extract code block if wrapped in markdown or inline."""
        code_block = re.search(r"```(?:python)?([\s\S]*?)```", query)
        if code_block:
            return code_block.group(1).strip()

        # If user said "run python: sum(range(10))"
        inline = re.sub(r"^(run python|execute python|python code|run code|python)\s*[:\-\,]\s*", "", query, flags=re.IGNORECASE)
        return inline.strip()

    def execute(self, query: str) -> ToolResult:
        code = self.extract_code(query)
        if not code:
            return ToolResult(
                tool_name=self.name,
                input_data=query,
                output_data="No valid Python code found to execute.",
                success=False,
                error="Empty code block"
            )

        # Block dangerous builtins
        disallowed = ["os.system", "subprocess", "shutil", "socket", "open(", "import os", "import sys", "exit()", "quit()"]
        for bad in disallowed:
            if bad in code:
                return ToolResult(
                    tool_name=self.name,
                    input_data=code,
                    output_data=f"Security notice: '{bad}' is restricted in the sandbox environment.",
                    success=False,
                    error="Restricted standard library call"
                )

        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        safe_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "list": list,
                "dict": dict,
                "set": set,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "map": map,
                "filter": filter,
            }
        }

        try:
            # If code is a single expression without print, evaluate and print it
            try:
                compiled = compile(code, "<string>", "eval")
                eval_res = eval(compiled, safe_globals)
                if eval_res is not None:
                    print(eval_res)
            except SyntaxError:
                # Execute multi-line statement
                compiled = compile(code, "<string>", "exec")
                exec(compiled, safe_globals)

            output = redirected_output.getvalue().strip()
            if not output:
                output = "Code executed successfully with 0 output."

            # Truncate if excessively long for social media
            if len(output) > 300:
                output = output[:300] + "..."

            return ToolResult(
                tool_name=self.name,
                input_data=code,
                output_data=output,
                success=True
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                input_data=code,
                output_data=f"Runtime error: {e}",
                success=False,
                error=str(e)
            )
        finally:
            sys.stdout = old_stdout
