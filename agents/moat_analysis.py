"""
Agent 3: Moat Analysis Agent
Owner: Espinosa

GOAL:
Validate and confirm the Moat Score for each company. The moat_score
is already PRE-FILLED in the CSV (filled in during research based on
the 4 moat criteria). This agent reads it, validates the range,
and clamps any out-of-bound values.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARIABLES YOU WILL READ FROM THE RECORD:
- record["moat_score"]  →  int (0–5), pre-filled from CSV

VARIABLES YOU WILL FILL/CONFIRM:
- record["moat_score"]  →  same field, validated and clamped to 0–5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE 4 MOAT CRITERIA (reference for paper — not used in computation):
  1. Architectural Lock-In    — proprietary tech embedded in customer infra
  2. Ecosystem Dominance      — market share, reference architecture, design wins
  3. Switching Costs          — cost/effort to migrate away
  4. Scarcity/Bottleneck      — rare capability, hard to replicate

SCORE MEANING:
  0 = no identifiable moat
  1 = weak differentiation
  2 = limited differentiation
  3 = moderate moat
  4 = strong moat
  5 = exceptional moat / bottleneck position

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Loop through every record.
2. Get the score: score = record.get("moat_score", 0)
3. Convert to int safely using try/except — default to 0 if invalid.
4. Clamp to valid range: score = max(0, min(5, score))
5. Write back: record["moat_score"] = score
6. Return the updated list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES:

  NVIDIA (NVDA):
    moat_score in CSV = 5
    After validation  = 5  (unchanged, already valid)

  Fluor (FLR):
    moat_score in CSV = 3
    After validation  = 3  (unchanged, already valid)

  Bad data edge case:
    moat_score in CSV = "N/A"
    After validation  = 0  (defaulted — cannot convert to int)

  Out-of-range edge case:
    moat_score in CSV = 7
    After validation  = 5  (clamped to maximum)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT:  list[dict]  — records from Market Mapping Agent
OUTPUT: list[dict]  — same records, moat_score validated

DO NOT:
- Recalculate moat_score from moat_notes text.
- Change any other field in the record.
- Crash if the value is not a number — use try/except.
"""


def run(records: list[dict]) -> list[dict]:
    # TODO: implement this agent
    # Loop, validate moat_score, clamp to 0-5, return records
    return records