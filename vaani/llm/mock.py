"""Mock LLM Provider for testing and offline development."""

from typing import Optional
from vaani.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Mock provider that generates helpful test responses without downloading weights.
    Ideal for unit tests and local CLI simulation before model setup.
    """

    def generate_response(
        self,
        query: str,
        author: str = "user",
        context: Optional[str] = None
    ) -> str:
        q_lower = query.lower()

        if "hello" in q_lower or "hi" in q_lower:
            return f"Hello @{author}! I'm Vaani AI. How can I help you today?"
        elif "who are you" in q_lower:
            return "I am Vaani AI, an autonomous social media AI agent ready to solve your questions whenever tagged!"
        elif "fine" in q_lower and "tune" in q_lower:
            return "Vaani AI logs each interaction into a dataset for continuous Hugging Face fine-tuning with LoRA!"
        else:
            return (
                f"Regarding '{query[:60]}...': Here is a direct solution from Vaani AI! "
                "Break down the problem, inspect the core components, and verify iteratively."
            )
