"""
Agent 3: Moat Analysis Agent
Owner: Espinosa

GOAL:
Validate and confirm the Moat Score for each company.
The moat_score is already PRE-FILLED in the CSV (you filled it in during
research based on the 4 moat criteria). This agent's job is to:
  1. Read the pre-filled score
  2. Make sure it is a valid integer between 0 and 5
  3. Clamp any out-of-range values

VARIABLES YOU WILL READ FROM THE RECORD:
- record["moat_score"]  →  int (0–5), pre-filled by you during research

VARIABLE YOU WILL FILL/CONFIRM:
- record["moat_score"]  →  same field, validated and clamped to 0–5

THE 4 MOAT CRITERIA (for reference/paper — not used in computation here):
  1. Architectural Lock-In    — proprietary tech embedded in customer infrastructure
  2. Ecosystem Dominance      — market share, reference architecture, design wins
  3. Switching Costs          — cost/effort to migrate away from this company
  4. Scarcity/Bottleneck      — rare capability, hard to replicate

WHAT TO DO:
1. Loop through every record.
2. Get the moat score: score = record.get("moat_score", 0)
3. Convert to int safely using try/except.
4. Clamp to valid range: score = max(0, min(5, score))
5. Write back: record["moat_score"] = score
6. Return the updated list.

INPUT:  list[dict]  — records from Market Mapping Agent
OUTPUT: list[dict]  — same records, moat_score validated

EXAMPLE:
  Input:  {"moat_score": 5, ...}   (from NVIDIA row in CSV)
  Output: {"moat_score": 5, ...}   (unchanged, already valid)

  Input:  {"moat_score": "N/A", ...}  (bad data edge case)
  Output: {"moat_score": 0, ...}      (defaulted to 0)

DO NOT:
- Recalculate the moat score from the text in moat_notes.
- Change any other field.
- Crash if the value is not a number — use try/except.
"""

def run(records: list[dict]) -> list[dict]:
    # TODO: implement this agent
    # Loop, validate moat_score, clamp to 0-5, return records
    return records