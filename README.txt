# AI Factory Growth

This repository is the shared codebase for the group's **AI Factory Growth** project.

## Project Status

The initial project structure is ready:

* **`schema.py`** — Contains the shared company record structure that all agents must follow.
* **`app.py`** — A simple Streamlit starter app so the project can already run locally.
* **`agents/`** — Contains placeholder files for each assigned agent. Each file includes comments describing what the assigned group member should build.

---

## Team File Ownership

| File                          | Owner                | Responsibility                |
| ----------------------------- | -------------------- | ----------------------------- |
| `agents/market_mapping.py`    | Member 1 / Tech Lead | Market Mapping                |
| `agents/company_ingestion.py` | Valdez               | Company Ingestion             |
| `agents/moat_analysis.py`     | Espinosa             | Moat Analysis                 |
| `agents/margin_analysis.py`   | Navarra              | Margin Analysis               |
| `agents/growth_forecast.py`   | Don                  | Growth Forecast               |
| `agents/risk_adjustment.py`   | De Jesus             | Risk Adjustment               |
| `agents/ranking.py`           | Flores               | Ranking                       |
| `agents/report.py`            | Dones                | Report Generation             |
| `app.py`                      | UI Lead              | Streamlit UI                  |
| `schema.py`                   | Tech Lead            | Shared schema / data contract |

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

Use a clear commit message describing what you completed:

```bash
git add .
git commit -m "Complete [agent name] implementation"
```

### 5. Push your branch

```bash
git push origin [your-branch-name]
```

### 6. Open a Pull Request

After pushing your branch, open a **Pull Request (PR)** on GitHub.

The **Tech Lead** will review the changes before merging them into the main branch.

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

## Project Structure

```text
ai-factory-growth/
│
├── agents/
│   ├── market_mapping.py
│   ├── company_ingestion.py
│   ├── moat_analysis.py
│   ├── margin_analysis.py
│   ├── growth_forecast.py
│   ├── risk_adjustment.py
│   ├── ranking.py
│   └── report.py
│
├── app.py
├── schema.py
├── requirements.txt
└── README.md
```

---

## Goal

Build a modular **AI Factory Growth analysis pipeline** where each agent is responsible for a specific part of the analysis while following a shared data structure and GitHub workflow.