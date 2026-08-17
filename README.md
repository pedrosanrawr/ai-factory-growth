# AI Factory Growth

This repository is the shared codebase for the group's **AI Factory Growth** project.

## Project Status

The initial project structure is ready:

* **`schema.py`** — Contains the shared company record structure that all agents must follow.
* **`app.py`** — A simple Streamlit starter app so the project can already run locally.
* **`agents/`** — Contains placeholder files for each assigned agent. Each file includes comments describing what the assigned group member should build.

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
| `frontend/data.py`            | Temporary mock data (UI only) |
| `schema.py`                   | Shared schema / data contract |

> **Important:** `schema.py` is a shared file. Do not change its field names without informing the entire team.

---

## GitHub Workflow

### 1. Clone the repository

```bash
git clone https://github.com/[your-username]/ai-factory-growth.git
cd ai-factory-growth
```

### 2. Create your own branch

Each team member should create a branch based on their assigned file:

```bash
# Market Mapping
git checkout -b agent/market-mapping

# Company Ingestion
git checkout -b agent/company-ingestion

# Moat Analysis
git checkout -b agent/moat-analysis

# Margin Analysis
git checkout -b agent/margin-analysis

# Growth Forecast
git checkout -b agent/growth-forecast

# Risk Adjustment
git checkout -b agent/risk-adjustment

# Ranking
git checkout -b agent/ranking

# Report
git checkout -b agent/report

# Streamlit UI
git checkout -b ui/streamlit-app
```

### 3. Work only on your assigned file

Only modify the file you own unless you have coordinated with the team beforehand.

### 4. Commit your changes

Use the standard commit message format:

```bash
git add [file-path]
git commit -m "type: message"
```

Only commit the file you worked on. Replace `[file-path]` with the path to your assigned file.

Common commit types:

* `feat:` — add a new feature
* `fix:` — fix a bug
* `docs:` — update documentation
* `chore:` — setup or maintenance work
* `refactor:` — restructure code without changing behavior
* `test:` — add or update tests
* `ui:` — modify ui

Examples:

```bash
git commit -m "feat: implement market mapping"
git commit -m "fix: handle missing company data"
git commit -m "docs: update README"
git commit -m "chore: set up project structure"
```

### 5. Push your branch

```bash
git push origin [your-branch-name]
```

### 6. Open a Pull Request

After pushing your branch, open a **Pull Request (PR)** on GitHub.

The **Owner** will review the changes before merging them into the main branch.

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

## Dashboard Control Contract

The Streamlit controls are pipeline inputs, not display-only settings. The UI
owner owns the widgets and passes values to agents; each agent owner implements
only the calculation in their assigned file.

| Control | UI responsibility | Agent responsibility |
| --- | --- | --- |
| Risk Adjustment Agent Discount (0-30%) | Pass `risk_discount` to `risk_adjustment.run(...)`. | Risk Adjustment uses it to calculate `risk_multiplier` and `adjusted_growth_pct`. |
| Power Efficiency Weighting (1.0-2.0x) | Pass `power_weight` to `ranking.run(...)`. | Ranking uses `eff_score` and the weight to calculate `tafgs_score`. |
| Ranking Agent Priority | Pass `ranking_priority` to `ranking.run(...)`. | Ranking selects the requested sort order. |
| AI Factory Role filter | Filter records before ranking. | No agent calculation changes. |

Use this pipeline order in the UI:

```python
records = adjust_risk(records, risk_discount_pct=risk_discount)
top_20 = rank_companies(
    records,
    ranking_priority=ranking_priority,
    power_efficiency_weight=power_weight,
)
```

`eff_score` is a required shared field: Company Ingestion reads it from the
CSV, Ranking uses it, and valid values are integers from 1 to 5.

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
|   `-- data.py                # Temporary mock data; remove after integration
|-- data/
|   `-- companies.csv          # Source dataset for Company Ingestion
|-- assets/
|   `-- logo.png
|-- .streamlit/
|   `-- config.toml
|-- app.py                     # Streamlit entry point
|-- schema.py                  # Shared record contract
|-- requirements.txt
`-- README.md
```

---

## Goal

Build a modular **AI Factory Growth analysis pipeline** where each agent is responsible for a specific part of the analysis while following a shared data structure and GitHub workflow.
