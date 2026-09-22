import json
import pytest
from pathlib import Path
from vaani.dataset_collector import DatasetCollector


def test_dataset_collector_logging(tmp_path):
    dataset_file = tmp_path / "test_dataset.jsonl"
    collector = DatasetCollector(str(dataset_file))

    assert collector.count_samples() == 0
    assert collector.get_samples() == []

    # Log first interaction
    collector.log_interaction(
        query="Explain supervised learning",
        response="Supervised learning trains models on labeled input-output pairs.",
        author="alice",
        source="twitter_mention"
    )

    assert collector.count_samples() == 1
    samples = collector.get_samples()
    assert len(samples) == 1
    assert samples[0]["input"] == "Explain supervised learning"
    assert "Supervised learning trains" in samples[0]["output"]
    assert samples[0]["author"] == "alice"
    assert "instruction" in samples[0]

    # Log second interaction
    collector.log_interaction(
        query="What is a neural network?",
        response="A network of connected artificial neurons that learns representations.",
        author="bob",
        source="cli_simulator"
    )

    assert collector.count_samples() == 2
