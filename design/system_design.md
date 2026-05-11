# Audio AI Weekly — Automated Update System
## Requirements and Architecture Design

**Version:** v1.3 — **Date:** 2026-04-25 — **Author:** Claude Sonnet 4.6

---

### Revision history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-25 | Initial draft |
| 1.1 | 2026-04-25 | Reflected four requirement changes (keyword management, 50-paper cap, GitHub Models, historical data retention) |
| 1.2 | 2026-04-25 | Added the development environment (DevContainer) section |
| 1.3 | 2026-04-25 | Switched the JSON filename convention to `YYYY-MMDD` |

> ★ marks changes from earlier versions.

---

## 1. Project overview

This document captures the requirements and architectural design for a web
system that weekly fetches, analyzes, and publishes the latest papers in the
audio and acoustics domain (arXiv `cs.SD` / `eess.AS`) on GitHub Pages.

### 1.1 Background and goals

- Over 100 papers per week are posted to arXiv `cs.SD` / `eess.AS`; manual
  triage is infeasible.
- This system produces a weekly summary focused on three areas: audio
  foundation models, source separation, and anomalous sound detection.
- It uses the Claude/GPT-4o models exposed by GitHub Models to generate
  six-angle structured summaries.
- All historical weekly data is retained and browsable from the UI.

### 1.2 System name

ArXiv Audio AI Weekly — Automated Update System.

### 1.3 Target users

- Researchers and engineers in audio / acoustics AI.
- Practitioners interested in audio foundation models, source separation, or
  anomalous sound detection.

---

## 2. Requirements

### 2.1 Functional requirements

#### 2.1.1 Paper collection

- Fetch new submissions from the last 7 days for `cs.SD` and `eess.AS`
  categories via the arXiv API (export.arxiv.org).
- ★ The keyword list is managed in `config/keywords.yaml`. Adding or removing
  keywords requires no code changes.
- ★ The maximum number of papers kept after filtering is **50** (configurable).
- Cross-listed duplicates are deduplicated by arXiv ID.
- Keywords are applied with OR semantics over title and abstract.

#### 2.1.2 Paper analysis and summarization

- ★ Uses GitHub Models (endpoint `models.inference.ai.azure.com`),
  authenticated with `GITHUB_TOKEN`.
- Each abstract is analyzed and structured into six angles in English:
  - ① What it is
  - ② Novelty vs prior work
  - ③ Core method
  - ④ Validation
  - ⑤ Discussion and limits
  - ⑥ Recommended reads (with arXiv links)
- A three-line weekly technical trend summary is also generated.

> **Change (v1.1):** Migrated from `Anthropic Claude API + ANTHROPIC_API_KEY`
> to `GitHub Models + GITHUB_TOKEN`. No external secrets are required.

#### 2.1.3 Data persistence

- ★ Analysis results are never overwritten; one file is written per week
  (`data/weekly/YYYY-MMDD.json`).
- ★ A `data/index.json` is automatically generated and updated to track all
  weeks.
- `data/latest.json` serves as a pointer to the most recent week (a file copy).
- Weekly files accumulate in Git and are retained indefinitely.

> **Change (v1.1):** Switched from overwriting `latest.json` to writing new
> weekly files plus an index, so historical data is preserved.

#### 2.1.4 Web page generation and publishing

- A static site built with React + Vite is published on GitHub Pages.
- The UI follows the existing Artifact design (dark theme, accordion cards).
- ★ A week selector lets users browse any past week.
- The latest week is shown by default.

#### 2.1.5 Scheduling

- A GitHub Actions cron triggers the pipeline **every Friday at 12:00 UTC
  (21:00 JST)**.
- A `workflow_dispatch` manual trigger is also supported.
- Run logs are retained as GitHub Actions Artifacts for 30 days.

---

### 2.2 Non-functional requirements

| Item | Requirement | Notes |
|---|---|---|
| Availability | Subject to GitHub Pages SLA (≥99.9% monthly) | |
| Runtime | Each GitHub Actions job completes within 30 minutes | Accounts for analyzing 50 papers |
| Cost | ★ Free in practice via GitHub Models | Stays within GitHub Pro / Team plan limits |
| Security | ★ Uses only `GITHUB_TOKEN`; no external keys | Token is issued automatically by Actions |
| Maintainability | All scripts and configs are version controlled | |
| Extensibility | ★ Keywords can be added/removed via config | No code changes needed |
| Retention | ★ Weekly JSONs are never deleted or overwritten | Recoverable from Git history |

