"""Hugging Face Inference API Provider using huggingface_hub.InferenceClient."""

import logging
from typing import Optional
from vaani.llm.base import BaseLLMProvider
from vaani.llm.prompt import build_chat_messages

logger = logging.getLogger(__name__)


class HuggingFaceInferenceProvider(BaseLLMProvider):
    """
    Uses Hugging Face's serverless Inference API.
    Does not require downloading model weights to the local machine.
    """

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-0.5B-Instruct",
        token: Optional[str] = None,
        max_new_tokens: int = 150,
        temperature: float = 0.7,
    ):
        self.model_id = model_id
        self.token = token.strip() if (token and isinstance(token, str) and token.strip()) else None
        self.max_new_tokens = max_new_tokens
        self.temperature = max(0.01, temperature)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from huggingface_hub import InferenceClient
            self._client = InferenceClient(
                model=self.model_id,
                token=self.token,
            )
        return self._client

    def generate_response(
        self,
        query: str,
        author: str = "user",
        context: Optional[str] = None,
        tool_observation: Optional[str] = None
    ) -> str:
        client = self._get_client()
        messages = build_chat_messages(query, author, context, tool_observation)

        try:
            # Try chat completion first (for instruct/chat models)
            response = client.chat_completion(
                messages=messages,
                max_tokens=self.max_new_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("Chat completion failed on HF Inference API (%s), falling back to text_generation", e)
            prompt = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])
            prompt += "\nAssistant:"
            text = client.text_generation(
                prompt=prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
            )
            return text.strip()
