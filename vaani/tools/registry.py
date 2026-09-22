"""Registry and orchestrator for Vaani AI tools."""

import logging
from typing import Dict, List, Optional
from vaani.tools.base import BaseTool, ToolResult
from vaani.tools.calculator import CalculatorTool
from vaani.tools.web_search import WebSearchTool
from vaani.tools.python_runner import PythonRunnerTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Manages available tools and coordinates autonomous tool selection & execution."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Register default tool suite
        self.register(CalculatorTool())
        self.register(PythonRunnerTool())
        self.register(WebSearchTool())

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s (%s)", tool.name, tool.icon)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def find_matching_tool(self, query: str) -> Optional[BaseTool]:
        """
        Determine if any registered tool's heuristic matches the query.
        Priority order: Calculator -> PythonRunner -> WebSearch
        """
        # 1. Calculator
        calc = self._tools.get("calculator")
        if calc and calc.can_handle(query):
            return calc

        # 2. Python Runner
        py_tool = self._tools.get("python_runner")
        if py_tool and py_tool.can_handle(query):
            return py_tool

        # 3. Web Search
        search = self._tools.get("web_search")
        if search and search.can_handle(query):
            return search

        return None

    def execute_matching_tool(self, query: str) -> Optional[ToolResult]:
        """Detect and execute a matching tool if one is triggered by the query."""
        tool = self.find_matching_tool(query)
        if not tool:
            return None

        logger.info("Executing tool '%s' for query: %s", tool.name, query)
        try:
            return tool.execute(query)
        except Exception as e:
            logger.error("Error running tool '%s': %s", tool.name, e)
            return ToolResult(
                tool_name=tool.name,
                input_data=query,
                output_data=f"Tool error: {e}",
                success=False,
                error=str(e)
            )

    def format_tool_prompt_description(self) -> str:
        """Generate markdown description of all available tools for LLM prompts."""
        lines = ["Available Tools for solving user queries:"]
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)


# Singleton instance
default_registry = ToolRegistry()
