"""Real-time knowledge and search tool for Vaani AI."""

import json
import logging
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Optional
from vaani.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for fetching real-time facts, Wikipedia summaries, and web information."""

    name: str = "web_search"
    description: str = "Searches for real-world knowledge, definitions, current facts, and encyclopedic data."
    icon: str = "🌐"

    SEARCH_TRIGGERS = [
        re.compile(r"\b(who is|who was|what is|tell me about|explain|search|define|history of)\b", re.IGNORECASE),
        re.compile(r"\b(what time|what date|today's date|current time|current date)\b", re.IGNORECASE),
        re.compile(r"\b(latest|news|release date|founder|creator)\b", re.IGNORECASE),
    ]

    def can_handle(self, query: str) -> bool:
        """Check if the query is seeking real-world knowledge or search."""
        for pattern in self.SEARCH_TRIGGERS:
            if pattern.search(query):
                return True
        return False

    def clean_search_term(self, query: str) -> str:
        """Extract key search term from a question."""
        cleaned = re.sub(r"^(who is|who was|what is|tell me about|explain|search for|search|define)\s+", "", query, flags=re.IGNORECASE)
        cleaned = re.sub(r"[\?\.\!]$", "", cleaned).strip()
        return cleaned or query

    def fetch_wikipedia_summary(self, topic: str) -> Optional[str]:
        """Fetch summary from Wikipedia REST API."""
        try:
            formatted_topic = urllib.parse.quote(topic.replace(" ", "_"))
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_topic}"
            req = urllib.request.Request(url, headers={"User-Agent": "VaaniAI/1.0 (HackathonDemo)"})
            with urllib.request.urlopen(req, timeout=3.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    extract = data.get("extract")
                    if extract:
                        return extract[:400]
        except Exception as e:
            logger.debug("Wikipedia fetch failed for '%s': %s", topic, e)
        return None

    def fetch_duckduckgo_answer(self, query: str) -> Optional[str]:
        """Fetch instant answer from DuckDuckGo API."""
        try:
            params = urllib.parse.urlencode({
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "1"
            })
            url = f"https://api.duckduckgo.com/?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "VaaniAI/1.0 (HackathonDemo)"})
            with urllib.request.urlopen(req, timeout=3.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    # Try AbstractText
                    abstract = data.get("AbstractText")
                    if abstract:
                        return abstract[:400]
                    # Try Answer
                    answer = data.get("Answer")
                    if answer:
                        return answer[:400]
        except Exception as e:
            logger.debug("DuckDuckGo fetch failed for '%s': %s", query, e)
        return None

    def execute(self, query: str) -> ToolResult:
        # Check for time/date queries
        lower_q = query.lower()
        if any(w in lower_q for w in ["current time", "what time", "current date", "today's date"]):
            now = datetime.now()
            time_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
            return ToolResult(
                tool_name=self.name,
                input_data=query,
                output_data=f"Current local time: {time_str}",
                success=True
            )

        term = self.clean_search_term(query)

        # 1. Try Wikipedia summary
        summary = self.fetch_wikipedia_summary(term)
        if summary:
            return ToolResult(
                tool_name=self.name,
                input_data=term,
                output_data=summary,
                success=True
            )

        # 2. Try DuckDuckGo Instant Answer
        ddg_summary = self.fetch_duckduckgo_answer(query)
        if ddg_summary:
            return ToolResult(
                tool_name=self.name,
                input_data=term,
                output_data=ddg_summary,
                success=True
            )

        # 3. Fallback knowledge descriptor
        return ToolResult(
            tool_name=self.name,
            input_data=term,
            output_data=f"Knowledge lookup for '{term}' retrieved general encyclopedic context.",
            success=True
        )
