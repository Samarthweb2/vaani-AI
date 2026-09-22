"""Twitter API v2 Client wrapper using Tweepy."""

import logging
from typing import Optional, List, Dict, Any
from vaani.twitter.formatter import format_tweet_chunks

logger = logging.getLogger(__name__)


class TwitterClient:
    """Wrapper around Tweepy Client for reading mentions and posting replies."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.bearer_token = bearer_token

        self._client = None
        self._bot_user = None

    def is_configured(self) -> bool:
        """Check whether minimum Twitter credentials are provided."""
        has_oauth1 = bool(self.api_key and self.api_secret and self.access_token and self.access_secret)
        has_bearer = bool(self.bearer_token)
        return has_oauth1 or has_bearer

    def _get_client(self):
        if self._client is None:
            import tweepy

            if not self.is_configured():
                raise ValueError(
                    "Twitter credentials are not configured. Please set TWITTER_API_KEY, "
                    "TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET in your .env file."
                )

            self._client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
                wait_on_rate_limit=True,
            )
        return self._client

    def get_me(self) -> Dict[str, Any]:
        """Fetch the authenticated bot user details."""
        if self._bot_user is None:
            client = self._get_client()
            resp = client.get_me(user_fields=["id", "username", "name"])
            if resp.data:
                self._bot_user = {"id": str(resp.data.id), "username": resp.data.username, "name": resp.data.name}
            else:
                raise RuntimeError("Could not retrieve authenticated Twitter user profile.")
        return self._bot_user

    def get_mentions(
        self,
        since_id: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent tweets mentioning the bot.
        """
        client = self._get_client()
        bot_user = self.get_me()
        user_id = bot_user["id"]

        kwargs = {
            "id": user_id,
            "max_results": max(5, min(max_results, 100)),
            "expansions": ["author_id"],
            "tweet_fields": ["created_at", "conversation_id", "in_reply_to_user_id", "text"],
            "user_fields": ["username"],
        }
        if since_id:
            kwargs["since_id"] = since_id

        response = client.get_users_mentions(**kwargs)
        if not response or not response.data:
            return []

        # Map author_id to username
        users_by_id = {}
        if response.includes and "users" in response.includes:
            for u in response.includes["users"]:
                users_by_id[str(u.id)] = u.username

        mentions = []
        for tweet in response.data:
            author_id = str(tweet.author_id)
            username = users_by_id.get(author_id, "unknown")
            mentions.append({
                "id": str(tweet.id),
                "author_id": author_id,
                "author_username": username,
                "text": tweet.text,
                "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
            })

        return mentions

    def reply_to_tweet(
        self,
        tweet_id: str,
        response_text: str
    ) -> List[str]:
        """
        Post a reply to a tweet. If the response exceeds 280 chars,
        it posts sequential threaded replies.
        """
        client = self._get_client()
        chunks = format_tweet_chunks(response_text)
        created_ids = []
        reply_to_id = tweet_id

        for chunk in chunks:
            resp = client.create_tweet(
                text=chunk,
                in_reply_to_tweet_id=reply_to_id
            )
            if resp.data:
                new_id = str(resp.data["id"])
                created_ids.append(new_id)
                reply_to_id = new_id  # Thread subsequent replies under the previous tweet
                logger.info("Posted reply tweet %s in response to %s", new_id, tweet_id)

        return created_ids
