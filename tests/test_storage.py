import pytest
from pathlib import Path
from vaani.storage import MentionStorage


def test_mention_storage_lifecycle(tmp_path):
    db_file = tmp_path / "test_vaani.db"
    storage = MentionStorage(str(db_file))

    # Initially tweet is not processed
    assert not storage.is_processed("12345")

    # Record a mention
    storage.record_mention(
        tweet_id="12345",
        author_id="999",
        author_username="testuser",
        query_text="@vaaniai how does AI work?",
        response_text="AI works by learning patterns from data.",
        reply_tweet_id="67890"
    )

    # Now it should be marked as processed
    assert storage.is_processed("12345")
    assert not storage.is_processed("99999")

    # Check history
    history = storage.get_recent_history(limit=5)
    assert len(history) == 1
    assert history[0]["tweet_id"] == "12345"
    assert history[0]["author_username"] == "testuser"
    assert history[0]["reply_tweet_id"] == "67890"

    # Test since_id cursor
    assert storage.get_last_since_id() is None
    storage.set_last_since_id("12345")
    assert storage.get_last_since_id() == "12345"
