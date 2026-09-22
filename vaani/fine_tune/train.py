"""
Production-grade LoRA fine-tuning engine for Vaani AI using Hugging Face trl (SFTTrainer) and PEFT.

Usage:
    python -m vaani.fine_tune.train \
        --model_id Qwen/Qwen2.5-0.5B-Instruct \
        --dataset_path data/train_large.jsonl \
        --output_dir checkpoints/vaani-lora \
        --epochs 1 \
        --batch_size 2
"""

import argparse
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vaani.train")


def run_training(
    model_id: str = "Qwen/Qwen2.5-0.5B-Instruct",
    dataset_path: str = "data/train_large.jsonl",
    output_dir: str = "checkpoints/vaani-lora",
    epochs: int = 1,
    batch_size: int = 1,
    grad_accum: int = 1,
    learning_rate: float = 2e-4,
    lora_r: int = 4,
    lora_alpha: int = 8,
    max_seq_length: int = 128,
    max_samples: int = None,
    max_steps: int = None,
) -> str:
    """
    Run LoRA fine-tuning on the specified dataset.

    Returns:
        The output path where the fine-tuned adapter is saved.
    """
    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from peft import LoraConfig, TaskType
    from trl import SFTTrainer

    dataset_file = Path(dataset_path)
    if not dataset_file.exists() or dataset_file.stat().st_size == 0:
        raise FileNotFoundError(
            f"Dataset file '{dataset_path}' not found or empty. "
            "Run 'python -m vaani.fine_tune.dataset_loader' first to download the dataset!"
        )

    logger.info("=" * 60)
    logger.info("        Vaani AI - Fine-Tuning Pipeline (LoRA)")
    logger.info("=" * 60)
    logger.info("Base Model:       %s", model_id)
    logger.info("Dataset:          %s", dataset_path)
    logger.info("Output Directory: %s", output_dir)
    logger.info("Epochs:           %d", epochs)
    logger.info("Batch Size:       %d (effective: %d)", batch_size, batch_size * grad_accum)
    logger.info("Learning Rate:    %s", learning_rate)
    logger.info("LoRA Rank (r):    %d, Alpha: %d", lora_r, lora_alpha)
    logger.info("Device:           %s", "cuda" if torch.cuda.is_available() else "cpu")
    logger.info("=" * 60)

    # 1. Load Dataset
    logger.info("Loading training data from %s...", dataset_path)
    raw_dataset = load_dataset("json", data_files=dataset_path, split="train")
    if max_samples and max_samples < len(raw_dataset):
        raw_dataset = raw_dataset.select(range(max_samples))
    logger.info("Loaded %d samples for training.", len(raw_dataset))

    # 2. Load Tokenizer & Model
    logger.info("Loading tokenizer for %s...", model_id)
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device_map = "auto" if torch.cuda.is_available() else None
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    logger.info("Loading base model weights (%s)...", torch_dtype)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        device_map=device_map,
        trust_remote_code=True,
    )

    # 3. Configure LoRA (targeted for efficiency on CPU and GPU)
    peft_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=["q_proj", "v_proj"],
    )

    # 4. Format dataset into ChatML prompts
    logger.info("Formatting dataset into ChatML instruction prompts...")
    def format_chat(sample):
        return {
            "text": (
                f"<|im_start|>system\n{sample['instruction']}<|im_end|>\n"
                f"<|im_start|>user\n{sample['input']}<|im_end|>\n"
                f"<|im_start|>assistant\n{sample['output']}<|im_end|>"
            )
        }

    formatted_dataset = raw_dataset.map(format_chat)

    # 5. Training Arguments & SFTTrainer
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    import inspect
    from trl import SFTConfig

    sft_params = inspect.signature(SFTConfig.__init__).parameters
    config_kwargs = {
        "output_dir": output_dir,
        "num_train_epochs": epochs,
        "per_device_train_batch_size": batch_size,
        "gradient_accumulation_steps": grad_accum,
        "learning_rate": learning_rate,
        "logging_steps": 1,
        "save_strategy": "no",
        "use_cpu": not torch.cuda.is_available(),
        "report_to": "none",
    }
    if max_steps:
        config_kwargs["max_steps"] = max_steps
    if "dataset_text_field" in sft_params:
        config_kwargs["dataset_text_field"] = "text"
    if "max_length" in sft_params:
        config_kwargs["max_length"] = max_seq_length
    elif "max_seq_length" in sft_params:
        config_kwargs["max_seq_length"] = max_seq_length

    training_args = SFTConfig(**config_kwargs)

    trainer_kwargs = {
        "model": model,
        "train_dataset": formatted_dataset,
        "peft_config": peft_config,
        "args": training_args,
    }
    trainer_params = inspect.signature(SFTTrainer.__init__).parameters
    if "dataset_text_field" in trainer_params:
        trainer_kwargs["dataset_text_field"] = "text"
    if "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    else:
        trainer_kwargs["tokenizer"] = tokenizer

    trainer = SFTTrainer(**trainer_kwargs)

    logger.info("Starting training loop...")
    trainer.train()

    # 7. Save adapter and tokenizer
    logger.info("Training complete! Saving LoRA adapter to %s...", output_dir)
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    logger.info("=" * 60)
    logger.info("FINE-TUNING SUCCEEDED! 🎉")
    logger.info("Adapter saved at: %s", output_dir)
    logger.info("To activate this model in Vaani AI, add this to your .env:")
    logger.info("    HF_MODE=local")
    logger.info("    HF_LORA_PATH=%s", output_dir)
    logger.info("=" * 60)

    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Vaani AI using LoRA on large datasets.")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-0.5B-Instruct", help="Base Hugging Face model")
    parser.add_argument("--dataset_path", type=str, default="data/train_large.jsonl", help="Preprocessed JSONL dataset")
    parser.add_argument("--output_dir", type=str, default="checkpoints/vaani-lora", help="Output directory")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--lora_r", type=int, default=8, help="LoRA rank")
    parser.add_argument("--max_samples", type=int, default=None, help="Limit number of samples for training")
    args = parser.parse_args()

    run_training(
        model_id=args.model_id,
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        learning_rate=args.lr,
        lora_r=args.lora_r,
        max_samples=args.max_samples,
    )


if __name__ == "__main__":
    main()
