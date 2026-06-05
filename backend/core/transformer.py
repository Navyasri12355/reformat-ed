"""
NeuraCore — AI Transformer Service
====================================
Accepts a curriculum atom + cognitive profile, picks the right prompt,
calls the configured AI model (OpenAI or Anthropic), and returns
the rewritten text.

Usage:
    from core.transformer import transform_atom
    result = await transform_atom("Plants make food using sunlight...", "adhd")
"""
from core.config import settings
from core.prompts import build_prompt, ProfileType


async def transform_atom(atom_text: str, profile: ProfileType) -> str:
    """
    Rewrite a curriculum atom for the given neurodivergent profile.

    Priority: OpenAI → Anthropic (uses whichever key is set in .env).

    Args:
        atom_text: Plain text chunk from the document parser
        profile:   "adhd" | "dyslexia" | "asd"

    Returns:
        AI-rewritten text string

    Raises:
        RuntimeError: if no API key is configured
        Exception:    if the model call fails (caller should catch and surface)
    """
    messages = build_prompt(profile, atom_text)

    if settings.OPENAI_API_KEY:
        return await _call_openai(messages)

    if settings.ANTHROPIC_API_KEY:
        return await _call_anthropic(messages)

    raise RuntimeError(
        "No AI API key configured. "
        "Add OPENAI_API_KEY or ANTHROPIC_API_KEY to backend/.env"
    )


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

async def _call_openai(messages: list[dict]) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    model  = settings.MODEL or "gpt-4o"

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=512,
        timeout=30,
    )
    return response.choices[0].message.content.strip()


async def _call_anthropic(messages: list[dict]) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    model  = settings.MODEL or "claude-3-5-sonnet-20241022"

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
