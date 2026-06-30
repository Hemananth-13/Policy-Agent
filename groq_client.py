import os
import logging
import httpx
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"


def load_system_prompt() -> str:
    try:
        if not SYSTEM_PROMPT_PATH.exists():
            raise FileNotFoundError(f"System prompt not found at {SYSTEM_PROMPT_PATH}")
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to load system prompt: {e}")


# Validate API key at startup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY is not set. Please add it to your .env file.\n"
        "Example: GROQ_API_KEY=your_key_here"
    )

# Model configurable via environment variable
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Load system prompt once at startup
SYSTEM_PROMPT = load_system_prompt()

# Disable SSL verification to fix Windows certificate issue (local dev only)
http_client = httpx.Client(verify=False)
client = Groq(api_key=GROQ_API_KEY, http_client=http_client)


def call_llm(user_message: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """
    Send a message to Groq LLM using the system prompt from system_prompt.md.
    Returns the text response.
    """
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Log token usage at debug level
    if response.usage:
        logger.debug(
            "Token usage — prompt: %d, completion: %d, total: %d",
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            response.usage.total_tokens,
        )

    return response.choices[0].message.content.strip()
