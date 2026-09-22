"""Configuration management for Vaani AI."""

from typing import Literal, Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Bot Handle
    bot_handle: str = Field(default="vaaniai", description="Twitter handle to monitor (without @)")

    # Hugging Face Settings
    hf_mode: Literal["local", "inference_api", "mock"] = Field(
        default="mock",
        description="Mode for Hugging Face inference: local, inference_api, or mock"
    )
    hf_model_id: str = Field(
        default="Qwen/Qwen2.5-0.5B-Instruct",
        description="Hugging Face Model ID or local directory path"
    )
    hf_token: Optional[str] = Field(
        default=None,
        description="Hugging Face API token (for inference_api or gated models)"
    )
    hf_device: str = Field(
        default="cpu",
        description="Device for local inference: 'cpu' or 'cuda'"
    )
    hf_lora_path: Optional[str] = Field(
        default=None,
        description="Optional path to local fine-tuned LoRA adapter directory"
    )

    # Generation Parameters
    max_new_tokens: int = Field(default=150, description="Maximum new tokens to generate")
    temperature: float = Field(default=0.7, description="Sampling temperature")

    # Polling & Execution
    poll_interval_seconds: int = Field(default=30, description="Seconds between mention polls")

    # Twitter API v2 Credentials
    twitter_api_key: Optional[str] = Field(default=None)
    twitter_api_secret: Optional[str] = Field(default=None)
    twitter_access_token: Optional[str] = Field(default=None)
    twitter_access_secret: Optional[str] = Field(default=None)
    twitter_bearer_token: Optional[str] = Field(default=None)

    # Storage Paths
    database_path: str = Field(default="data/vaani.db", description="Path to SQLite storage")
    dataset_path: str = Field(default="data/dataset.jsonl", description="Path to training dataset export")

    @property
    def bot_mention(self) -> str:
        """Returns the mention tag, e.g. '@vaaniai'"""
        return f"@{self.bot_handle.lstrip('@').lower()}"


# Global configuration singleton helper
def get_settings() -> Settings:
    return Settings()
