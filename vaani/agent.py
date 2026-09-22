"""Central agent orchestrator for Vaani AI."""

import logging
from typing import Optional, Dict, Any, List, Tuple
from vaani.config import Settings, get_settings
from vaani.storage import MentionStorage
from vaani.dataset_collector import DatasetCollector
from vaani.llm import create_llm_provider, BaseLLMProvider
from vaani.twitter.formatter import clean_query, format_tweet_chunks
from vaani.twitter.client import TwitterClient
from vaani.twitter.poller import TwitterPoller

from vaani.tools import ToolRegistry, default_registry

logger = logging.getLogger(__name__)


class VaaniAgent:
    """
    Vaani AI Agent:
    - Ingests mentions tagging @vaaniai
    - Evaluates and calls autonomous tools (calculator, web search, python runner)
    - Solves the query using Hugging Face LLM augmented with tool observations
    - Formats the response for Twitter/Social media
    - Records the interaction into fine-tuning dataset
    - Stores state in SQLite to prevent duplicate processing
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        storage: Optional[MentionStorage] = None,
        dataset_collector: Optional[DatasetCollector] = None,
        twitter_client: Optional[TwitterClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.settings = settings or get_settings()
        self.storage = storage or MentionStorage(self.settings.database_path)
        self.dataset_collector = dataset_collector or DatasetCollector(self.settings.dataset_path)
        self.llm = llm_provider or create_llm_provider(self.settings)
        self.tool_registry = tool_registry or default_registry
        self.last_used_tools: List[Dict[str, Any]] = []

        self.twitter_client = twitter_client or TwitterClient(
            api_key=self.settings.twitter_api_key,
            api_secret=self.settings.twitter_api_secret,
            access_token=self.settings.twitter_access_token,
            access_secret=self.settings.twitter_access_secret,
            bearer_token=self.settings.twitter_bearer_token,
        )

    def solve_mention_query(
        self,
        raw_text: str,
        author: str = "user",
        context: Optional[str] = None,
        source: str = "social_mention",
        return_tools: bool = False
    ) -> Any:
        """
        Process a raw mention string:
        1. Clean and strip '@vaaniai' from the input text
        2. Check and invoke relevant tools (Calculator, Web Search, Python Runner)
        3. Invoke Hugging Face LLM (augmented with tool observations)
        4. Format response into tweet-compatible chunks (<= 280 chars)
        5. Log sample to training dataset (JSONL) for future fine-tuning

        Returns:
            Tuple of (full_response_text, list_of_tweet_chunks)
            or (full_response_text, list_of_tweet_chunks, used_tools) if return_tools=True
        """
        cleaned = clean_query(raw_text, bot_handle=self.settings.bot_handle)
        if not cleaned:
            cleaned = "Hello! What can I help you with?"

        logger.info("Solving query from @%s: '%s'", author, cleaned)

        # 2. Autonomous Tool Calling
        used_tools = []
        tool_observation = None
        tool_result = self.tool_registry.execute_matching_tool(cleaned)
        if tool_result:
            logger.info("Tool %s executed: %s", tool_result.tool_name, tool_result.output_data)
            tool_dict = {
                "name": tool_result.tool_name,
                "input": tool_result.input_data,
                "output": tool_result.output_data,
                "success": tool_result.success
            }
            used_tools.append(tool_dict)
            tool_observation = tool_result.output_data

        self.last_used_tools = used_tools

        # 3. Invoke Hugging Face model with tool observation
        full_response = self.llm.generate_response(
            query=cleaned,
            author=author,
            context=context,
            tool_observation=tool_observation
        )

        # 4. Format response chunks
        chunks = format_tweet_chunks(full_response)

        # 5. Save to fine-tuning dataset
        try:
            self.dataset_collector.log_interaction(
                query=cleaned,
                response=full_response,
                author=author,
                source=source
            )
            logger.debug("Logged interaction to dataset. Total samples: %d", self.dataset_collector.count_samples())
        except Exception as e:
            logger.warning("Failed to log interaction to dataset: %s", e)

        if return_tools:
            return full_response, chunks, used_tools

        return full_response, chunks

    def handle_twitter_mention(self, mention: Dict[str, Any]) -> None:
        """
        Handle a live mention received from Twitter API.
        """
        tweet_id = str(mention["id"])
        author_username = mention.get("author_username", "user")
        author_id = str(mention.get("author_id", "0"))
        raw_text = mention.get("text", "")
        created_at = mention.get("created_at")

        if self.storage.is_processed(tweet_id):
            logger.info("Tweet %s already handled. Skipping.", tweet_id)
            return

        full_response, chunks = self.solve_mention_query(
            raw_text=raw_text,
            author=author_username,
            source="twitter_mention"
        )

        # Post reply to Twitter
        reply_ids = []
        if self.twitter_client.is_configured():
            try:
                reply_ids = self.twitter_client.reply_to_tweet(
                    tweet_id=tweet_id,
                    response_text=full_response
                )
                logger.info("Successfully posted reply to tweet %s: %s", tweet_id, reply_ids)
            except Exception as e:
                logger.error("Failed to post tweet reply: %s", e)
                raise
        else:
            logger.warning("Twitter client is not configured. Reply was generated but not tweeted.")

        # Record in SQLite to prevent reprocessing
        primary_reply_id = reply_ids[0] if reply_ids else None
        self.storage.record_mention(
            tweet_id=tweet_id,
            author_id=author_id,
            author_username=author_username,
            query_text=raw_text,
            response_text=full_response,
            reply_tweet_id=primary_reply_id,
            created_at=created_at
        )

    def run_live(self) -> None:
        """Run the live Twitter bot poller loop."""
        if not self.twitter_client.is_configured():
            raise ValueError(
                "Cannot run in live mode: Twitter credentials are not configured. "
                "Please configure your .env file with TWITTER_API_KEY, TWITTER_API_SECRET, "
                "TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_SECRET."
            )

        poller = TwitterPoller(
            twitter_client=self.twitter_client,
            storage=self.storage,
            interval_seconds=self.settings.poll_interval_seconds
        )

        logger.info("Vaani AI is active and monitoring mentions for @%s", self.settings.bot_handle)
        poller.start_polling(self.handle_twitter_mention)