### 2.3 Constraints

- Respect arXiv's terms of use; do not exceed 3 req/sec.
- Respect GitHub Models' rate limits and terms.
- Run within the GitHub Actions free tier (2,000 minutes/month). Weekly
  execution typically consumes ~120-180 minutes/month.
- Do not reproduce figures or full text from papers; only abstracts are used.
- Keep each weekly JSON file under ~500 KB to limit repository growth.

---

## 3. Architecture

### 3.1 System overview

The system has two layers — a data collection/analysis pipeline and a static
web frontend — and stays within the GitHub ecosystem.

> External dependencies are limited to the arXiv API and GitHub Models. Since
> GitHub Models authenticates with `GITHUB_TOKEN`, no external secret
> management is needed.

| Layer | Component | Stack |
|---|---|---|
| Scheduler | Weekly cron | GitHub Actions (cron) |
| Data collection | arXiv API client | Python 3.11 + requests |
| AI analysis | ★ GitHub Models client | ★ OpenAI SDK (pointed at GitHub Models) |
| Persistence | ★ Weekly JSONs committed to Git | ★ `data/weekly/YYYY-MMDD.json` (immutable) |
| Index management | ★ Automated all-week index | ★ `data/index.json` |
| Frontend | Static React app | React 18 + Vite |
| Hosting | Static site | GitHub Pages |

---

### 3.2 GitHub Models integration

| Item | Value |
|---|---|
| Endpoint | `https://models.inference.ai.azure.com` |
| Auth | `Authorization: Bearer $GITHUB_TOKEN` |
| Model | `gpt-4o` (configurable in `settings.yaml`) |
| SDK | `openai` Python package with `base_url` pointed at GitHub Models |
| Rate limits | GitHub Pro: 50 req/day, 10 req/min |
| Cost | Included with GitHub Pro / Team / Enterprise |

> `GITHUB_TOKEN` is automatically issued by GitHub Actions; admins do not need
> to add it to repository Secrets.

---

### 3.3 Repository layout

```
arxiv-weekly/
├── .devcontainer/
│   └── devcontainer.json       # Python 3.11 base image + features + first-time setup
├── .github/
│   └── workflows/
│       └── update.yml          # GitHub Actions workflow
├── config/
│   ├── keywords.yaml           # ★ Filter keywords (edit here only)
│   └── settings.yaml           # System settings (max_papers=50, etc.)
├── data/
│   ├── index.json              # ★ All-week index
│   ├── latest.json             # Copy of the most recent week
│   └── weekly/
│       └── YYYY-MMDD.json      # ★ Weekly paper data (immutable)
├── scripts/
│   ├── fetch_papers.py         # Fetch / filter / categorize from arXiv
│   ├── analyze_papers.py       # Six-angle analysis via GitHub Models
│   ├── build_data.py           # Build weekly JSON / update index
│   └── test_connection.py      # GitHub Models connectivity check
├── web/
│   ├── public/data/            # Data copied at build time
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── WeekSelector.jsx
│   │       ├── CategoryFilter.jsx
│   │       ├── PaperCard.jsx
│   │       └── TrendSummary.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── requirements.txt            # openai, pyyaml
└── README.md
```

---

### 3.4 Config file specification

#### 3.4.1 config/keywords.yaml

| Field | Type | Description |
|---|---|---|
| `include` | `string[]` | Filter keywords (OR semantics). Matched against title and abstract. |
| `exclude` | `string[]` | Optional exclusion keywords. |
| `categories` | `string[]` | Target arXiv categories (e.g. cs.SD, eess.AS). |
| `ui_categories` | `object[]` | UI category definitions (id / label / color / keywords). |

> Example: to track anomalous sound detection, simply add `'anomalous sound'`
> to `include`.

#### 3.4.2 config/settings.yaml

| Field | Type | Default | Description |
|---|---|---|---|
| `max_papers` | int | `50` | ★ Maximum papers after filtering |
| `lookback_days` | int | `7` | Number of days of recent papers to consider |
| `model` | string | `gpt-4o` | ★ GitHub Models model name |
| `retry_max` | int | `3` | Maximum retries on API errors |
| `request_interval` | float | `1.0` | Delay between arXiv API requests (seconds) |

---

### 3.5 Data flow

#### Step 1 — Fetch papers (`fetch_papers.py`)

1. GET the arXiv API with the query `cat:cs.SD OR cat:eess.AS` for the past 7
   days.
