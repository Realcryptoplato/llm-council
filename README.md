# LLM Council

> **Fork Note:** This is a fork of [karpathy/llm-council](https://github.com/karpathy/llm-council) with additional features. Original project by [Andrej Karpathy](https://github.com/karpathy).

![llmcouncil](header.jpg)

Instead of asking a question to a single LLM, group them into your "LLM Council". This repo queries multiple frontier LLMs, has them review and rank each other's work anonymously, and synthesizes a final response from a Chairman LLM.

## How It Works

1. **Stage 1: First opinions** - All LLMs answer independently
2. **Stage 2: Peer review** - Each LLM ranks the others (anonymized to prevent bias)
3. **Stage 3: Synthesis** - Chairman LLM compiles the final answer

---

## Quick Start (CLI - No Server Required)

The simplest way to use the council is the standalone CLI script.

### 1. Clone and Configure

```bash
git clone https://github.com/Realcryptoplato/llm-council.git ~/repos/llm-council
cd ~/repos/llm-council

# Add your OpenRouter API key
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env
```

Get your API key at [openrouter.ai/keys](https://openrouter.ai/keys).

### 2. Run a Query

```bash
python council_cli.py "What is the best database for real-time apps?"
```

That's it! No server, no dependencies to install (just Python 3.10+ and httpx).

### Cost Tiers

```bash
# Budget (~$0.05/query) - uses mini/flash models
python council_cli.py --tier budget "Your question"

# Balanced (~$0.15/query) - default, good quality
python council_cli.py --tier balanced "Your question"

# Premium (~$1.50/query) - best models (expensive!)
python council_cli.py --tier premium "Your question"
```

| Tier | Cost | Models |
|------|------|--------|
| budget | ~$0.05 | gpt-4o-mini, claude-3.5-sonnet, gemini-flash, grok-4.1-fast |
| balanced | ~$0.15 | gpt-5.2, claude-sonnet-4.5, gemini-3-pro, grok-4.1-fast |
| premium | ~$1.50 | gpt-5.2-pro, claude-opus-4.5, gemini-3-pro, grok-4 |

### CLI Options

```bash
python council_cli.py --help
python council_cli.py --models          # Show available models
python council_cli.py --json "Question" # Output as JSON
```

---

## Claude Code Integration

Use the council directly from Claude Code with slash commands:

```bash
/council What's the best approach to implement caching?
/council-issue https://github.com/owner/repo/issues/123
```

### Install Commands

Copy the command files to your Claude Code config:

```bash
mkdir -p ~/.claude/commands
cp docs/commands/*.md ~/.claude/commands/
```

Or manually create them - see the `docs/commands/` directory for templates.

---

## Web UI (Optional)

For a visual interface with conversation history:

### Setup

```bash
# Install dependencies
uv sync                    # Python backend
cd frontend && npm install # React frontend

# Configure
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
```

### Run

```bash
./start.sh
# Or manually:
# Terminal 1: uv run python -m backend.main
# Terminal 2: cd frontend && npm run dev
```

Open http://localhost:5173

---

## API Server (Optional)

For programmatic access via HTTP:

```bash
uv run python -m backend.main  # Starts on port 8001
```

### Endpoints

```bash
# Health check
curl http://localhost:8001/

# Current models
curl http://localhost:8001/api/models

# Query the council
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question here"}'

# With full details
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "include_details": true}'
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | Your OpenRouter API key |
| `USE_BUDGET_MODELS` | `balanced` | Cost tier: `budget`, `balanced`, `premium` |
| `USE_DYNAMIC_MODELS` | `true` | Auto-fetch latest models from OpenRouter |

### Example `.env`

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
USE_BUDGET_MODELS=balanced
```

---

## Tech Stack

- **CLI:** Python 3.10+, httpx (async HTTP)
- **Backend:** FastAPI, async httpx, OpenRouter API
- **Frontend:** React + Vite, react-markdown
- **Storage:** JSON files in `data/conversations/`

---

## Vibe Code Alert

> *From the original author:*
>
> This project was 99% vibe coded as a fun Saturday hack because I wanted to explore and evaluate a number of LLMs side by side. It's nice and useful to see multiple responses side by side, and also the cross-opinions of all LLMs on each other's outputs. Code is ephemeral now and libraries are over, ask your LLM to change it in whatever way you like.

---

## License

This project inherits from the original [karpathy/llm-council](https://github.com/karpathy/llm-council) which did not specify a license. Use at your own discretion.
