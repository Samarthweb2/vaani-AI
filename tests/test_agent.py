import pytest
from pathlib import Path
from vaani.agent import VaaniAgent
from vaani.config import Settings
from vaani.storage import MentionStorage
from vaani.dataset_collector import DatasetCollector
from vaani.llm.mock import MockLLMProvider


def test_agent_solve_mention_query(tmp_path):
    settings = Settings(
        bot_handle="vaaniai",
        database_path=str(tmp_path / "test.db"),
        dataset_path=str(tmp_path / "dataset.jsonl"),
        hf_mode="mock"
    )

    storage = MentionStorage(settings.database_path)
    dataset_collector = DatasetCollector(settings.dataset_path)
    llm = MockLLMProvider()

    from vaani.twitter.client import TwitterClient
    agent = VaaniAgent(
        settings=settings,
        llm_provider=llm,
        storage=storage,
        dataset_collector=dataset_collector,
        twitter_client=TwitterClient()
    )

    # 1. Test query solving
    response, chunks = agent.solve_mention_query(
        raw_text="@vaaniai how do I fine-tune a model?",
        author="developer"
    )

    assert "fine-tuning" in response.lower() or "vaani" in response.lower()
    assert len(chunks) >= 1
    assert dataset_collector.count_samples() == 1

    # 2. Test handling tweet mention through agent
    mention = {
        "id": "tweet_1001",
        "author_id": "author_555",
        "author_username": "developer",
        "text": "@vaaniai what is AI?",
        "created_at": "2026-09-22T10:00:00Z"
    }

    # First handle
    assert not storage.is_processed("tweet_1001")
    agent.handle_twitter_mention(mention)
    assert storage.is_processed("tweet_1001")
    assert dataset_collector.count_samples() == 2

    # Second handle (duplicate protection)
    agent.handle_twitter_mention(mention)
    # Should not re-add to dataset because it was skipped
    assert dataset_collector.count_samples() == 2


def test_agent_tool_calling(tmp_path):
    settings = Settings(
        bot_handle="vaaniai",
        database_path=str(tmp_path / "test_tools.db"),
        dataset_path=str(tmp_path / "dataset_tools.jsonl"),
        hf_mode="mock"
    )

    storage = MentionStorage(settings.database_path)
    dataset_collector = DatasetCollector(settings.dataset_path)
    llm = MockLLMProvider()

    from vaani.twitter.client import TwitterClient
    agent = VaaniAgent(
        settings=settings,
        llm_provider=llm,
        storage=storage,
        dataset_collector=dataset_collector,
        twitter_client=TwitterClient()
    )

    # 1. Calculator Tool Call
    resp, chunks, tools = agent.solve_mention_query(
        raw_text="@vaaniai calculate 125 * 84",
        author="mathematician",
        return_tools=True
    )
    assert len(tools) == 1
    assert tools[0]["name"] == "calculator"
    assert "10500" in tools[0]["output"]
    assert "10500" in resp

    # 2. Python Runner Tool Call
    resp_py, chunks_py, tools_py = agent.solve_mention_query(
        raw_text="@vaaniai run python: print(2**10)",
        author="coder",
        return_tools=True
    )
    assert len(tools_py) == 1
    assert tools_py[0]["name"] == "python_runner"
    assert "1024" in tools_py[0]["output"]

    # 3. Web Search Tool Call
    resp_search, chunks_search, tools_search = agent.solve_mention_query(
        raw_text="@vaaniai who is Guido van Rossum?",
        author="researcher",
        return_tools=True
    )
    assert len(tools_search) == 1
    assert tools_search[0]["name"] == "web_search"
    assert "Python" in tools_search[0]["output"]

