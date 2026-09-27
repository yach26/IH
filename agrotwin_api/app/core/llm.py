"""Optional, bounded Groq/xAI text generation; failures never become plan text."""
import logging
import os

LOG = logging.getLogger(__name__)
_client = None
_client_config = None


def _config():
    groq_key = os.getenv("GROQ_API_KEY", "")
    xai_key = os.getenv("XAI_API_KEY", "")
    # Support the original branch's Groq-key-in-XAI_API_KEY setup.
    if groq_key or xai_key.startswith("gsk_"):
        return (groq_key or xai_key, "https://api.groq.com/openai/v1",
                os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    return xai_key, "https://api.x.ai/v1", os.getenv("XAI_MODEL", "grok-4.3")


def get_client():
    global _client, _client_config
    key, base_url, _ = _config()
    if not key:
        raise ValueError("Set GROQ_API_KEY or XAI_API_KEY to enable LLM text.")
    if _client is None or _client_config != (key, base_url):
        from openai import OpenAI
        _client = OpenAI(api_key=key, base_url=base_url, timeout=10.0, max_retries=0)
        _client_config = (key, base_url)
    return _client


def generate_chat_completion(messages, model=None, temperature=0.3, max_tokens=500):
    key, _, default_model = _config()
    if not key:
        return ""
    try:
        response = get_client().chat.completions.create(
            model=model or default_model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        LOG.warning("Optional LLM request failed (%s)", type(exc).__name__)
        return ""
