"""Main entry point for Vaani AI."""

import argparse
import logging
import sys
from vaani.config import get_settings
from vaani.agent import VaaniAgent
from vaani.simulator import run_simulator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vaani")


def main():
    parser = argparse.ArgumentParser(description="Vaani AI - Social Media Mention Agent")
    parser.add_argument(
        "--mode",
        choices=["simulate", "live", "test-hf", "stats", "download-data", "train"],
        default="simulate",
        help="Execution mode: simulate, live, test-hf, stats, download-data, or train"
    )
    parser.add_argument("--dataset", type=str, default="dolly", choices=["dolly", "alpaca"], help="Dataset to download")
    parser.add_argument("--max-samples", type=int, default=None, help="Max samples for downloading or training")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for training")
    parser.add_argument("--max-steps", type=int, default=None, help="Max steps for training")
    args = parser.parse_args()

    settings = get_settings()
    agent = VaaniAgent(settings=settings)

    if args.mode == "simulate":
        run_simulator(agent)

    elif args.mode == "live":
        print(f"Starting Vaani AI in LIVE mode for @{settings.bot_handle}...")
        try:
            agent.run_live()
        except KeyboardInterrupt:
            print("\nShutting down Vaani AI live bot.")
        except Exception as e:
            logger.error("Failed to run live bot: %s", e)
            sys.exit(1)

    elif args.mode == "test-hf":
        test_query = f"@{settings.bot_handle} What is the significance of fine-tuning language models?"
        print(f"Testing Hugging Face engine with mode='{settings.hf_mode}', model='{settings.hf_model_id}'...")
        print(f"Input: {test_query}\n")
        response, chunks = agent.solve_mention_query(test_query, author="test_user")
        print("Generated Response:")
        print(response)
        print("\nFormatted Tweet Chunks:")
        for idx, chunk in enumerate(chunks, 1):
            print(f"  [{idx}/{len(chunks)} ({len(chunk)} chars)]: {chunk}")

    elif args.mode == "stats":
        total_samples = agent.dataset_collector.count_samples()
        history = agent.storage.get_recent_history(limit=5)
        print("=" * 50)
        print("           Vaani AI Status & Stats")
        print("=" * 50)
        print(f"Bot Handle:            @{settings.bot_handle}")
        print(f"Hugging Face Mode:     {settings.hf_mode}")
        print(f"Hugging Face Model:    {settings.hf_model_id}")
        print(f"Database Path:         {settings.database_path}")
        print(f"Fine-Tuning Dataset:   {settings.dataset_path}")
        print(f"Total Logged Samples:  {total_samples}")
        print("=" * 50)
        if history:
            print("\nRecent Processed Mentions:")
            for item in history:
                print(f"- [{item['processed_at']}] Query: '{item['query_text']}'")
        else:
            print("\nNo mentions processed yet.")

    elif args.mode == "download-data":
        from vaani.fine_tune.dataset_loader import download_and_preprocess_dataset, inspect_dataset
        output_file = "data/train_large.jsonl"
        print(f"Downloading large dataset '{args.dataset}' from Hugging Face Hub...")
        count = download_and_preprocess_dataset(
            dataset_name=args.dataset,
            output_path=output_file,
            max_samples=args.max_samples
        )
        inspect_dataset(output_file)

    elif args.mode == "train":
        from vaani.fine_tune.train import run_training
        dataset_file = "data/train_large.jsonl"
        print(f"Starting LoRA fine-tuning on {dataset_file}...")
        run_training(
            model_id=settings.hf_model_id,
            dataset_path=dataset_file,
            output_dir="checkpoints/vaani-lora",
            epochs=args.epochs,
            batch_size=args.batch_size,
            max_samples=args.max_samples,
            max_steps=args.max_steps
        )


if __name__ == "__main__":
    main()
