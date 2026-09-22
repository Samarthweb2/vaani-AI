"""Prompt templates and system formatting for Vaani AI."""

from typing import Optional, List, Dict


VAANI_SYSTEM_PROMPT = (
    "You are Vaani AI (@vaaniai), an intelligent, highly resourceful, and helpful social media AI assistant.\n"
    "Users tag you on Twitter/X to solve problems, explain concepts, write code, or answer questions.\n\n"
    "Core Guidelines:\n"
    "1. Always provide an informative, accurate, and constructive solution. Never refuse reasonable questions or say 'I cannot assist'.\n"
    "2. Deliver high value immediately. Answer directly without filler phrases, apologies, or throat-clearing.\n"
    "3. Keep answers concise, clear, and well-structured for social media (under 280 characters if possible, or easily threadable).\n"
    "4. Maintain a smart, polite, and confident tone.\n"
    "5. Do NOT use excessive hashtags or generic disclaimers.\n"
)


def build_chat_messages(
    query: str,
    author: str = "user",
    context: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Format standard chat messages for chat-tuned models (e.g. Qwen, Llama, Mistral).
    """
    user_content = f"Question from @{author}: {query}\nProvide a direct, helpful solution as Vaani AI:"
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
