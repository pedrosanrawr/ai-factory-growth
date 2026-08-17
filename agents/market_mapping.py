"""
Agent 1: Market Mapping Agent
Owner: Igot

GOAL:
Assign a capital-stack weight to each company based on its AI Factory
segment. This weight represents how much of the total AI Factory dollar
spend flows through that segment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARIABLES YOU WILL READ FROM THE RECORD:
- record["role"]  →  str, the company's AI Factory segment
  Possible values:
    "Compute/Server"
    "Networking"
    "Power Infrastructure"
    "Cooling Systems"
    "Engineering & Construction"

VARIABLES YOU WILL FILL:
- record["segment_weight"]  →  float (0.0–1.0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEGMENT WEIGHTS (defined in schema.py — always import, never hard-code):
  "Compute/Server"              → 0.40
  "Networking"                  → 0.20
  "Power Infrastructure"        → 0.15
  "Cooling Systems"             → 0.15
  "Engineering & Construction"  → 0.10

These weights reflect the share of total AI Factory capital spend
per segment. They are fixed — do not change them.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Import SEGMENT_WEIGHTS from schema.
2. Loop through every record.
3. Get the role: role = record.get("role", "")
4. Look it up: record["segment_weight"] = SEGMENT_WEIGHTS.get(role, 0.0)
   — Use .get() with default 0.0 so unknown roles don't crash the app.
5. Return the updated list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES:

  NVIDIA (NVDA):
    role = "Compute/Server"
    segment_weight = SEGMENT_WEIGHTS["Compute/Server"] = 0.40

  Vertiv (VRT):
    role = "Cooling Systems"
    segment_weight = SEGMENT_WEIGHTS["Cooling Systems"] = 0.15

  Unknown role:
    role = "Software"
    segment_weight = 0.0  (default — not in the AI Factory value chain)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT:  list[dict]  — records from Company Ingestion Agent
OUTPUT: list[dict]  — same records, segment_weight filled in per record

DO NOT:
- Hard-code the weights inside this function — always use schema.SEGMENT_WEIGHTS.
- Change any other field in the record.
- Crash if role is missing — use .get() with a default.
"""

from schema import SEGMENT_WEIGHTS


def run(records: list[dict]) -> list[dict]:
    # TODO: implement this agent
    # Loop through records, assign segment_weight from SEGMENT_WEIGHTS
    # Return the updated records list
    return records