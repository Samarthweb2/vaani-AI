"""Twitter mentions poller service."""

import time
import logging
from typing import Callable, Optional
from vaani.twitter.client import TwitterClient
from vaani.storage import MentionStorage

logger = logging.getLogger(__name__)


class TwitterPoller:
    """Periodically queries Twitter API v2 for new @mentions."""

    def __init__(
        self,
        twitter_client: TwitterClient,
        storage: MentionStorage,
        interval_seconds: int = 30,
    ):
        self.client = twitter_client
        self.storage = storage
        self.interval_seconds = max(10, interval_seconds)
        self._running = False

    def poll_once(self, on_mention_callback: Callable[[dict], None]) -> int:
        """
        Poll mentions once and execute callback on unhandled mentions.
        Returns the count of newly handled mentions.
        """
        since_id = self.storage.get_last_since_id()
        logger.debug("Polling mentions with since_id=%s", since_id)

        try:
            mentions = self.client.get_mentions(since_id=since_id)
        except Exception as e:
            logger.error("Error polling mentions from Twitter API: %s", e)
            return 0

        if not mentions:
            return 0

        # Twitter API returns mentions from newest to oldest. Reverse to handle chronologically.
        mentions.reverse()
        processed_count = 0
        latest_id = since_id

        # Get bot's own user ID to prevent replying to itself
        try:
            bot_info = self.client.get_me()
            bot_user_id = bot_info.get("id")
        except Exception:
            bot_user_id = None

        for mention in mentions:
            m_id = mention["id"]
            author_id = mention.get("author_id")

            # Skip if authored by the bot itself
            if bot_user_id and author_id == bot_user_id:
                continue

            # Skip if already processed in SQLite
            if self.storage.is_processed(m_id):
                continue

            try:
                on_mention_callback(mention)
                processed_count += 1
            except Exception as e:
                logger.error("Failed to handle mention %s: %s", m_id, e)

            latest_id = m_id

        if latest_id:
            self.storage.set_last_since_id(latest_id)

        return processed_count

    def start_polling(self, on_mention_callback: Callable[[dict], None]) -> None:
        """Loop polling indefinitely."""
        self._running = True
        logger.info("Starting mention poller (interval: %ds)...", self.interval_seconds)

        while self._running:
            try:
                count = self.poll_once(on_mention_callback)
                if count > 0:
                    logger.info("Successfully handled %d new mention(s).", count)
            except Exception as e:
                logger.error("Unexpected error in poll loop: %s", e)

            time.sleep(self.interval_seconds)

    def stop(self) -> None:
        """Stop polling loop."""
        self._running = False
