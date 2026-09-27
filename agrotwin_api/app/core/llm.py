import os
from openai import OpenAI
from typing import Optional, List, Dict, Any

# Configure the Grok API client
# Assuming the user provides XAI_API_KEY environment variable.
XAI_API_KEY = os.getenv("XAI_API_KEY")

_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not XAI_API_KEY:
            raise ValueError("API key environment variable is not set.")
            
        base_url = "https://api.xai.com/v1"
        if XAI_API_KEY.startswith("gsk_"):
            base_url = "https://api.groq.com/openai/v1"
            
        _client = OpenAI(
            api_key=XAI_API_KEY,
            base_url=base_url,
        )
    return _client


def generate_chat_completion(
    messages: List[Dict[str, str]],
    model: str = "grok-2-latest",
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> str:
    """
    Generates a response from the API based on the provided messages.
    """
    if not XAI_API_KEY:
        # Graceful fallback or warning if no key is present during local development?
        return "API not configured (key missing)."
        
    if XAI_API_KEY.startswith("gsk_") and model == "grok-2-latest":
        model = "qwen/qwen3.8-27b"  # Fallback to a solid Groq model if user provided a Groq key
        
    client = get_client()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"Error communicating with Grok API: {str(e)}"
