# ia-tools/ia_tools_catalog.py
"""Static AI-tools catalog — organic data source for IAToolsMCP.

Curated list of LLMs, coding assistants, image generators, and AI platforms.
Keyword search against name, provider, category, and tags.
"""
from __future__ import annotations

_CATALOG: list[dict] = [
    {
        "id": "claude", "name": "Claude", "provider": "Anthropic",
        "category": "llm", "price_from": "Free / 20 USD/mo (Pro)",
        "url": "https://claude.ai",
        "tags": ["claude", "llm", "chat", "anthropic", "ai", "assistant"],
    },
    {
        "id": "gpt4", "name": "GPT-4o", "provider": "OpenAI",
        "category": "llm", "price_from": "20 USD/mo (Plus)",
        "url": "https://openai.com/gpt-4",
        "tags": ["gpt", "gpt4", "openai", "llm", "chat", "ai", "assistant"],
    },
    {
        "id": "gemini", "name": "Gemini", "provider": "Google",
        "category": "llm", "price_from": "Free / 19.99 USD/mo (Advanced)",
        "url": "https://gemini.google.com",
        "tags": ["gemini", "google", "bard", "llm", "chat", "ai", "assistant"],
    },
    {
        "id": "mistral", "name": "Mistral AI", "provider": "Mistral",
        "category": "llm", "price_from": "API from 0.14 USD/1M tokens",
        "url": "https://mistral.ai",
        "tags": ["mistral", "llm", "open-source", "ai", "french"],
    },
    {
        "id": "llama", "name": "Llama 3", "provider": "Meta",
        "category": "llm", "price_from": "Free (open-weights)",
        "url": "https://llama.meta.com",
        "tags": ["llama", "meta", "open-source", "llm", "local", "ai"],
    },
    {
        "id": "cursor", "name": "Cursor", "provider": "Anysphere",
        "category": "coding-assistant", "price_from": "0 USD/mo (Hobby) / 20 USD/mo (Pro)",
        "url": "https://cursor.sh",
        "tags": ["cursor", "coding", "code", "assistant", "ide", "ai", "copilot", "dev"],
    },
    {
        "id": "github-copilot", "name": "GitHub Copilot", "provider": "GitHub / OpenAI",
        "category": "coding-assistant", "price_from": "10 USD/mo",
        "url": "https://github.com/features/copilot",
        "tags": ["copilot", "github", "coding", "code", "assistant", "ai", "dev", "vscode"],
    },
    {
        "id": "codeium", "name": "Codeium", "provider": "Codeium",
        "category": "coding-assistant", "price_from": "Free / 15 USD/mo (Teams)",
        "url": "https://codeium.com",
        "tags": ["codeium", "coding", "code", "assistant", "ai", "free", "dev"],
    },
    {
        "id": "midjourney", "name": "Midjourney", "provider": "Midjourney",
        "category": "image-gen", "price_from": "10 USD/mo",
        "url": "https://midjourney.com",
        "tags": ["midjourney", "image", "art", "generative", "ai", "design", "illustration"],
    },
    {
        "id": "dalle3", "name": "DALL-E 3", "provider": "OpenAI",
        "category": "image-gen", "price_from": "0.040 USD/image",
        "url": "https://openai.com/dall-e-3",
        "tags": ["dalle", "dall-e", "openai", "image", "art", "generative", "ai"],
    },
    {
        "id": "stable-diffusion", "name": "Stable Diffusion", "provider": "Stability AI",
        "category": "image-gen", "price_from": "Free (open-weights)",
        "url": "https://stability.ai",
        "tags": ["stable-diffusion", "sd", "stability", "image", "art", "open-source", "local"],
    },
    {
        "id": "perplexity", "name": "Perplexity AI", "provider": "Perplexity",
        "category": "search", "price_from": "Free / 20 USD/mo (Pro)",
        "url": "https://perplexity.ai",
        "tags": ["perplexity", "search", "ai", "research", "web", "assistant"],
    },
    {
        "id": "langchain", "name": "LangChain", "provider": "LangChain Inc.",
        "category": "framework", "price_from": "Free (open-source)",
        "url": "https://langchain.com",
        "tags": ["langchain", "framework", "rag", "agent", "python", "dev", "llm", "open-source"],
    },
    {
        "id": "llamaindex", "name": "LlamaIndex", "provider": "LlamaIndex",
        "category": "framework", "price_from": "Free (open-source)",
        "url": "https://llamaindex.ai",
        "tags": ["llamaindex", "llama-index", "framework", "rag", "index", "python", "dev", "llm"],
    },
    {
        "id": "huggingface", "name": "Hugging Face", "provider": "Hugging Face",
        "category": "platform", "price_from": "Free / 9 USD/mo (Pro)",
        "url": "https://huggingface.co",
        "tags": ["huggingface", "hf", "platform", "models", "datasets", "open-source", "ai", "ml"],
    },
    {
        "id": "replicate", "name": "Replicate", "provider": "Replicate",
        "category": "platform", "price_from": "Pay-per-use",
        "url": "https://replicate.com",
        "tags": ["replicate", "platform", "api", "models", "ai", "image", "llm", "deploy"],
    },
    {
        "id": "elevenlabs", "name": "ElevenLabs", "provider": "ElevenLabs",
        "category": "voice", "price_from": "Free / 5 USD/mo (Starter)",
        "url": "https://elevenlabs.io",
        "tags": ["elevenlabs", "voice", "tts", "speech", "audio", "ai", "clone"],
    },
]


class IAToolsCatalogError(Exception):
    """Raised on any catalog fault."""


class IAToolsCatalogClient:
    """In-memory AI-tools catalog — no HTTP, no rate limits.

    search() does case-insensitive substring matching against name, provider,
    category, and tags.
    aclose() is a no-op.
    """

    async def search(self, query: str) -> list[dict]:
        """Return tools whose name, provider, category, or tags match any query token."""
        tokens = query.lower().split()
        results = []
        for item in _CATALOG:
            haystack = (
                item["name"].lower()
                + " " + item["provider"].lower()
                + " " + item["category"].lower()
                + " " + " ".join(item["tags"])
            )
            if any(tok in haystack for tok in tokens):
                results.append(item)
        return results

    async def aclose(self) -> None:
        pass
