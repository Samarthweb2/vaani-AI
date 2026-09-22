"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Interface for LLM generation backends."""

    @abstractmethod
    def generate_response(
        self,
        query: str,
        author: str = "user",
        context: Optional[str] = None
    ) -> str:
        """
        Generate a solution/response to the user's query.

        Args:
            query: The extracted user question/prompt.
            author: The username of the person asking.
            context: Any parent tweet or thread context.

        Returns:
            The generated response string.
        """
        pass
