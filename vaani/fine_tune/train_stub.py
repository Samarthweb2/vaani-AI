"""
Fine-tuning script for Vaani AI using Hugging Face trl (SFTTrainer) and PEFT (LoRA).

Usage:
    python -m vaani.fine_tune.train_stub \
        --model_id Qwen/Qwen2.5-0.5B-Instruct \
        --dataset_path data/dataset.jsonl \
        --output_dir checkpoints/vaani-lora \
        --epochs 3
"""

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Vaani AI on collected mention interactions.")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-0.5B-Instruct", help="Base Hugging Face model ID")
    parser.add_argument("--dataset_path", type=str, default="data/dataset.jsonl", help="Path to instruction dataset JSONL")
    parser.add_argument("--output_dir", type=str, default="checkpoints/vaani-lora", help="Output directory for LoRA adapter")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Per-device train batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    args = parser.parse_args()

    dataset_file = Path(args.dataset_path)
    if not dataset_file.exists() or dataset_file.stat().st_size == 0:
        logger.error(
            "Dataset file '%s' does not exist or is empty. "
            "Interact with Vaani AI via simulator or live bot first to accumulate training examples!",
            args.dataset_path
        )
        return

    logger.info("Initializing Fine-Tuning pipeline...")
    logger.info("Base Model: %s", args.model_id)
    logger.info("Dataset: %s", args.dataset_path)
    logger.info("Output Directory: %s", args.output_dir)

    try:
        import torch
        from datasets import load_dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from peft import LoraConfig, get_peft_model
        from trl import SFTTrainer
    except ImportError:
        logger.error(
            "Required fine-tuning libraries are not installed. "
            "Please run: pip install trl datasets"
        )
        return

    # 1. Load Dataset
    logger.info("Loading training data from %s...", args.dataset_path)
    dataset = load_dataset("json", data_files=args.dataset_path, split="train")
    logger.info("Loaded %d training samples.", len(dataset))

    # 2. Load Tokenizer & Model
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device_map = "auto" if torch.cuda.is_available() else None
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map=device_map,
        trust_remote_code=True,
    )

    # 3. Configure LoRA (Parameter Efficient Fine-Tuning)
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    # 4. Training Arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        logging_steps=10,
        save_strategy="epoch",
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    # 5. Format prompt function
    def formatting_prompts_func(example):
        output_texts = []
        for i in range(len(example["instruction"])):
            instruction = example["instruction"][i]
            user_input = example["input"][i]
            response = example["output"][i]
            text = (
                f"<|im_start|>system\n{instruction}<|im_end|>\n"
                f"<|im_start|>user\n{user_input}<|im_end|>\n"
                f"<|im_start|>assistant\n{response}<|im_end|>"
            )
            output_texts.append(text)
        return output_texts

    # 6. SFT Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        formatting_func=formatting_prompts_func,
        tokenizer=tokenizer,
        args=training_args,
        max_seq_length=512,
    )

    logger.info("Starting model fine-tuning...")
    trainer.train()

    # 7. Save LoRA Adapter
    logger.info("Saving fine-tuned adapter to %s...", args.output_dir)
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    logger.info("Fine-tuning complete! Set HF_LORA_PATH=%s in your .env to use the new weights.", args.output_dir)


if __name__ == "__main__":
    main()