2. Parse the Atom XML and extract title, ID, date, authors, and abstract.
3. Apply OR-filter using the include keywords from `config/keywords.yaml`.
4. ★ Cap the result at 50 papers and save to `data/raw_papers.json`.

#### Step 2 — AI analysis (`analyze_papers.py`)

1. ★ Send requests to GitHub Models via the OpenAI SDK, authenticated with
   `GITHUB_TOKEN`.
2. Read `raw_papers.json` and ask the model to return a six-angle JSON for each
   abstract.
3. Parse responses and write `analyzed_papers.json`.
4. Retry on API errors (up to 3 attempts, exponential backoff).

#### Step 3 — Build data and commit (`build_data.py`)

1. ★ Write a new file at `data/weekly/YYYY-MMDD.json` using the run date.
2. ★ Skip if the file already exists (idempotency for same-day reruns).
3. ★ Update `data/index.json` with date, file path, paper count, and timestamp.
4. Copy the latest week to `data/latest.json`.
5. Commit and push all changes.

#### Step 4 — Build frontend and deploy

1. Run `npm ci && npm run build` in `web/`.
2. ★ The frontend fetches `data/index.json` at startup to build the week list.
3. ★ The latest week (`data/latest.json`) is shown by default; the week
   selector switches to any other week.
4. Deploy `web/dist/` to GitHub Pages (`gh-pages` branch).

---

### 3.6 GitHub Actions workflow

| Job | Description | Token | Depends on |
|---|---|---|---|
| `fetch` | Fetch papers from arXiv | None | — |
| `analyze` | ★ Six-angle analysis via GitHub Models | ★ `GITHUB_TOKEN` | fetch |
| `build` | ★ Build weekly JSON / update index / push | `GITHUB_TOKEN` | analyze |
| `deploy` | Vite build → GitHub Pages | `GITHUB_TOKEN` | build |

> Granting `permissions: contents: write` to the workflow enables pushing.

---

### 3.7 Frontend design

#### 3.7.1 Components

| Component | Role |
|---|---|
| `App.jsx` | Data fetching; week selector and filter state |
| `Header.jsx` | Title, date, paper count |
| `WeekSelector.jsx` | ★ Week dropdown built from `index.json` |
| `CategoryFilter.jsx` | Category tabs (All / Foundation Models / Source Separation / Anomalous Sound Detection) |
| `PaperCard.jsx` | Paper card. Clicking the header expands the six-angle view. |
| `TrendSummary.jsx` | Three-line weekly trend summary |

#### 3.7.2 Data flow

1. On startup, fetch `data/index.json` and pass the week list to `WeekSelector`.
2. Initial render: fetch `data/latest.json` and render the latest week.
3. ★ On week change: fetch `data/weekly/YYYY-MMDD.json` and render that week.

---

### 3.8 Data schemas

#### data/index.json

```json
{
  "weeks": [
    {
      "date": "2026-0425",
      "file": "weekly/2026-0425.json",
      "count": 42,
      "generated_at": "2026-04-25T12:00:00Z"
    }
  ],
  "generated_at": "2026-04-25T12:05:00Z"
}
```

#### data/weekly/YYYY-MMDD.json

```json
{
  "date": "2026-0425",
  "generated_at": "2026-04-25T12:00:00Z",
  "total": 42,
  "categories": [
    {
      "id": "foundation",
      "label": "Audio Foundation Models",
      "color": "#38bdf8",
      "papers": [
        {
          "id": "2604.10905",
          "date": "Apr 15",
          "title": "...",
          "org": "NVIDIA / UMD",
          "url": "https://arxiv.org/abs/2604.10905",
          "what": "...",
          "novel": "...",
          "method": "...",
          "validation": "...",
          "discussion": "...",
          "nextReads": [
            { "label": "Qwen-Audio (2023)", "url": "https://arxiv.org/abs/2311.07919" }
          ]
        }
      ]
    }
  ],
  "trend": [
    "Audio foundation models advanced ...",
    "Source separation accuracy improved ...",
    "Anomalous sound detection ..."
  ]
}
```

---

### 3.9 Security

| Surface | Mitigation |
|---|---|
| ★ GitHub Models auth | ★ Uses `GITHUB_TOKEN` (auto-issued by Actions); no external keys |
| GitHub token scope | Grant only `contents: write` (principle of least privilege) |
| arXiv API | No auth required; sets a descriptive User-Agent |
| Frontend | Static site, no API endpoints; React's default escaping mitigates XSS |
| Weekly-JSON tampering | Git history tracks every change; same-day reruns are skipped |

