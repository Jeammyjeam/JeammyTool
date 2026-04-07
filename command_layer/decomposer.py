"""
Decomposer: turns a user command into a list of executable steps.
Uses Claude to produce a structured task plan.
"""

import json
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a task decomposer for an AI command layer.
Given a user command, produce a minimal list of concrete steps to execute it.

Available step types:
- "github_fetch": fetches GitHub repo metadata and README. "input" must be "owner/repo".
- "analyze": sends data to an LLM for analysis. "input" is the analysis instruction.

Rules:
- Use the fewest steps needed to answer the command well.
- For GitHub repo analysis, always start with a "github_fetch" step.
- "analyze" steps may reference prior step results — state in "description" what context they use.
- Keep step IDs sequential: "step_1", "step_2", etc.
- "depends_on" is a list of step IDs this step needs to run first.

Output ONLY a valid JSON array. No markdown, no explanation."""


def decompose(command: str) -> list[dict]:
    """Break a command into an ordered list of executable steps."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Command: {command}"}],
    )

    text = next(b.text for b in response.content if b.type == "text")
    steps = json.loads(text)
    return steps
