# AI Factory Growth

This repository is the shared codebase for the group's **AI Factory Growth** project.

## Project Status

The provider-backed analysis pipeline is ready:

* **`schema.py`** — Contains the shared company record structure that all agents must follow.
* **`app.py`** — Launches the Streamlit dashboard.
* **`agents/`** — Contains the eight analysis modules that process company records in sequence.


The dashboard loads its curated company universe from `data/companies.csv` and
runs the LangGraph scoring pipeline immediately. This makes the standard
Top-20 view repeatable and fast. The CSV is the approved Phase-1 company
universe and scoring snapshot. When present, the local evidence store is read
alongside it to display previously approved sources and research status; the
dashboard never fetches external research at runtime.

### Offline Research Refresh

There is no dashboard research button. Run these commands manually or from a
scheduled task outside Streamlit:

```bash
# Stage newly found SEC sources for review (no CSV or evidence-store writes).
python -m scripts.refresh_research --dry-run

# Build or update the cached Gemini analysis snapshot from local evidence.
python -m scripts.refresh_analysis
```

`refresh_analysis` reuses cached Gemini responses when the company evidence is
unchanged. The dashboard only reads `data/research_snapshots/latest.json`; it
never waits for Gemini. A changed source invalidates that company's snapshot,
so stale analysis is not applied.

---

## Team File Ownership

| File                          | Responsibility                |
| ----------------------------- | ----------------------------- |
| `agents/market_mapping.py`    | Market Mapping                |
| `agents/company_ingestion.py` | Company Ingestion             |
| `agents/moat_analysis.py`     | Moat Analysis                 |
| `agents/margin_analysis.py`   | Margin Analysis               |
| `agents/growth_forecast.py`   | Growth Forecast               |
| `agents/risk_adjustment.py`   | Risk Adjustment               |
| `agents/ranking.py`           | Ranking                       |
| `agents/report.py`            | Report Generation             |
| `app.py`                      | Streamlit entry point         |
| `frontend/page.py`            | UI layout and control wiring  |
| `frontend/components.py`      | Dashboard tables and export   |
| `frontend/styles.py`          | Dashboard styling             |
| `schema.py`                   | Shared schema / data contract |

> **Important:** `schema.py` is a shared file. Do not change its field names without informing the entire team.

---

## GitHub Workflow

### 1. Clone the repository

If you have not cloned the repository yet:

```bash
git clone https://github.com/[your-username]/ai-factory-growth.git
cd ai-factory-growth
```

### 2. Create your own branch

Each team member must create their **own branch** for their work.

First, make sure your local `main` branch is up to date:

```bash
git fetch origin
git checkout main
git pull origin main
```

Then create your own branch:

```bash
git checkout -b folder/your-branch-name
```

Use the following naming convention:

```text
folder/description
```

The `folder` should indicate the area of the project you are working on, while the description should clearly identify the specific task.

Examples:

```bash
git checkout -b frontend/dashboard-control
git checkout -b frontend/logo
git checkout -b frontend/sidebar
git checkout -b agents/market-mapping
git checkout -b agents/company-ingestion
git checkout -b agents/ranking
```

After creating your branch, all of your changes should be committed and pushed to **your own branch**.

Your Pull Request should target:

```text
your-branch-name → main
```

For example:

```text
frontend/dashboard-control → main
```

The Owner will review the Pull Request before merging it into `main`.

### 3. Work only on your assigned file

Only modify the file you own unless you have coordinated with the team beforehand.

### 4. Commit your changes

Use the standard commit message format:

```bash
git add [file-path]
git commit -m "type: message"
```

Only commit the file(s) you worked on. Replace `[file-path]` with the path to your assigned file.

Common commit types:

* `feat:` — add a new feature
* `fix:` — fix a bug
* `docs:` — update documentation
* `chore:` — setup or maintenance work
* `refactor:` — restructure code without changing behavior
* `test:` — add or update tests
* `ui:` — modify UI

Examples:

```bash
git commit -m "feat: implement market mapping"
git commit -m "fix: handle missing company data"
git commit -m "docs: update README"
git commit -m "chore: set up project structure"
git commit -m "ui: improve dashboard layout"
```

### 5. Push your branch

Push your changes to your own branch:

```bash
git push -u origin your-branch-name
```

For example:

```bash
git push -u origin frontend/dashboard-control
```

### 6. Open a Pull Request

After pushing your branch, open a **Pull Request (PR)** on GitHub.

Your Pull Request should always target the `main` branch:

```text
your-branch-name → main
```

For example:

```text
frontend/dashboard-control → main
```

The **Owner will review the changes before merging the Pull Request into `main`**.

The Owner may:

1. Review the code.
2. Test the changes.
3. Request changes if necessary.
4. Approve the Pull Request.
5. Merge the Pull Request into `main`.

---

## Local Setup

### Install Dependencies

Make sure Python is installed, then run:

```bash
pip install -r requirements.txt
```

### Run the Application

Start the Streamlit app with:

```bash
streamlit run app.py
```

The application should open automatically in your browser.

---

## Local Testing

Before pushing your changes, make sure that:

