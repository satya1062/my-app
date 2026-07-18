"""
Core code review agent: an agentic loop over the Claude Messages API.

Usage:
    python agent.py [base_ref]
"""

import json
import sys
import anthropic
from tools import TOOL_SCHEMAS, DISPATCH, get_diff

MODEL = "claude-sonnet-5"          # good default: strong reasoning, cost-effective
MAX_TURNS = 8                       # cap on tool-use round trips, avoid runaway loops

SYSTEM_PROMPT = """You are a senior code reviewer. You will be given a git diff.

Your job:
1. Review the diff for bugs, security issues, performance problems, and
   style/consistency issues with the rest of the codebase.
2. Use the available tools when the diff alone isn't enough context —
   e.g. read a file to see the full function, or search for other callers
   before flagging something as unused or breaking.
3. Don't nitpick trivial style points unless they violate an explicit
   convention you can see in the codebase.
4. When you're done investigating, respond with ONLY a JSON object
   (no markdown fences, no prose) matching this shape:

{
  "summary": "1-3 sentence overall assessment",
  "verdict": "approve" | "request_changes" | "comment",
  "findings": [
    {
      "file": "path/to/file",
      "line": 42,
      "severity": "critical" | "warning" | "suggestion",
      "comment": "explanation of the issue and suggested fix"
    }
  ]
}

Emit that JSON as your final message once you have enough information —
do not keep calling tools after you're confident in your findings.
"""


def run_review(base_ref: str = "main") -> dict:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    diff = get_diff(base_ref)
    if diff.strip() == "(no diff found)":
        return {"summary": "No changes to review.", "verdict": "approve", "findings": []}

    messages = [
        {"role": "user", "content": f"Review this diff:\n\n```diff\n{diff}\n```"}
    ]

    for turn in range(MAX_TURNS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Did the model ask to use a tool?
        tool_calls = [b for b in response.content if b.type == "tool_use"]

        if not tool_calls:
            # Final answer — extract the JSON text block
            text = "".join(b.text for b in response.content if b.type == "text")
            return _parse_json_response(text)

        # Otherwise, run each requested tool and feed results back
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for call in tool_calls:
            fn = DISPATCH.get(call.name)
            result = fn(call.input) if fn else f"ERROR: unknown tool {call.name}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": result,
            })
        messages.append({"role": "user", "content": tool_results})

    return {"summary": "Review incomplete: exceeded max tool-use turns.",
            "verdict": "comment", "findings": []}


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"summary": text, "verdict": "comment", "findings": []}


def print_report(report: dict):
    print(f"\n=== Code Review: {report.get('verdict', 'unknown').upper()} ===")
    print(report.get("summary", ""))
    for f in report.get("findings", []):
        print(f"\n[{f.get('severity', '?').upper()}] {f.get('file')}:{f.get('line')}")
        print(f"  {f.get('comment')}")


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    report = run_review(base)
    print_report(report)
    # Non-zero exit code on critical findings — useful for CI gating
    if any(f.get("severity") == "critical" for f in report.get("findings", [])):
        sys.exit(1)