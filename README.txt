# AI Factory Growth

This repository is the shared codebase for the group's AI Factory Growth project.

## What Is Ready Now

- `schema.py` contains the shared company record structure that everyone must follow.
- `app.py` is a simple Streamlit starter app so the project can already run.
- Each file in `agents/` contains placeholder comments that explain what the assigned groupmate should build.

## Team File Ownership

- `agents/market_mapping.py`: Member 1 / Tech Lead
- `agents/company_ingestion.py`: Valdez
- `agents/moat_analysis.py`: Espinosa
- `agents/margin_analysis.py`: Navarra
- `agents/growth_forecast.py`: Don
- `agents/risk_adjustment.py`: De Jesus
- `agents/ranking.py`: Flores
- `agents/report.py`: Dones
- `app.py`: UI lead
- `schema.py`: Tech Lead shared file, do not change field names without informing the whole group

## GitHub Workflow

1. Clone the repository:

```bash
git clone https://github.com/[your-username]/ai-factory-growth.git
cd ai-factory-growth
```

2. Create your own branch based on your assigned file:

```bash
git checkout -b agent/market-mapping
git checkout -b agent/company-ingestion
git checkout -b agent/moat-analysis
git checkout -b agent/margin-analysis
git checkout -b agent/growth-forecast
git checkout -b agent/risk-adjustment
git checkout -b agent/ranking
git checkout -b agent/report
git checkout -b ui/streamlit-app
```

3. Only edit the file you own unless the team agrees otherwise.

4. Commit your work with a clear message:

```bash
git add .
git commit -m "Complete [agent name] implementation"
```

5. Push your branch:

```bash
git push origin [your-branch-name]
```

6. Open a Pull Request on GitHub so the Tech Lead can review and merge it.

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app locally:

```bash
streamlit run app.py
```

## Local Testing

Before pushing your work:

1. Make sure `streamlit run app.py` still opens successfully.
2. Make sure your assigned agent file has no syntax errors.
3. Do not rename schema fields unless the whole team agrees.

## Important Team Rules

- `schema.py` is the contract for all agents.
- Every agent should accept and return the shared `list[dict]` structure.
- Avoid editing another member's file unless you coordinated first.
- If a schema change is really needed, announce it to the whole team before coding it.