1. `streamlit run app.py` opens successfully.
2. Your assigned agent file has no Python syntax errors.
3. Your changes follow the shared schema in `schema.py`.
4. You did not rename or remove schema fields without team approval.
5. You did not accidentally modify another team member's file.

---

## Shared Data Contract

`schema.py` defines the **shared data contract** used by all agents.

Every agent should:

* Accept the shared `list[dict]` structure.
* Return the shared `list[dict]` structure.
* Use the field names defined in `schema.py`.
* Avoid modifying the schema without team approval.

This ensures that the outputs from different agents can be connected together without breaking the pipeline.

---

## Important Team Rules

> **1. `schema.py` is the contract for all agents.**

> **2. Every agent should accept and return the shared `list[dict]` structure.**

> **3. Avoid editing another member's file unless you have coordinated with them.**

> **4. If a schema change is necessary, announce it to the whole team before making the change.**

> **5. Each team member should work on their own branch and submit a Pull Request for review.**

---

## Core Pipeline Structure

```text
ai-factory-growth/
|-- agents/                    # One module per analysis agent
|   |-- company_ingestion.py
|   |-- market_mapping.py
|   |-- moat_analysis.py
|   |-- margin_analysis.py
|   |-- growth_forecast.py
|   |-- risk_adjustment.py
|   |-- ranking.py
|   `-- report.py
|-- frontend/                  # Streamlit presentation layer
|   |-- page.py                # Layout, controls, and pipeline handoff
|   |-- components.py          # Tables, export, and reusable UI helpers
|   |-- styles.py              # CSS styling
|-- data/
|   `-- companies.csv          # Source dataset for Company Ingestion
|-- assets/
|   `-- logo.png
|-- .streamlit/
|   `-- config.toml
|-- app.py                     # Streamlit entry point
|-- services/
|   |-- research_sources.py     # Free SEC EDGAR discovery, filings, facts
|   `-- research_enrichment.py # Candidate evidence collection/storage
|-- schema.py                  # Shared record contract
|-- requirements.txt
`-- README.md
```

---

## Quarterly Research Refresh Runbook

Operator process for `scripts/refresh_research.py`, which keeps company
research evidence current without ever silently overwriting
`data/companies.csv` or the evidence store.

### Quarterly steps

1. **Stage** (safe, read-only against every canonical file):

   ```bash
   python -m scripts.refresh_research \
     --input-csv data/companies.csv \
     --evidence-store evidence_store.json
   ```

   This fetches candidate evidence per company and writes a dated,
   reviewable JSON report under `data/refresh_reports/`. Nothing else on
   disk is touched.

2. **(Optional) Dry run** a specific company list or a fresh checkout
   before staging for real, with `--dry-run` — prints the same summary
   to the terminal but writes no files at all, not even the report.

3. **Review** the staged report with a human analyst. For each company
   with `new_evidence_count > 0`, open each candidate evidence item's
   URL and confirm it actually supports its `claim` before doing
   anything else.

4. **Approve and write** only after review:

   ```bash
   python -m scripts.refresh_research \
     --approve-write \
     --from-report data/refresh_reports/research_refresh_<date>.json
   ```

   This is the only step that touches `data/companies.csv` or
   `evidence_store.json`, and only after backing both up (see Backup /
   rollback below).

5. **Spot-check the dashboard**: run `streamlit run app.py`, open a
   couple of the updated companies' profile popups, and confirm the new
   evidence and status badge render as expected.

### Review criteria

* A candidate evidence item may be manually promoted from `needs_review`
  to `verified` **only** after a human has actually opened the source
  and confirmed it supports the stated claim. This script never marks
  anything `verified` on its own.
* Reject (do not approve) any candidate whose `claim` cannot be
  confirmed against the linked source, whose URL 404s, or whose
  `source_type` looks misclassified.
* A company with `analysis_status: "unavailable"` in the report means
  the refresh found nothing new to review — that is expected and is not
  itself a failure to investigate.

### Backup / rollback

* Every `--approve-write` run copies the current `data/companies.csv`
  and evidence-store file into `backups/` with a UTC timestamp suffix
  (e.g. `backups/companies.csv.20260901T120000Z.bak`) **before** writing
  anything.
* To roll back, copy the relevant backup file back over the canonical
  path it came from, e.g.:

  ```bash
  cp backups/companies.csv.20260901T120000Z.bak data/companies.csv
  cp backups/evidence_store.json.20260901T120000Z.bak evidence_store.json
  ```

* Keep the staged report JSON from step 1 alongside the backups — it's
  the record of exactly what was reviewed and approved that quarter.

### Required tests

Run before every quarterly refresh and before merging any change to
this workflow:

```bash
python -m pytest scripts/test_refresh_research.py
python -m pytest agents/__tests__/test_report.py
python -m pytest tests/test_research_profile_rendering.py
python -m pytest services/__tests__/test_evidence_store.py
```

These cover: dry-run (no disk writes), a no-change refresh, a
proposed-change report, report JSON serialization, the approved-write
path (backup + CSV/evidence-store update), and popup rendering for the
verified, needs_review, fallback, and unavailable states.

---

## Goal

Build a modular **AI Factory Growth analysis pipeline** where each agent is responsible for a specific part of the analysis while following a shared data structure and GitHub workflow.
