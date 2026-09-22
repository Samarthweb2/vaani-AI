"""Text processing, mention stripping, and tweet thread formatting for Twitter/X."""

import re
from typing import List


def clean_query(text: str, bot_handle: str = "vaaniai") -> str:
    """
    Remove the @bot_handle tag and any stray usernames at the start,
    returning the clean query prompt for the LLM.

    Example:
        '@vaaniai what is machine learning?' -> 'what is machine learning?'
        '@user @vaaniai explain recursion' -> 'explain recursion'
    """
    # Remove bot handle mention case-insensitively (supports @vaaniai, @vaani, @vaani_ai, etc.)
    handle_pattern = re.compile(rf"@(vaaniai|vaani_ai|vaani|{re.escape(bot_handle)})\b", re.IGNORECASE)
    cleaned = handle_pattern.sub("", text)

    # If user typed '@vaani ai ...', remove leading 'ai' word
    cleaned = re.sub(r"^\s*ai\b", "", cleaned, flags=re.IGNORECASE)

    # Remove any other leading mentions like @someone
    cleaned = re.sub(r"^(\s*@\w+\s*)+", "", cleaned)

    # Clean whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def clean_response(text: str) -> str:
    """
    Remove unnecessary markdown formatting that doesn't render well on Twitter
    (e.g., code block fences, excess bolding).
    """
    # Replace markdown headers like '### ' with clean text
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # Remove code blocks ```python ... ``` fences but preserve content
    text = re.sub(r"```[\w-]*\n?", "", text)
    text = text.replace("```", "")
    # Remove double bolding if excessive
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # Strip excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_tweet_chunks(response: str, max_chars: int = 280) -> List[str]:
    """
    Split a response into one or more tweets respecting the 280 character limit.
    If multiple chunks are needed, numbers them like (1/3), (2/3), etc.
    """
    cleaned = clean_response(response)
    if not cleaned:
        return ["I could not generate an answer to that question."]

    if len(cleaned) <= max_chars:
        return [cleaned]

    # Split into words or sentences to respect character limits
    words = cleaned.split()
    chunks = []
    current_chunk = []

    # Reserve 7 characters for thread indicator e.g. " (1/10)"
    effective_limit = max_chars - 8

    for word in words:
        candidate = " ".join(current_chunk + [word])
        if len(candidate) <= effective_limit:
            current_chunk.append(word)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
            else:
                # Word itself exceeds limit, hard slice
                chunks.append(word[:effective_limit])
                current_chunk = [word[effective_limit:]]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    total = len(chunks)
    if total == 1:
        return chunks

    # Add thread indicators (e.g. " (1/3)")
    threaded_chunks = []
    for idx, chunk in enumerate(chunks, 1):
        indicator = f" ({idx}/{total})"
        # If adding indicator exceeds max_chars, trim chunk
        if len(chunk) + len(indicator) > max_chars:
            chunk = chunk[: max_chars - len(indicator) - 1] + "…"
        threaded_chunks.append(f"{chunk}{indicator}")

    return threaded_chunks
