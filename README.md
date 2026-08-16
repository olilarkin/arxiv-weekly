# Audio AI Weekly — Automatic Updater

A weekly pipeline that pulls papers from arXiv (`cs.SD` / `eess.AS`) every Friday,
analyzes them with Google Gemini, and publishes the results to GitHub
Pages.

## Topics covered
- Audio foundation models
- Source separation
- Music transcription & beat tracking

## Setup

### 1. Repository configuration
```bash
# Enable GitHub Pages:
# Settings -> Pages -> Source: Deploy from a branch -> gh-pages

# Add the AI provider key (required — the pipeline fails without it):
gh secret set GEMINI_API_KEY   # key from https://aistudio.google.com/apikey
```

### 2. Launch the development environment in DevContainer
Open the repository in VS Code and choose "Reopen in Container".

### 3. Smoke-test the pipeline
```bash
python scripts/test_connection.py        # Check AI provider connectivity.
python scripts/fetch_papers.py --dry-run # Test arXiv fetching.
```

### 4. Run manually
GitHub Actions tab -> Weekly arXiv Update -> Run workflow.

## Switching AI provider
`config/settings.yaml` selects the provider under `ai.provider`, and each
provider has its own block naming the endpoint, model and API-key environment
variable. Any OpenAI-compatible provider can be added the same way.

Note: the `github_models` block is kept for reference only — GitHub Models has
been retired and its endpoint now returns HTTP 410.

## Adding or removing keywords
Edit the `include` list in `config/keywords.yaml`. No code changes required.

## Project layout
```
.devcontainer/     # DevContainer config
.github/workflows/ # GitHub Actions workflows
config/
  keywords.yaml    # Filter keywords (editable)
  settings.yaml    # System settings
data/
  index.json       # Index of all weeks
  latest.json      # Latest week data
  weekly/          # Weekly JSON files (YYYY-MMDD.json)
scripts/
  fetch_papers.py    # Fetch from arXiv
  analyze_papers.py  # Analyze via the configured AI provider
  build_data.py      # Build data and update index
  test_connection.py # Connectivity smoke test
web/                 # React frontend
requirements.txt
```
