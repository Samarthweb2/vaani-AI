"""Prompt templates and system formatting for Vaani AI."""

from typing import Optional, List, Dict


VAANI_SYSTEM_PROMPT = (
    "You are Vaani AI (@vaaniai), an intelligent, insightful, and helpful social media AI agent.\n"
    "Users mention you on Twitter/X to solve problems, explain concepts, answer questions, or get assistance.\n\n"
    "Rules for responses:\n"
    "1. Be direct, clear, and provide high-value answers immediately without unnecessary conversational filler.\n"
    "2. Keep the answer concise and suitable for social media (under 280 characters if possible, or easily chunkable).\n"
    "3. Use a polite, smart, and confident tone.\n"
    "4. Do NOT start with 'Sure!' or 'Here is your answer:'. Answer directly.\n"
    "5. Do NOT tag excessive hashtags.\n"
)


def build_chat_messages(
    query: str,
    author: str = "user",
    context: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Format standard chat messages for chat-tuned models (e.g. Qwen, Llama, Mistral).
    """
    user_content = f"@{author} asked: {query}"
    if context:
        user_content = f"Thread context: {context}\n\n{user_content}"

    return [
        {"role": "system", "content": VAANI_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]


def build_raw_prompt(
    query: str,
    author: str = "user",
    context: Optional[str] = None
) -> str:
    """
    Format a plain text prompt for base or non-chat models.
    """
    messages = build_chat_messages(query, author, context)
    prompt = f"### System:\n{messages[0]['content']}\n\n"
    prompt += f"### User:\n{messages[1]['content']}\n\n"
    prompt += "### Vaani AI:\n"
    return prompt
