"""
NeuraCore — Cognitive Transformation Service
===============================================
Accepts a curriculum atom + a cognitive profile, picks the right prompt template,
calls the configured AI model, and returns the rewritten text.

Supports:
  - OpenAI (GPT-4o by default)
  - Anthropic Claude (set MODEL=claude-3-5-sonnet-20241022 in .env)
"""

from core.config import settings
from core.prompts import build_prompt, ProfileType


async def transform_atom(atom_text: str, profile: ProfileType) -> str:
    """
    Rewrite a curriculum atom for the given neurodivergent profile.

    Args:
        atom_text: Plain text chunk from Phase 1 parsing
        profile:   "adhd" | "dyslexia" | "asd"

    Returns:
        AI-rewritten text string

    Raises:
        RuntimeError: if no API key is configured or the model call fails
    """
    messages = build_prompt(profile, atom_text)

    # ── OpenAI path ──
    if settings.OPENAI_API_KEY:
        return await _call_openai(messages)

    # ── Anthropic path ──
    if settings.ANTHROPIC_API_KEY:
        return await _call_anthropic(messages)

    raise RuntimeError(
        "No AI API key configured. Add OPENAI_API_KEY or ANTHROPIC_API_KEY to your .env file."
    )


async def _call_openai(messages: list[dict]) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    model = settings.MODEL or "gpt-4o"

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,          # creative but controlled
        max_tokens=512,
        timeout=30,
    )
    return response.choices[0].message.content.strip()


async def _call_anthropic(messages: list[dict]) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    model = settings.MODEL or "claude-3-5-sonnet-20241022"

    # Anthropic uses a separate system field — split from messages list
    system_content = next(
        (m["content"] for m in messages if m["role"] == "system"), ""
    )
    user_messages = [m for m in messages if m["role"] != "system"]

    response = await client.messages.create(
        model=model,
        system=system_content,
        messages=user_messages,
        max_tokens=512,
        timeout=30,
    )
    return response.content[0].text.strip()
