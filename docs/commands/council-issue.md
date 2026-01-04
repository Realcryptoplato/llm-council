---
description: Send a GitHub issue to the LLM Council for deliberation and post the synthesized response as a comment
argument-hint: [issue-url or owner/repo#number]
allowed-tools: Bash
---

Send a GitHub issue to the LLM Council for multi-model deliberation, then post the council's synthesized answer as a comment.

**No server required** - uses standalone CLI script.

## Instructions

1. **Parse the issue reference** from $ARGUMENTS:
   - Full URL: `https://github.com/owner/repo/issues/123`
   - Short form: `owner/repo#123`

2. **Check for council CLI**:
   ```bash
   test -f ~/repos/llm-council/council_cli.py && echo "Found" || echo "Not found"
   ```
   If not found, tell user to install and STOP.

3. **Fetch the GitHub issue**:
   ```bash
   gh issue view <number> --repo <owner/repo> --json title,body,comments,state
   ```

4. **Display the issue summary** to user.

5. **Build the council prompt**:
   ```
   Please analyze this GitHub issue and provide a well-reasoned response:

   **Issue Title:** [title]

   **Issue Description:**
   [body]

   Please provide:
   1. Analysis of the issue/request
   2. Recommended approach or solution
   3. Any concerns or considerations
   4. Suggested next steps
   ```

6. **Query the council** using CLI:
   ```bash
   cd ~/repos/llm-council && python council_cli.py --json "THE_PROMPT_HERE"
   ```

7. **Parse the JSON response** and extract the `answer` field.

8. **Show the response to user** and ask for confirmation before posting.

9. **Post as GitHub comment** (after user confirms):
   ```bash
   gh issue comment <number> --repo <owner/repo> --body "## LLM Council Analysis

   *Council: gpt-5.2, claude-sonnet-4.5, gemini-3-pro, grok-4.1-fast*

   [answer]

   ---
   *Deliberated by 4 AI models with anonymous peer review.*"
   ```

10. **Confirm success** with link to comment.

## Issue Reference

$ARGUMENTS
