---
description: Query the LLM Council for consensus answers from multiple AI models (dynamically selected frontier models)
argument-hint: [question]
allowed-tools: Bash
---

Query the LLM Council for a well-considered answer synthesized from multiple frontier AI models through deliberation and peer review.

**No server required** - uses standalone CLI script.

## Instructions

1. **Check for the council CLI script**:
   ```bash
   test -f ~/repos/llm-council/council_cli.py && echo "Found" || echo "Not found"
   ```

2. **If not found**, tell the user:
   ```
   The LLM Council CLI is not installed. To install:

   git clone https://github.com/Realcryptoplato/llm-council.git ~/repos/llm-council

   Then add your OpenRouter API key to ~/repos/llm-council/.env:
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
   Then STOP.

3. **Check for API key**:
   ```bash
   grep -q OPENROUTER_API_KEY ~/repos/llm-council/.env 2>/dev/null && echo "Key configured" || echo "No key"
   ```
   If no key, tell user to add it and STOP.

4. **Run the council CLI**:
   ```bash
   cd ~/repos/llm-council && python council_cli.py "THE_USER_QUESTION_HERE"
   ```

   For budget mode (cheaper):
   ```bash
   cd ~/repos/llm-council && python council_cli.py --tier budget "THE_USER_QUESTION_HERE"
   ```

   The script will:
   - Show which models are being used
   - Display progress for each stage
   - Output the synthesized answer

5. **Present the answer** to the user. The CLI output is already well-formatted.

## Tiers

| Tier | Cost/Query | Models |
|------|-----------|--------|
| budget | ~$0.05 | gpt-4o-mini, claude-3.5-sonnet, gemini-flash, grok-4.1-fast |
| balanced | ~$0.15 | gpt-5.2, claude-sonnet-4.5, gemini-3-pro, grok-4.1-fast |
| premium | ~$1.50 | gpt-5.2-pro, claude-opus-4.5, gemini-3-pro, grok-4 |

## Question

$ARGUMENTS
