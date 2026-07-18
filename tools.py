"""
Tool implementations for the code review agent.
Each tool is a plain Python function; TOOL_SCHEMAS describes them to Claude
in the format the Messages API expects.
"""

import subprocess
import os

REPO_ROOT = os.getcwd()


def get_diff(base_ref: str = "main") -> str:
    """Return the git diff between the current branch and base_ref."""
    result = subprocess.run(
        ["git", "diff", f"{base_ref}...HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    return result.stdout or "(no diff found)"


def read_file(path: str) -> str:
    """Read a file's full contents, with line numbers, so the agent has context
    beyond just the changed lines."""
    full_path = os.path.join(REPO_ROOT, path)
    if not os.path.isfile(full_path):
        return f"ERROR: {path} does not exist"
    with open(full_path, "r", errors="replace") as f:
        lines = f.readlines()
    numbered = "".join(f"{i+1:>5}  {line}" for i, line in enumerate(lines))
    return numbered[:20000]  # guard against huge files blowing up context


def list_directory(path: str = ".") -> str:
    """List files in a directory (non-recursive) so the agent can orient itself."""
    full_path = os.path.join(REPO_ROOT, path)
    if not os.path.isdir(full_path):
        return f"ERROR: {path} is not a directory"
    entries = sorted(os.listdir(full_path))
    return "\n".join(entries)


def search_codebase(pattern: str) -> str:
    """Grep the repo for a pattern, e.g. to check if a function is used elsewhere."""
    result = subprocess.run(
        ["grep", "-rn", "--exclude-dir=.git", "--exclude-dir=node_modules", pattern, "."],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    output = result.stdout.strip()
    return output[:5000] if output else "(no matches)"


# JSON schemas describing these tools to Claude
TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read the full contents of a file in the repository, with line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Repo-relative file path"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files/folders in a directory to understand project structure.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Repo-relative directory path, default '.'"}},
        },
    },
    {
        "name": "search_codebase",
        "description": "Grep the repository for a string or regex pattern, e.g. to find callers of a function.",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string", "description": "Pattern to search for"}},
            "required": ["pattern"],
        },
    },
]

DISPATCH = {
    "read_file": lambda inp: read_file(inp["path"]),
    "list_directory": lambda inp: list_directory(inp.get("path", ".")),
    "search_codebase": lambda inp: search_codebase(inp["pattern"]),
}