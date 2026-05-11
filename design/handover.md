# Handover to GitHub Copilot
## Audio AI Weekly — Automated Update System

**Date:** 2026-04-25 — **From:** Claude Sonnet 4.6 — **To:** GitHub Copilot

---

| ✅ Done | ☐ Remaining |
|---|---|
| Design, implementation, commits | GitHub setup, testing, debugging |

---

## 1. Project overview

| Item | Description |
|---|---|
| Project | Audio AI Weekly — Automated Update System |
| Scope | Audio foundation models, source separation, anomalous sound detection |
| Cadence | Every Friday at 12:00 UTC (GitHub Actions cron) |
| AI engine | GitHub Models (GPT-4o) / `GITHUB_TOKEN` auth |
| Frontend | React 18 + Vite served on GitHub Pages |
| Data model | Weekly JSON (`YYYY-MMDD.json`) + `index.json` retaining every week |
| Design doc | Requirements v1.3 (`system_design.md`) |

---

## 2. Work completed

> Everything below has been committed to the repository.

### 2.1 Documentation
- ✅ Requirements doc v1.3 (4 spec changes + DevContainer section)
- ✅ Architecture doc (system overview, data flow, schemas)
- ✅ `README.md` (setup steps, command reference)

### 2.2 Configuration
- ✅ `config/keywords.yaml` — filter keywords (22 entries, freely editable)
- ✅ `config/settings.yaml` — `max_papers=50`, GitHub Models endpoint, etc.

### 2.3 Backend scripts (Python 3.11)
- ✅ `scripts/fetch_papers.py` — arXiv fetch, keyword filter, category assignment
- ✅ `scripts/analyze_papers.py` — six-angle English analysis via GitHub Models
- ✅ `scripts/build_data.py` — weekly JSON build, `index.json` and `latest.json` update
- ✅ `scripts/test_connection.py` — GitHub Models connectivity check
- ✅ `requirements.txt` — `openai`, `pyyaml`

### 2.4 CI/CD
- ✅ `.github/workflows/update.yml` — four-job pipeline (fetch → analyze → build → deploy)

### 2.5 Frontend (React 18 + Vite)
- ✅ `web/src/App.jsx` — data fetching, week selector, category filter
- ✅ `web/src/components/Header.jsx`
- ✅ `web/src/components/WeekSelector.jsx` — builds week list from `index.json`
- ✅ `web/src/components/CategoryFilter.jsx`
- ✅ `web/src/components/PaperCard.jsx` — header click expands the six-angle view
- ✅ `web/src/components/TrendSummary.jsx`
- ✅ `web/index.html` / `vite.config.js` / `package.json`

### 2.6 DevContainer
- ✅ `.devcontainer/devcontainer.json`
- ✅ Adds Node 20, GitHub CLI, common-utils via devcontainer features
- ✅ `devcontainer.json` runs venv / npm install / `gh auth status` on create

---

## 3. Remaining tasks for GitHub Copilot

### 3.1 GitHub repo configuration [highest priority]

**☐ Enable GitHub Pages**
```
Settings -> Pages -> Source: Deploy from branch
-> Branch: gh-pages / (root) -> Save
```

**☐ Confirm Actions has write permissions**
```
Settings -> Actions -> General
-> Workflow permissions -> Read and write permissions -> Save
```

> `GITHUB_TOKEN` is auto-issued by Actions, so it does NOT need to be added
> to Secrets manually.

---

### 3.2 First-run smoke tests

**☐ Open the DevContainer and run the connectivity check**
```bash
python scripts/test_connection.py
```

**☐ Dry-run the arXiv fetcher**
```bash
python scripts/fetch_papers.py --dry-run
```

**☐ Trigger the workflow manually and verify every job goes green**
```
Actions -> Weekly arXiv Update -> Run workflow -> Run workflow
```

**☐ Verify the GitHub Pages URL renders the frontend**
```
https://YOUR_ORG.github.io/arxiv-weekly/
```

---

### 3.3 Debugging cheatsheet

| Symptom | Likely cause | Fix |
|---|---|---|
| `analyze` job fails | GitHub Models rate limit | Increase `retry_interval` in `settings.yaml` (e.g. `10.0`) |
| `deploy` job fails | GitHub Pages not enabled | Complete step 3.1 |
| No papers shown in UI | `data/` not copied to `web/public/data/` | Check the "Copy data to web/public" step in `update.yml` |
| Papers classified as "Other" | Keywords don't match | Add/adjust `include` keywords in `keywords.yaml` |
| Weekly JSON skipped | File for that date already exists | Expected; delete `data/weekly/YYYY-MMDD.json` to rerun |
| GitHub Models auth error | `GITHUB_TOKEN` lacks permission | Ensure `permissions: contents: write` in `update.yml` |

