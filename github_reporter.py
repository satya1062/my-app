"""
Posts the agent's findings to GitHub as an inline PR review, using the
"Create a review for a pull request" endpoint — this lets us submit all
inline comments plus a summary in a single API call, and set an overall
review state (COMMENT / REQUEST_CHANGES / APPROVE).

Requires these env vars (all set automatically inside GitHub Actions,
except GITHUB_TOKEN which needs `permissions: pull-requests: write`):
    GITHUB_TOKEN        - auth token for the API call
    GITHUB_REPOSITORY   - "owner/repo"
    GITHUB_EVENT_PATH   - path to the JSON payload for the triggering event
"""

import json
import os
import requests

API_BASE = "https://api.github.com"

# Map our severity levels to a GitHub review state.
# "critical" anywhere -> block the PR. Otherwise just comment.
VERDICT_TO_STATE = {
    "approve": "APPROVE",
    "request_changes": "REQUEST_CHANGES",
    "comment": "COMMENT",
}


def _get_pr_context() -> dict:
    """Pull repo/PR/commit info out of the GitHub Actions event payload."""
    event_path = os.environ["GITHUB_EVENT_PATH"]
    with open(event_path) as f:
        event = json.load(f)

    pr = event.get("pull_request")
    if not pr:
        raise RuntimeError(
            "No pull_request found in event payload — this only works on "
            "pull_request-triggered workflow runs."
        )

    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    return {
        "owner": owner,
        "repo": repo,
        "pull_number": pr["number"],
        "commit_id": pr["head"]["sha"],  # head SHA, required by the reviews API
    }


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def post_review(report: dict) -> None:
    """Submit the agent's report as a single PR review with inline comments.

    Findings that reference a file/line become inline review comments.
    Findings without a resolvable line (e.g. general remarks) are folded
    into the top-level review body instead, since GitHub requires inline
    comments to anchor to a line in the diff.
    """
    ctx = _get_pr_context()

    inline_comments = []
    fallback_notes = []

    for finding in report.get("findings", []):
        path = finding.get("file")
        line = finding.get("line")
        severity = finding.get("severity", "suggestion")
        comment = finding.get("comment", "")
        label = {"critical": "🔴 Critical", "warning": "🟡 Warning", "suggestion": "🔵 Suggestion"}.get(
            severity, severity
        )
        body = f"**{label}**\n\n{comment}"

        if path and isinstance(line, int) and line > 0:
            inline_comments.append({
                "path": path,
                "line": line,
                "side": "RIGHT",   # comment on the new version of the file
                "body": body,
            })
        else:
            fallback_notes.append(f"- **{path or 'general'}**: {comment}")

    summary = report.get("summary", "")
    if fallback_notes:
        summary += "\n\n**Additional notes:**\n" + "\n".join(fallback_notes)

    payload = {
        "commit_id": ctx["commit_id"],
        "body": summary,
        "event": VERDICT_TO_STATE.get(report.get("verdict", "comment"), "COMMENT"),
        "comments": inline_comments,
    }

    url = f"{API_BASE}/repos/{ctx['owner']}/{ctx['repo']}/pulls/{ctx['pull_number']}/reviews"
    resp = requests.post(url, headers=_headers(), json=payload)

    if resp.status_code >= 300:
        # Inline comments can fail if a line isn't part of the diff (GitHub
        # rejects comments on unchanged lines). Fall back to a plain issue
        # comment with everything folded into the body so nothing is lost.
        _post_fallback_comment(ctx, report)
        print(f"Inline review failed ({resp.status_code}): {resp.text}\n"
              f"Posted a fallback summary comment instead.")
    else:
        print(f"Posted review with {len(inline_comments)} inline comment(s).")


def _post_fallback_comment(ctx: dict, report: dict) -> None:
    lines = [report.get("summary", ""), ""]
    for f in report.get("findings", []):
        lines.append(
            f"- **[{f.get('severity', '?').upper()}] {f.get('file')}:{f.get('line')}** — {f.get('comment')}"
        )
    body = "\n".join(lines)

    url = f"{API_BASE}/repos/{ctx['owner']}/{ctx['repo']}/issues/{ctx['pull_number']}/comments"
    requests.post(url, headers=_headers(), json={"body": body})
