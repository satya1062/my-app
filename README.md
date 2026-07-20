# Custom Code Review AI Agent Using Claude API

An agentic code reviewer built on the Claude API that intelligently reviews git diffs using tool-use. It reads a git diff, uses tools to explore the surrounding codebase when needed, and returns structured JSON findings.

This project integrates the AI code review agent into a Next.js application for end-to-end implementation and UI visualization.

## Tech Stack

**Backend:**
- **Python** (63.9%) — Core agent logic and tools
- **TypeScript** (16.9%) — Next.js backend and type safety
- **CSS** (16.7%) — UI styling
- **JavaScript** (2.5%) — Frontend components

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+ (for Next.js UI)
- Anthropic API key

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=your-key-here

# Install Node dependencies (for UI)
npm install
```

## Quick Start

### Run Agent Locally

```bash
# Review current branch against main
python agent.py main

# Review against a different base branch
python agent.py develop
```

### Run Next.js UI

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to access the UI.

## How It Works

### Core Components

- **`agent.py`** — The agentic loop. Sends the diff to Claude with tool schemas attached. Claude decides whether to call a tool (e.g., read a file to see full function context) or return its final JSON verdict. This repeats until Claude stops calling tools or `MAX_TURNS` is reached.

- **`tools.py`** — Agent tool functions including:
  - `read_file` — Read file contents
  - `list_directory` — List directory contents
  - `search_codebase` — Search for patterns in the codebase
  - `get_diff` — Pull the git diff

- **`github_reporter.py`** — Posts code review findings as GitHub PR comments and annotations

- **Next.js App** (`app/` directory) — Web UI for visualizing and managing code reviews

## Output Format

The agent returns structured JSON findings:

```json
{
  "summary": "1-3 sentence overall assessment",
  "verdict": "approve | request_changes | comment",
  "findings": [
    {
      "file": "path/to/file",
      "line": 42,
      "severity": "critical | warning | suggestion",
      "comment": "explanation of the issue and suggested fix"
    }
  ]
}
```

## Extending the Agent

### Add More Tools
1. Add a function to `tools.py`
2. Describe it in `TOOL_SCHEMAS`
3. Register it in `DISPATCH`

Good additions:
- Run the test suite
- Run linter/type-checker
- Fetch PR description
- Check code coverage

### Customize Output
Modify the JSON shape in `SYSTEM_PROMPT` to match your needs (e.g., GitHub PR comment format).

### Post Results to GitHub
Use the `gh` CLI or GitHub API from `agent.py` after `run_review()` to post `findings` as inline PR comments instead of printing to stdout. See `github_reporter.py` for an example implementation.

### Control Cost & Latency
- Swap `MODEL` to a smaller model for a fast first pass
- Escalate to a larger model only for files above a complexity threshold

## CI/CD Integration

Move `.github-workflows-code-review.yml` to `.github/workflows/code-review.yml` in your repo:

```bash
mv .github-workflows-code-review.yml .github/workflows/code-review.yml
```

Then add `ANTHROPIC_API_KEY` as a repository secret in GitHub Settings.

The workflow will:
- Run on every PR
- Fail the check if the agent flags a `critical` finding
- Post inline comments with suggestions

## Project Structure

```
.
├── agent.py              # Main agentic loop
├── tools.py              # Tool implementations
├── github_reporter.py    # GitHub integration
├── requirements.txt      # Python dependencies
├── package.json          # Node.js dependencies
├── app/                  # Next.js application
│   ├── page.tsx
│   ├── layout.tsx
│   └── api/             # API routes for agent
├── public/              # Static assets
└── .github/
    └── workflows/       # CI/CD workflows
```

## Learning Resources

**Claude & Tool Use:**
- [Anthropic Claude API](https://www.anthropic.com/api) — Documentation and pricing

**Next.js:**
- [Next.js Documentation](https://nextjs.org/docs) — Learn about features and API
- [Learn Next.js](https://nextjs.org/learn) — Interactive tutorial

**Git & GitHub:**
- Review the workflow files in `.github/workflows/` for CI/CD examples

## Deployment

### Deploy to Vercel

The easiest way to deploy the Next.js app is using [Vercel](https://vercel.com):

1. Push this repo to GitHub
2. Create a new project on Vercel
3. Import this repository
4. Set `ANTHROPIC_API_KEY` as an environment variable
5. Deploy

See [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for detailed instructions.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source. Please see LICENSE for details.

## Support

For issues or questions:
- Check existing GitHub issues
- Review the code comments in `agent.py` and `tools.py`
- Consult the Anthropic API documentation