---

### 3.4 Future enhancements

- ☐ Show citation counts and GitHub stars (Semantic Scholar API)
- ☐ Weekly notifications to Slack / etc. via webhook
- ☐ Visualize keyword-hit trends (charts)
- ☐ Add PDF summaries (fetch from arXiv HTML)

---

## 4. File status

| Path | Description | Status |
|---|---|---|
| `.devcontainer/devcontainer.json` | Python 3.11 image + features + first-time setup | ✅ Implemented |
| `.github/workflows/update.yml` | Four-job auto-update workflow | ✅ Implemented |
| `config/keywords.yaml` | Filter keywords (edit here only) | ✅ Implemented |
| `config/settings.yaml` | `max_papers=50` etc. | ✅ Implemented |
| `data/index.json` | All-week index (empty initially) | ✅ Implemented |
| `data/latest.json` | Latest-week data (placeholder initially) | ✅ Implemented |
| `data/weekly/YYYY-MMDD.json` | Weekly paper data | ☐ Generated by Actions |
| `scripts/fetch_papers.py` | arXiv fetch / filter / categorize | ✅ Implemented |
| `scripts/analyze_papers.py` | Six-angle analysis via GitHub Models | ✅ Implemented |
| `scripts/build_data.py` | Weekly JSON + index build | ✅ Implemented |
| `scripts/test_connection.py` | GitHub Models connectivity check | ✅ Implemented |
| `requirements.txt` | `openai`, `pyyaml` | ✅ Implemented |
| `web/src/App.jsx` | Main component / state management | ✅ Implemented |
| `web/src/components/PaperCard.jsx` | Six-angle accordion card | ✅ Implemented |
| `web/src/components/WeekSelector.jsx` | Week dropdown | ✅ Implemented |
| `web/package.json` / `vite.config.js` | Vite build config | ✅ Implemented |
| `README.md` | Setup and usage | ✅ Implemented |

---

## 5. Data flow summary

```
Every Friday 12:00 UTC
        │
        ▼
┌─────────────┐
│    fetch    │  fetch_papers.py
│  arXiv API  │  -> data/raw_papers.json
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   analyze   │  analyze_papers.py
│ GitHub      │  auth via GITHUB_TOKEN
│ Models      │  -> data/analyzed_papers.json
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    build    │  build_data.py
│ weekly JSON │  -> data/weekly/YYYY-MMDD.json
│ update idx  │  -> data/index.json
│ update last │  -> data/latest.json
│ git push    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   deploy    │  vite build
│ GitHub Pages│  -> gh-pages branch
└─────────────┘
```

> ⚠️ **Mind the rate limit:** GitHub Models Pro is 50 req/day. For testing,
> lower `max_papers` in `settings.yaml` to 3-5.

---

## 6. Keyword management (common operations)

### Add a new keyword

Just append to the `include` list in `config/keywords.yaml`. No code change.

```yaml
include:
  - audio foundation model   # existing
  - audio codec              # <- just add
```

### Map keywords to an existing UI category

Also add the keyword to the relevant entry's `keywords` under `ui_categories`.

### Add a new UI category

Add a new entry to `ui_categories`. The frontend `CategoryFilter` builds the
tab list dynamically, so no code change is needed.

```yaml
ui_categories:
  - id: new_category
    label: New Category Name
    color: "#e879f9"
    keywords:
      - new keyword 1
      - new keyword 2
```

---

## 7. References

| Resource | URL / Location |
|---|---|
| Requirements / Design | `system_design.md` (in this folder) |
| arXiv API docs | https://arxiv.org/help/api/user-manual |
| GitHub Models docs | https://docs.github.com/en/github-models |
| GitHub Pages docs | https://docs.github.com/en/pages |
| Vite docs | https://vitejs.dev/ |
| openai Python SDK | https://github.com/openai/openai-python |

---

## 8. Handover checklist

Run through these in order before continuing.

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | Commits pushed to the repository | Done | ✅ |
| 2 | GitHub Pages is enabled | Copilot | ☐ |
| 3 | Actions has `Read and write permissions` | Copilot | ☐ |
| 4 | DevContainer starts successfully | Copilot | ☐ |
| 5 | `test_connection.py` succeeds | Copilot | ☐ |
| 6 | Manual `workflow_dispatch` is fully green | Copilot | ☐ |
| 7 | Frontend renders at the Pages URL | Copilot | ☐ |
| 8 | First weekly JSON appears under `data/weekly/` | Copilot | ☐ |
| 9 | Frontend renders the paper data correctly | Copilot | ☐ |
| 10 | The next Friday's scheduled run succeeds | Copilot | ☐ |

---

*End of handover.*
