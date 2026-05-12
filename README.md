# Audio AI Weekly — Automatic Updater

A weekly pipeline that pulls papers from arXiv (`cs.SD` / `eess.AS`) every Friday,
analyzes them with GitHub Models (GPT-4o), and publishes the results to GitHub
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
```

### 2. Launch the development environment in DevContainer
Open the repository in VS Code and choose "Reopen in Container".

### 3. Smoke-test the pipeline
```bash
python scripts/test_connection.py        # Check GitHub Models connectivity.
python scripts/fetch_papers.py --dry-run # Test arXiv fetching.
```

### 4. Run manually
GitHub Actions tab -> Weekly arXiv Update -> Run workflow.

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
  analyze_papers.py  # Analyze via GitHub Models
  build_data.py      # Build data and update index
  test_connection.py # Connectivity smoke test
web/                 # React frontend
requirements.txt
```
