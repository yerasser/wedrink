from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_base_url: str
    api_timeout: float

def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    api_timeout = float(os.getenv("API_TIMEOUT", "30"))

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is empty")

    return Settings(
        bot_token=bot_token,
        api_base_url=api_base_url,
        api_timeout=api_timeout,
    )
