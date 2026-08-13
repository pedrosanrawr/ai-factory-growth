"""
Agent 2: Company Ingestion

- Load `data/companies.csv`
- Validate required columns exist
- Convert each row into the shared `schema.empty_record()` format
- Return a `list[dict]` of company records

Suggested function shape:

def run(csv_path: str = "data/companies.csv") -> list[dict]:
    ...
"""