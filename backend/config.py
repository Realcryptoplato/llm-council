"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Dynamic model selection - fetches latest frontier models from OpenRouter
# Set to False to use hardcoded fallbacks below
USE_DYNAMIC_MODELS = os.getenv("USE_DYNAMIC_MODELS", "true").lower() == "true"

# Hardcoded fallback models (used if USE_DYNAMIC_MODELS=false or API fails)
FALLBACK_COUNCIL_MODELS = [
    "openai/gpt-5.2",
    "anthropic/claude-opus-4.5",
    "google/gemini-3-pro-preview",
    "x-ai/grok-4",
]
FALLBACK_CHAIRMAN_MODEL = "google/gemini-3-pro-preview"


def get_council_models() -> list[str]:
    """Get council models - dynamic or fallback."""
    if USE_DYNAMIC_MODELS:
        try:
            from .models import get_latest_frontier_models
            return get_latest_frontier_models()
        except Exception as e:
            print(f"Dynamic model fetch failed, using fallback: {e}")
    return FALLBACK_COUNCIL_MODELS


def get_chairman_model() -> str:
    """Get chairman model - dynamic or fallback."""
    if USE_DYNAMIC_MODELS:
        try:
            from .models import get_chairman_model as fetch_chairman
            return fetch_chairman()
        except Exception as e:
            print(f"Dynamic chairman fetch failed, using fallback: {e}")
    return FALLBACK_CHAIRMAN_MODEL


# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
