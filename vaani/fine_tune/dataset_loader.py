"""Large dataset ingestion and preprocessing for Vaani AI fine-tuning."""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vaani.dataset_loader")

VAANI_DEFAULT_INSTRUCTION = (
    "You are Vaani AI (@vaaniai), an intelligent, concise, and helpful social media AI agent. "
    "Solve the user's question clearly, accurately, and politely."
)

SUPPORTED_DATASETS = {
    "dolly": "databricks/databricks-dolly-15k",
    "alpaca": "yahma/alpaca-cleaned",
}


def download_and_preprocess_dataset(
    dataset_name: str = "dolly",
    output_path: str = "data/train_large.jsonl",
    max_samples: Optional[int] = None,
    instruction_prompt: str = VAANI_DEFAULT_INSTRUCTION,
) -> int:
    """
    Download a large dataset from Hugging Face, preprocess and standardize it
    into Vaani AI instruction format, and write to JSONL.

    Args:
        dataset_name: 'dolly' or 'alpaca' or a full Hugging Face dataset identifier.
        output_path: Path to save the processed JSONL file.
        max_samples: Optional limit on the number of samples to process.
        instruction_prompt: System instruction defining Vaani AI's persona.

    Returns:
        The total number of samples written.
    """
    from datasets import load_dataset

    hf_id = SUPPORTED_DATASETS.get(dataset_name.lower(), dataset_name)
    logger.info("Loading dataset '%s' from Hugging Face Hub...", hf_id)

    dataset = load_dataset(hf_id, split="train")
    total_available = len(dataset)
    logger.info("Downloaded %d raw samples from '%s'.", total_available, hf_id)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    written_count = 0

    with open(output_file, "w", encoding="utf-8") as f:
        for item in dataset:
            query = ""
            response = ""

            # 1. Parse based on known schemas
            if "response" in item and "instruction" in item:
                # Databricks Dolly schema
                instruction = item.get("instruction", "").strip()
                context = item.get("context", "").strip()
                if context:
                    query = f"{instruction}\n\nContext: {context}"
                else:
                    query = instruction
                response = item.get("response", "").strip()

            elif "output" in item and "instruction" in item:
                # Alpaca schema
                instruction = item.get("instruction", "").strip()
                inp = item.get("input", "").strip()
                if inp:
                    query = f"{instruction}\n\nInput: {inp}"
                else:
                    query = instruction
                response = item.get("output", "").strip()

            else:
                # Generic fallback: look for question/answer or prompt/completion
                query = item.get("prompt") or item.get("question") or item.get("text") or ""
                response = item.get("completion") or item.get("answer") or ""

            # 2. Quality filters
            query = query.strip()
            response = response.strip()
            if not query or not response:
                continue

            # Filter out excessively long answers (> 2000 chars) to prioritize concise answers
            if len(response) > 2500:
                continue

            # 3. Format into standardized Vaani AI instruction sample
            record = {
                "instruction": instruction_prompt,
                "input": query,
                "output": response,
                "source": hf_id
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written_count += 1

            if max_samples and written_count >= max_samples:
                break

    logger.info(
        "Preprocessing complete! Written %d high-quality samples to '%s'.",
        written_count,
        output_path
    )
    return written_count


def inspect_dataset(file_path: str = "data/train_large.jsonl", preview_count: int = 3) -> None:
    """Print statistics and preview samples of the processed dataset."""
    path = Path(file_path)
    if not path.exists():
        logger.error("Dataset file '%s' does not exist.", file_path)
        return

    samples = []
    total = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            total += 1
            if len(samples) < preview_count:
                samples.append(json.loads(line))

    print("\n" + "=" * 60)
    print(f"Dataset Summary: {file_path}")
    print("=" * 60)
    print(f"Total Processed Samples: {total}")
    print(f"File Size:                {path.stat().st_size / (1024 * 1024):.2f} MB")
    print("-" * 60)
    print("Sample Previews:")
    for idx, s in enumerate(samples, 1):
        print(f"\n[{idx}] Input:  {s['input'][:100]}...")
        print(f"    Output: {s['output'][:120]}...")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Download and preprocess large datasets from Hugging Face for Vaani AI.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="dolly",
        choices=["dolly", "alpaca"],
        help="Dataset to download: 'dolly' (15k samples) or 'alpaca' (52k samples)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/train_large.jsonl",
        help="Target output JSONL path"
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Maximum samples to process (default: all)"
    )
    args = parser.parse_args()

    download_and_preprocess_dataset(
        dataset_name=args.dataset,
        output_path=args.output,
        max_samples=args.max_samples,
    )
    inspect_dataset(args.output)


if __name__ == "__main__":
    main()
