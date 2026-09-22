"""Parser and processor for the TWCS (Twitter Customer Support) dataset.

Extracts real Twitter user queries and assistant reply pairs, cleans handles and
sign-offs, filters out DM referrals, and formats into Alpaca/ShareGPT instruction format.
"""

import csv
import json
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("vaani.twcs_parser")

VAANI_INSTRUCTION = (
    "You are Vaani AI (@vaaniai), an intelligent, concise, and helpful social media AI agent. "
    "Solve the user's question clearly, accurately, and politely within tweet limits."
)

EXCLUDED_PHRASES = [
    "dm us",
    "send us a dm",
    "direct message",
    "please dm",
    "follow and dm",
    "send a private message",
    "reach out in dm",
]


def clean_tweet_text(text: str) -> str:
    """Clean tweet text: remove handles, URLs, and employee sign-offs."""
    # Remove mentions (@username)
    text = re.sub(r'@[A-Za-z0-9_]+', '', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove employee signature codes (e.g. ^JK, ^AB, ^HSB)
    text = re.sub(r'\^[A-Z]{2,4}\b', '', text)
    # Normalize whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_twcs_dataset(
    csv_path: str = "twcs.csv",
    output_path: str = "data/train_twitter.jsonl",
    max_rows: Optional[int] = 100000,
    target_pairs: int = 5000,
) -> int:
    """
    Parse twcs.csv and generate high-quality Twitter instruction tuning pairs.
    """
    path = Path(csv_path)
    if not path.exists():
        logger.error("Dataset file '%s' not found.", csv_path)
        return 0

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Parsing TWCS dataset from '%s' (max_rows: %s)...", csv_path, max_rows)

    inbound_by_id: Dict[str, str] = {}
    written_count = 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f, \
         open(out_file, "w", encoding="utf-8") as out:

        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if max_rows and idx >= max_rows:
                break

            tweet_id = row.get("tweet_id", "").strip()
            inbound = row.get("inbound", "").strip().lower() == "true"
            text = row.get("text", "").strip()
            in_response_to = row.get("in_response_to_tweet_id", "").strip()

            if inbound:
                # Store user's incoming question
                inbound_by_id[tweet_id] = text
            else:
                # Company/assistant reply
                if in_response_to and in_response_to in inbound_by_id:
                    orig_question = inbound_by_id[in_response_to]
                    orig_reply = text

                    clean_q = clean_tweet_text(orig_question)
                    clean_a = clean_tweet_text(orig_reply)

                    # Quality filters
                    if len(clean_q) < 20 or len(clean_a) < 25:
                        continue
                    if len(clean_a) > 280:
                        continue
                    if any(phrase in clean_a.lower() for phrase in EXCLUDED_PHRASES):
                        continue

                    # Standardize into instruction format
                    sample = {
                        "instruction": VAANI_INSTRUCTION,
                        "input": clean_q,
                        "output": clean_a,
                        "source": "twcs_twitter_dataset"
                    }

                    out.write(json.dumps(sample, ensure_ascii=False) + "\n")
                    written_count += 1

                    if target_pairs and written_count >= target_pairs:
                        break

    logger.info("Successfully extracted %d clean Twitter Q&A pairs to '%s'.", written_count, output_path)
    return written_count


def merge_datasets(
    dolly_path: str = "data/train_large.jsonl",
    twitter_path: str = "data/train_twitter.jsonl",
    output_path: str = "data/train_combined.jsonl",
    max_dolly: int = 5000,
    max_twitter: int = 5000,
) -> int:
    """Merge Databricks Dolly 15k knowledge with Twitter conversational data."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with open(out_file, "w", encoding="utf-8") as out:
        # 1. Add Dolly samples (knowledge base)
        d_path = Path(dolly_path)
        if d_path.exists():
            d_count = 0
            with open(d_path, "r", encoding="utf-8") as f:
                for line in f:
                    out.write(line)
                    total += 1
                    d_count += 1
                    if max_dolly and d_count >= max_dolly:
                        break
            logger.info("Included %d samples from '%s'.", d_count, dolly_path)

        # 2. Add Twitter samples (social tone & conciseness)
        t_path = Path(twitter_path)
        if t_path.exists():
            t_count = 0
            with open(t_path, "r", encoding="utf-8") as f:
                for line in f:
                    out.write(line)
                    total += 1
                    t_count += 1
                    if max_twitter and t_count >= max_twitter:
                        break
            logger.info("Included %d samples from '%s'.", t_count, twitter_path)

    logger.info("Combined dataset created at '%s' with %d total samples.", output_path, total)
    return total


if __name__ == "__main__":
    parse_twcs_dataset(csv_path="twcs.csv", output_path="data/train_twitter.jsonl", max_rows=150000, target_pairs=5000)
    merge_datasets()
