import os

from openai import OpenAI  # type: ignore


def make_client() -> OpenAI:
    """
    Create an OpenAI-compatible client that can talk to different providers
    (Ollama, Groq, Gemini, Hugging Face, etc.) based on environment variables.

    Configuration (all optional, with sensible defaults):

    - API_PROVIDER:
        One of: "ollama", "groq", "gemini", "huggingface".
        Default: "ollama".

    - OPENAI_BASE_URL:
        If set, this is used directly for the client base_url.
        If not set, a default is derived from API_PROVIDER:
          * ollama     -> http://localhost:11434/v1
          * groq       -> https://api.groq.com/openai/v1
          * gemini     -> https://generativelanguage.googleapis.com/v1beta/openai/
          * huggingface-> https://api-inference.huggingface.co/v1

    - OPENAI_API_KEY:
        Provider-specific API key.
        For Ollama, this is not used by the server but is still required
        by the OpenAI client, so any non-empty string is fine (e.g. "ollama").
    """
    provider = os.getenv("API_PROVIDER", "ollama").strip().lower()

    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    api_key = os.getenv("OPENAI_API_KEY", "").strip() or None

    if base_url is None:
        if provider == "ollama":
            base_url = "http://localhost:11434/v1"
            # Ollama ignores the key, but the client requires something non-empty
            if not api_key:
                api_key = "ollama"
        elif provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
        elif provider == "gemini":
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif provider == "huggingface":
            base_url = "https://api-inference.huggingface.co/v1"

    if not api_key:
        # Leave it empty only if the environment truly has no key;
        # this will cause the OpenAI client to raise a clear error.
        raise ValueError(
            "OPENAI_API_KEY is not set. Please provide a key for the selected provider."
        )

    return OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

