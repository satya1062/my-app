This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

# Custom Code Review Agent

An agentic code reviewer built on the Claude API. It reads a git diff, uses
tools to explore the surrounding codebase when needed, and returns
structured JSON findings.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
```

## Run locally

```bash
python agent.py main          # reviews current branch against `main`
```

## How it works

- `tools.py` — the functions the agent can call: `read_file`,
  `list_directory`, `search_codebase`, plus `get_diff` to pull the git diff.
- `agent.py` — the loop. It sends the diff to Claude with the tool schemas
  attached. Claude decides whether to call a tool (e.g. read a file to see
  full function context) or return its final JSON verdict. This repeats
  until Claude stops calling tools or `MAX_TURNS` is hit.

## Extending it

- **More tools**: add a function to `tools.py`, describe it in
  `TOOL_SCHEMAS`, and register it in `DISPATCH`. Good next additions: run
  the test suite, run a linter/type-checker, fetch the PR description.
- **Different output**: change the JSON shape in `SYSTEM_PROMPT` to match
  whatever consumes it (e.g. GitHub PR comment format).
- **Post results to GitHub**: use the `gh` CLI or GitHub API from
  `agent.py` after `run_review()` to post `findings` as inline PR comments
  instead of printing to stdout.
- **Cost/latency control**: swap `MODEL` to a smaller model for a fast
  first pass, and only escalate to a larger model for files above some
  complexity threshold.

## CI integration

Move `.github-workflows-code-review.yml` to `.github/workflows/code-review.yml`
in your repo and add `ANTHROPIC_API_KEY` as a repository secret. It will run
on every PR and fail the check if the agent flags a `critical` finding.
