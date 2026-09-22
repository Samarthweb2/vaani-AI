"""Dataset collector for logging user mentions and responses for future fine-tuning."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List


class DatasetCollector:
    """
    Logs queries and responses into instruction fine-tuning datasets
    (standard Alpaca / ShareGPT JSONL format) for future model fine-tuning.
    """

    def __init__(self, dataset_path: str = "data/dataset.jsonl"):
        self.dataset_path = Path(dataset_path)
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)

    def log_interaction(
        self,
        query: str,
        response: str,
        author: str = "user",
        source: str = "social_mention",
        instruction: Optional[str] = None
    ) -> None:
        """
        Append a single instruction-tuning sample into dataset.jsonl.
        """
        default_instruction = (
            "You are Vaani AI (@vaaniai), an intelligent, concise, and polite social media assistant. "
            "Solve the user's question clearly and accurately within tweet limits."
        )

        entry = {
            "instruction": instruction or default_instruction,
            "input": query.strip(),
            "output": response.strip(),
            "author": author,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        with open(self.dataset_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def count_samples(self) -> int:
        """Return the number of recorded training samples."""
        if not self.dataset_path.exists():
            return 0
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def get_samples(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read recorded training samples."""
        if not self.dataset_path.exists():
            return []
        samples = []
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
                if limit and len(samples) >= limit:
                    break
        return samples
