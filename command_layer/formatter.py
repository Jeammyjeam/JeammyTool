"""
Formatter: synthesizes all step results into a clean final answer.
"""

import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a result synthesizer for an AI command layer.
Given an original command and the results of all execution steps, produce a clean,
well-structured final answer in markdown.

Be direct and useful. Lead with the answer, support it with evidence from the results.
Use headers, bullet points, and a final verdict/summary where appropriate."""


def format_result(command: str, steps: list[dict], results: dict) -> str:
    """Synthesize step results into a clean final answer."""
    steps_text = ""
    for step in steps:
        step_id = step["id"]
        result = results.get(step_id, "no result")
        # Truncate very long results for the synthesis prompt
        truncated = result[:2000] + ("..." if len(result) > 2000 else "")
        steps_text += f"\n\n### {step_id}: {step['description']}\n{truncated}"

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Original command: {command}\n\n"
                    f"Execution results:{steps_text}\n\n"
                    f"Provide the final answer to the command."
                ),
            }
        ],
    )
    return next(b.text for b in response.content if b.type == "text")