---

## 4. Development environment (DevContainer)

### 4.1 Problems the DevContainer solves

| Problem | Solution |
|---|---|
| Python / Node version drift | Pinned versions inside the container; host independent |
| Connectivity to arXiv / GitHub Models | Run scripts directly from the container |
| Diverging local vs CI envs | Same Ubuntu base image as CI |
| Dependency conflicts | A venv lives inside the container; no global pollution |
| Onboarding time for new contributors | "Reopen in Container" and you're done |

### 4.2 Container spec

| Item | Spec |
|---|---|
| Base image | `mcr.microsoft.com/devcontainers/python:3.11-bullseye` |
| Python | 3.11 (pinned in container) |
| Node.js | 20.x LTS (via nvm) |
| GitHub CLI | Pre-installed (for testing GitHub Models) |

### 4.3 VS Code extensions (auto-installed)

| Extension | Purpose |
|---|---|
| `ms-python.python` | Python completion / debugging |
| `charliermarsh.ruff` | Python linter / formatter |
| `esbenp.prettier-vscode` | TypeScript / JSX formatting |
| `GitHub.copilot` | AI code completion |
| `GitHub.vscode-github-actions` | workflow.yml syntax check |
| `redhat.vscode-yaml` | `config/*.yaml` editing |

### 4.4 Environment checklist

```bash
python --version                              # Python 3.11.x
node --version                                # v20.x.x
gh auth status                                # Logged in to github.com
python scripts/test_connection.py             # GitHub Models connectivity
python scripts/fetch_papers.py --dry-run      # arXiv fetch test
cd web && npm run dev                         # http://localhost:5173
```

---

## 5. Development roadmap

| Phase | Work | Estimate |
|---|---|---|
| Phase 1 | ★ Create repo, set up DevContainer, verify GitHub Pages | 1 day |
| Phase 2 | Implement arXiv fetcher, design `keywords.yaml`, unit tests | 0.5 day |
| Phase 3 | Implement GitHub Models analyzer and tune prompts (50-paper batch) | 1 day |
| Phase 4 | Implement weekly JSON / `index.json` builder | 0.5 day |
| Phase 5 | Implement GitHub Actions workflow and run E2E test | 1 day |
| Phase 6 | Build React frontend (add week selector UI) | 1 day |
| Phase 7 | Integration test and first production run | 0.5 day |

---

## 6. Tech stack

| Category | Library / Service | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.11 | All backend scripts |
| Language | TypeScript / React | 18.x | Frontend |
| ★ AI | ★ GitHub Models (GPT-4o) | — | ★ Paper analysis (auth via `GITHUB_TOKEN`) |
| ★ AI SDK | ★ openai (Python) | latest | ★ Client for GitHub Models |
| Build | Vite | 5.x | React app build |
| CI/CD | GitHub Actions | — | Scheduling and deploy |
| Hosting | GitHub Pages | — | Static hosting |
| ★ Dev env | ★ Dev Containers | — | Unified development env |
| ★ Dev env | ★ GitHub Codespaces | — | Browser-based development |

---

## 7. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| arXiv API spec change | Medium | Track official docs; OAI-PMH as fallback |
| ★ GitHub Models rate limit | Medium | ★ Sleep between calls; cap at 50 papers |
| ★ Model availability change | Medium | ★ Model name is in `settings.yaml`; easy swap |
| Repository size growth | Low | Keep each weekly JSON under 500 KB |
| Same-day rerun | Low | Skip when file already exists |
| GitHub Actions quota | Low | Operate within 2,000 min/month (~120-180/month usage) |

---

## 8. Glossary

| Term | Description |
|---|---|
| arXiv | Open-access preprint server operated by Cornell University |
| cs.SD | arXiv's Sound category |
| eess.AS | arXiv's Audio and Speech Processing category |
| GitHub Models | GitHub's AI model inference service, usable with `GITHUB_TOKEN` |
| `GITHUB_TOKEN` | Auto-issued repository-scoped access token in GitHub Actions |
| `YYYY-MMDD` | Filename convention used by this project (e.g. `2026-0425` = 2026-04-25) |
| GitHub Actions | GitHub's CI/CD platform |
| GitHub Pages | GitHub's static site hosting service |
| `workflow_dispatch` | GitHub Actions manual trigger |
| Vite | Fast JavaScript build tool |

---

*End (v1.3)*
