"""Dynamic model discovery for the LLM Council."""

import httpx
from typing import Optional
from functools import lru_cache
import time

# Frontier vendors we want on the council
FRONTIER_VENDORS = ["openai", "anthropic", "google", "x-ai"]

# Model selection preferences per vendor
# Format: (vendor, include_pattern, exclude_pattern)
# Cost tier options - set via USE_BUDGET_MODELS env var
# Budget: ~$0.05/query, Balanced: ~$0.15/query, Premium: ~$1.50/query
import os
USE_BUDGET_MODELS = os.getenv("USE_BUDGET_MODELS", "balanced").lower()

VENDOR_PREFERENCES_BUDGET = {
    "openai": {
        "include": ["gpt-4o-mini", "gpt-5-mini"],  # Mini models, very cheap
        "exclude": ["search", "audio"],
    },
    "anthropic": {
        "include": ["claude-sonnet"],  # Sonnet is great value
        "exclude": ["opus"],
    },
    "google": {
        "include": ["gemini-3-flash", "gemini-2.5-flash"],  # Flash models
        "exclude": ["lite", "image", "nano", "exp"],
    },
    "x-ai": {
        "include": ["grok-4"],  # Fast variants are cheap
        "exclude": ["mini", "code"],
    },
}

VENDOR_PREFERENCES_BALANCED = {
    "openai": {
        "include": ["gpt-5.2", "gpt-4o"],  # Standard GPT-5.2 (NOT pro), or GPT-4o
        "exclude": ["mini", "codex", "image", "safeguard", "pro", "extended", "search", "audio", "chat"],
    },
    "anthropic": {
        "include": ["claude-sonnet"],  # Sonnet 4.5 is excellent and cheaper than Opus
        "exclude": ["opus"],
    },
    "google": {
        "include": ["gemini-3-pro", "gemini-4"],  # Pro tier Gemini
        "exclude": ["flash", "image", "nano"],
    },
    "x-ai": {
        "include": ["grok-4", "grok-5"],  # Latest Grok
        "exclude": ["mini", "code"],
    },
}

VENDOR_PREFERENCES_PREMIUM = {
    "openai": {
        "include": ["gpt-5.2-pro", "gpt-6"],  # Top tier (expensive!)
        "exclude": ["mini", "codex", "image", "safeguard", "chat"],
    },
    "anthropic": {
        "include": ["claude-opus"],  # Opus is the best
        "exclude": [],
    },
    "google": {
        "include": ["gemini-3-pro", "gemini-4"],
        "exclude": ["flash", "image", "nano"],
    },
    "x-ai": {
        "include": ["grok-4", "grok-5"],
        "exclude": ["mini", "fast"],  # Non-fast for premium
    },
}

# Select preferences based on tier
VENDOR_PREFERENCES = {
    "budget": VENDOR_PREFERENCES_BUDGET,
    "balanced": VENDOR_PREFERENCES_BALANCED,
    "premium": VENDOR_PREFERENCES_PREMIUM,
}.get(USE_BUDGET_MODELS, VENDOR_PREFERENCES_BALANCED)

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600
_cache_timestamp = 0
_cached_models = None


def fetch_openrouter_models() -> list[dict]:
    """Fetch all available models from OpenRouter."""
    global _cache_timestamp, _cached_models

    # Return cached if fresh
    if _cached_models and (time.time() - _cache_timestamp) < CACHE_TTL:
        return _cached_models

    try:
        response = httpx.get("https://openrouter.ai/api/v1/models", timeout=10)
        response.raise_for_status()
        _cached_models = response.json().get("data", [])
        _cache_timestamp = time.time()
        return _cached_models
    except Exception as e:
        print(f"Error fetching models from OpenRouter: {e}")
        return _cached_models or []


def get_vendor_from_id(model_id: str) -> Optional[str]:
    """Extract vendor from model ID (e.g., 'openai/gpt-5' -> 'openai')."""
    if "/" in model_id:
        return model_id.split("/")[0]
    return None


def matches_preferences(model_id: str, prefs: dict) -> bool:
    """Check if model matches vendor preferences."""
    model_name = model_id.split("/")[-1].lower()

    # Must match at least one include pattern
    includes = prefs.get("include", [])
    if includes and not any(inc.lower() in model_name for inc in includes):
        return False

    # Must not match any exclude pattern
    excludes = prefs.get("exclude", [])
    if any(exc.lower() in model_name for exc in excludes):
        return False

    return True


def get_latest_frontier_models(count_per_vendor: int = 1) -> list[str]:
    """
    Get the latest frontier model from each major vendor.

    Returns list of model IDs like ['openai/gpt-5.2', 'anthropic/claude-opus-4.5', ...]
    """
    models = fetch_openrouter_models()
    if not models:
        # Fallback to hardcoded if API fails
        return [
            "openai/gpt-5.2",
            "anthropic/claude-opus-4.5",
            "google/gemini-3-pro-preview",
            "x-ai/grok-4",
        ]

    # Group by vendor and filter
    vendor_models = {v: [] for v in FRONTIER_VENDORS}

    for model in models:
        model_id = model.get("id", "")
        vendor = get_vendor_from_id(model_id)

        if vendor not in FRONTIER_VENDORS:
            continue

        prefs = VENDOR_PREFERENCES.get(vendor, {})
        if not matches_preferences(model_id, prefs):
            continue

        vendor_models[vendor].append({
            "id": model_id,
            "name": model.get("name", ""),
            "created": model.get("created", 0),
            "pricing": model.get("pricing", {}),
        })

    # Sort each vendor's models by creation date (newest first)
    result = []
    for vendor in FRONTIER_VENDORS:
        sorted_models = sorted(
            vendor_models[vendor],
            key=lambda x: x["created"],
            reverse=True
        )
        # Take the top N models from each vendor
        for model in sorted_models[:count_per_vendor]:
            result.append(model["id"])

    return result


def get_chairman_model() -> str:
    """Get the best model for chairman role (synthesis)."""
    # Prefer Gemini Pro for synthesis (good at summarization)
    models = fetch_openrouter_models()

    for model in models:
        model_id = model.get("id", "")
        if "gemini-3-pro" in model_id and "flash" not in model_id and "image" not in model_id:
            return model_id

    # Fallback
    return "google/gemini-3-pro-preview"


def get_council_info() -> dict:
    """Get current council configuration for display."""
    council = get_latest_frontier_models()
    chairman = get_chairman_model()

    return {
        "council_models": council,
        "chairman_model": chairman,
        "vendor_count": len(set(get_vendor_from_id(m) for m in council)),
        "model_count": len(council),
    }


if __name__ == "__main__":
    # Test the dynamic model fetching
    print("Latest frontier models:")
    for model in get_latest_frontier_models():
        print(f"  - {model}")
    print(f"\nChairman: {get_chairman_model()}")
    print(f"\nCouncil info: {get_council_info()}")
