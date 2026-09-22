import pytest
from vaani.twitter.formatter import clean_query, clean_response, format_tweet_chunks


def test_clean_query():
    # Basic mention
    assert clean_query("@vaaniai what is python?") == "what is python?"
    # Case insensitive
    assert clean_query("@VaaniAI what is machine learning?") == "what is machine learning?"
    # Multiple mentions
    assert clean_query("@user1 @vaaniai explain deep learning") == "explain deep learning"
    # Mention in middle or end
    assert clean_query("hey @vaaniai can you help?") == "hey can you help?"
    # Extra whitespace
    assert clean_query("   @vaaniai    hello    world   ") == "hello world"


def test_clean_response():
    markdown_text = "### Header\n**Key Point:** Use ```python\nprint('hello')\n``` for output."
    cleaned = clean_response(markdown_text)
    assert "###" not in cleaned
    assert "```" not in cleaned
    assert "**" not in cleaned
    assert "print('hello')" in cleaned


def test_format_tweet_chunks_short():
    short_text = "This is a concise solution under 280 characters."
    chunks = format_tweet_chunks(short_text, max_chars=280)
    assert len(chunks) == 1
    assert chunks[0] == short_text


def test_format_tweet_chunks_long():
    # Create long text exceeding 280 chars
    long_text = " ".join(["Explanation paragraph word"] * 30)
    chunks = format_tweet_chunks(long_text, max_chars=100)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 100
        # Check thread indicator
        assert "(" in chunk and ")" in chunk
