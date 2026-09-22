"""Base class and data contracts for Vaani AI tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result returned by a tool execution."""
    tool_name: str
    input_data: str
    output_data: str
    success: bool = True
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all tools accessible to Vaani AI."""

    name: str = ""
    description: str = ""
    icon: str = "🔧"

    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """Heuristic or pattern check to determine if this tool should handle the query."""
        pass

    @abstractmethod
    def execute(self, query: str) -> ToolResult:
        """Execute the tool on the given user query or input string."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return a structured schema description of this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "icon": self.icon
        }
