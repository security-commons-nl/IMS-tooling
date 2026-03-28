"""OpenAI-compatible LLM client for OpenRouter (or any OpenAI-compatible API)."""

import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.AI_API_BASE,
            api_key=settings.AI_API_KEY or "dummy",
            timeout=60.0,
        )
    return _client


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Non-streaming chat completion. Returns the full response dict."""
    client = get_client()
    model = model or settings.AI_MODEL_NAME
    temperature = temperature if temperature is not None else settings.AI_TEMPERATURE
    max_tokens = max_tokens or settings.AI_MAX_TOKENS

    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choice = response.choices[0]
            return {
                "content": choice.message.content or "",
                "model": response.model,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "finish_reason": choice.finish_reason,
            }
        except RateLimitError:
            if attempt < 2:
                import asyncio
                await asyncio.sleep(2 ** attempt)
                continue
            raise
        except APITimeoutError:
            if attempt < 2:
                import asyncio
                await asyncio.sleep(1)
                continue
            raise
        except APIError as e:
            logger.error(f"LLM API error: {e}")
            raise

    return {"content": "", "model": model, "prompt_tokens": 0, "completion_tokens": 0, "finish_reason": "error"}


async def chat_completion_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncGenerator[str, None]:
    """Streaming chat completion. Yields content chunks."""
    client = get_client()
    model = model or settings.AI_MODEL_NAME
    temperature = temperature if temperature is not None else settings.AI_TEMPERATURE
    max_tokens = max_tokens or settings.AI_MAX_TOKENS

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def create_embedding(
    text: str,
    model: str | None = None,
) -> list[float]:
    """Generate an embedding vector for the given text."""
    client = get_client()
    model = model or settings.AI_EMBEDDING_MODEL

    response = await client.embeddings.create(
        model=model,
        input=text,
    )
    return response.data[0].embedding
