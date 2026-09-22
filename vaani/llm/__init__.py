"""LLM Engine for Vaani AI."""

from vaani.llm.base import BaseLLMProvider
from vaani.llm.mock import MockLLMProvider
from vaani.llm.hf_local import HuggingFaceLocalProvider
from vaani.llm.hf_inference import HuggingFaceInferenceProvider


def create_llm_provider(settings) -> BaseLLMProvider:
    """Factory function to instantiate the configured LLM provider."""
    mode = settings.hf_mode.lower()

    if mode == "local":
        return HuggingFaceLocalProvider(
            model_id=settings.hf_model_id,
            device=settings.hf_device,
            token=settings.hf_token,
            lora_path=settings.hf_lora_path,
            max_new_tokens=settings.max_new_tokens,
            temperature=settings.temperature,
        )
    elif mode == "inference_api":
        return HuggingFaceInferenceProvider(
            model_id=settings.hf_model_id,
            token=settings.hf_token,
            max_new_tokens=settings.max_new_tokens,
            temperature=settings.temperature,
        )
    elif mode == "mock":
        return MockLLMProvider()
    else:
        raise ValueError(f"Unknown HF_MODE: '{mode}'. Expected 'local', 'inference_api', or 'mock'.")
