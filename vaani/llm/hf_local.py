"""Local Hugging Face Transformers Provider supporting local inference and fine-tuned LoRA weights."""

import logging
from typing import Optional
from vaani.llm.base import BaseLLMProvider
from vaani.llm.prompt import build_chat_messages, build_raw_prompt

logger = logging.getLogger(__name__)


class HuggingFaceLocalProvider(BaseLLMProvider):
    """
    Runs inference locally using Hugging Face's `transformers` library.
    Supports base models as well as fine-tuned LoRA adapters (via PEFT).
    """

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-0.5B-Instruct",
        device: str = "cpu",
        token: Optional[str] = None,
        lora_path: Optional[str] = None,
        max_new_tokens: int = 150,
        temperature: float = 0.7,
    ):
        self.model_id = model_id
        self.device = device
        self.token = token.strip() if (token and isinstance(token, str) and token.strip()) else None
        self.lora_path = lora_path
        self.max_new_tokens = max_new_tokens
        self.temperature = max(0.01, temperature)

        self._tokenizer = None
        self._model = None

    def _load_model(self):
        """Lazy load model and tokenizer on first call."""
        if self._model is not None and self._tokenizer is not None:
            return

        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        logger.info("Loading tokenizer for %s...", self.model_id)
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            token=self.token,
            trust_remote_code=True,
        )

        logger.info("Loading model weights for %s onto %s...", self.model_id, self.device)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            token=self.token,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True,
        )

        if self.device == "cpu":
            model.to("cpu")

        # Load fine-tuned LoRA adapter if specified
        if self.lora_path:
            logger.info("Loading fine-tuned LoRA adapter from %s...", self.lora_path)
            try:
                from peft import PeftModel
                model = PeftModel.from_pretrained(model, self.lora_path)
                logger.info("LoRA adapter merged successfully.")
            except Exception as e:
                logger.error("Failed to load LoRA adapter from %s: %s", self.lora_path, e)
                raise

        model.eval()
        self._model = model

    def generate_response(
        self,
        query: str,
        author: str = "user",
        context: Optional[str] = None
    ) -> str:
        self._load_model()
        import torch

        messages = build_chat_messages(query, author, context)

        # Apply chat template if supported
        if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template:
            input_text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            input_text = build_raw_prompt(query, author, context)

        inputs = self._tokenizer(input_text, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=True,
                temperature=self.temperature,
                top_p=0.9,
                pad_token_id=self._tokenizer.eos_token_id or self._tokenizer.pad_token_id,
            )

        # Decode only the generated new tokens
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self._tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

        # Guard against generic refusal phrases
        refusal_markers = [
            "i'm sorry, but i can't assist",
            "i cannot assist with that",
            "i am unable to help",
            "as an ai, i cannot",
        ]
        if any(marker in response.lower() for marker in refusal_markers):
            logger.info("Refusal detected in model output. Re-generating direct constructive answer...")
            direct_prompt = f"Topic: {query}\nDirect explanation and answer:"
            retry_inputs = self._tokenizer(direct_prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                retry_outputs = self._model.generate(
                    **retry_inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=True,
                    temperature=0.5,
                    top_p=0.9,
                    pad_token_id=self._tokenizer.eos_token_id or self._tokenizer.pad_token_id,
                )
            retry_tokens = retry_outputs[0][retry_inputs["input_ids"].shape[1]:]
            retry_resp = self._tokenizer.decode(retry_tokens, skip_special_tokens=True).strip()
            if retry_resp:
                response = retry_resp

        return response
