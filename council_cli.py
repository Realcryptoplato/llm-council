#!/usr/bin/env python3
"""
Standalone LLM Council CLI - No server required.

Usage:
    python council_cli.py "What is the best database for real-time apps?"
    python council_cli.py --tier budget "Your question here"
    python council_cli.py --json "Your question here"  # JSON output

Environment:
    OPENROUTER_API_KEY: Required. Get from https://openrouter.ai/keys
    USE_BUDGET_MODELS: Optional. budget|balanced|premium (default: balanced)
"""

import asyncio
import httpx
import json
import os
import sys
from typing import List, Dict, Any, Optional, Tuple

# Try to load from .env file
try:
    from dotenv import load_dotenv
    # Look for .env in script directory or current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model tiers
TIER = os.getenv("USE_BUDGET_MODELS", "balanced").lower()

MODELS_BY_TIER = {
    "budget": {
        "council": [
            "openai/gpt-4o-mini",
            "anthropic/claude-3-5-sonnet",
            "google/gemini-2.0-flash-001",
            "x-ai/grok-4.1-fast",
        ],
        "chairman": "google/gemini-2.0-flash-001",
    },
    "balanced": {
        "council": [
            "openai/gpt-5.2",
            "anthropic/claude-sonnet-4.5",
            "google/gemini-3-pro-preview",
            "x-ai/grok-4.1-fast",
        ],
        "chairman": "google/gemini-3-pro-preview",
    },
    "premium": {
        "council": [
            "openai/gpt-5.2-pro",
            "anthropic/claude-opus-4.5",
            "google/gemini-3-pro-preview",
            "x-ai/grok-4",
        ],
        "chairman": "google/gemini-3-pro-preview",
    },
}


async def query_model(model: str, messages: List[Dict], timeout: float = 120.0) -> Optional[Dict]:
    """Query a single model via OpenRouter."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return {"content": data["choices"][0]["message"].get("content", "")}
    except Exception as e:
        print(f"  ⚠ Error querying {model}: {e}", file=sys.stderr)
        return None


async def query_models_parallel(models: List[str], messages: List[Dict]) -> Dict[str, Optional[Dict]]:
    """Query multiple models in parallel."""
    tasks = [query_model(model, messages) for model in models]
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}


async def stage1_collect_responses(query: str, council_models: List[str]) -> List[Dict]:
    """Stage 1: Collect individual responses from all council models."""
    messages = [{"role": "user", "content": query}]
    responses = await query_models_parallel(council_models, messages)

    results = []
    for model, response in responses.items():
        if response:
            results.append({"model": model, "response": response.get("content", "")})
    return results


async def stage2_collect_rankings(
    query: str, stage1_results: List[Dict], council_models: List[str]
) -> Tuple[List[Dict], Dict[str, str]]:
    """Stage 2: Each model ranks the anonymized responses."""
    labels = [chr(65 + i) for i in range(len(stage1_results))]
    label_to_model = {f"Response {label}": result["model"] for label, result in zip(labels, stage1_results)}

    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually.
2. Then provide a final ranking.

IMPORTANT: End with "FINAL RANKING:" followed by a numbered list from best to worst.
Example:
FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]
    responses = await query_models_parallel(council_models, messages)

    results = []
    for model, response in responses.items():
        if response:
            results.append({"model": model, "ranking": response.get("content", "")})

    return results, label_to_model


async def stage3_synthesize(
    query: str, stage1_results: List[Dict], stage2_results: List[Dict], chairman_model: str
) -> Dict:
    """Stage 3: Chairman synthesizes final response."""
    stage1_text = "\n\n".join([
        f"Model: {r['model']}\nResponse: {r['response']}" for r in stage1_results
    ])
    stage2_text = "\n\n".join([
        f"Model: {r['model']}\nRanking: {r['ranking']}" for r in stage2_results
    ])

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses and ranked each other.

Original Question: {query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

Synthesize all of this into a single, comprehensive, accurate answer that represents the council's collective wisdom:"""

    messages = [{"role": "user", "content": chairman_prompt}]
    response = await query_model(chairman_model, messages)

    return {
        "model": chairman_model,
        "response": response.get("content", "Error: Unable to synthesize.") if response else "Error: Chairman failed."
    }


async def run_council(query: str, tier: str = "balanced") -> Dict:
    """Run the full 3-stage council process."""
    config = MODELS_BY_TIER.get(tier, MODELS_BY_TIER["balanced"])
    council_models = config["council"]
    chairman_model = config["chairman"]

    print(f"\n🏛️  LLM Council ({tier} tier)", file=sys.stderr)
    print(f"   Council: {', '.join([m.split('/')[-1] for m in council_models])}", file=sys.stderr)
    print(f"   Chairman: {chairman_model.split('/')[-1]}", file=sys.stderr)
    print(file=sys.stderr)

    # Stage 1
    print("📝 Stage 1: Collecting individual responses...", file=sys.stderr)
    stage1 = await stage1_collect_responses(query, council_models)
    if not stage1:
        return {"error": "All models failed in Stage 1"}
    print(f"   ✓ Got {len(stage1)} responses", file=sys.stderr)

    # Stage 2
    print("🔍 Stage 2: Peer ranking (anonymized)...", file=sys.stderr)
    stage2, label_map = await stage2_collect_rankings(query, stage1, council_models)
    print(f"   ✓ Got {len(stage2)} rankings", file=sys.stderr)

    # Stage 3
    print("⚖️  Stage 3: Chairman synthesizing...", file=sys.stderr)
    stage3 = await stage3_synthesize(query, stage1, stage2, chairman_model)
    print("   ✓ Synthesis complete", file=sys.stderr)
    print(file=sys.stderr)

    return {
        "answer": stage3["response"],
        "chairman": stage3["model"],
        "council_models": council_models,
        "tier": tier,
        "stage1": stage1,
        "stage2": stage2,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Query the LLM Council")
    parser.add_argument("question", nargs="?", help="The question to ask the council")
    parser.add_argument("--tier", choices=["budget", "balanced", "premium"], default=TIER,
                       help="Cost tier (default: balanced)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--models", action="store_true", help="Show available models and exit")
    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not set.", file=sys.stderr)
        print("Set it in your environment or create a .env file.", file=sys.stderr)
        sys.exit(1)

    if args.models:
        print(json.dumps(MODELS_BY_TIER, indent=2))
        sys.exit(0)

    if not args.question:
        parser.print_help()
        sys.exit(1)

    result = asyncio.run(run_council(args.question, args.tier))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print("=" * 60)
        print("COUNCIL'S ANSWER")
        print("=" * 60)
        print(result["answer"])
        print()
        print("-" * 60)
        print(f"Deliberated by: {', '.join([m.split('/')[-1] for m in result['council_models']])}")
        print(f"Synthesized by: {result['chairman'].split('/')[-1]}")


if __name__ == "__main__":
    main()
