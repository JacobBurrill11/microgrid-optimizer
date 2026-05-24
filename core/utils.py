import json
import re


def parse_json_response(text: str) -> dict:
    """Parse JSON from an LLM response that may be wrapped in markdown code blocks."""
    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    return json.loads(text.strip())
