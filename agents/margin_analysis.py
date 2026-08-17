"""
Agent 4: Margin Analysis Agent
Owner: Navarra

GOAL:
Convert each company's raw operating margin percentage into a
normalized 1–5 score using the official scoring bands from the
project brief. This score is then used by the Ranking Agent in
the TAFGS formula.

VARIABLE YOU WILL READ FROM THE RECORD:
- record["operating_margin_pct"]  →  float (e.g. 60.38 for Nvidia, -2.2 for Fluor)

VARIABLE YOU WILL FILL:
- record["margin_score"]  →  int (1–5)

SCORING BANDS (from the project brief — defined in schema.MARGIN_SCORE_BANDS):
  Operating Margin %  →  Score
  > 40%               →  5
  > 30%               →  4
  > 20%               →  3
  > 10%               →  2
  ≤ 10% (or negative) →  1

NOTE: The minimum score is 1, not 0. Even a company with a negative
margin (like Fluor at -2.2%) still gets a score of 1.

WHAT TO DO:
1. Import MARGIN_SCORE_BANDS from schema.
2. Loop through every record.
3. Get the margin: margin = record.get("operating_margin_pct", 0.0)
4. Loop through MARGIN_SCORE_BANDS to find the matching score:
   for threshold, score in MARGIN_SCORE_BANDS:
       if margin > threshold:
           record["margin_score"] = score
           break
   else:
       record["margin_score"] = 1  # default if nothing matches
5. Return the updated list.

INPUT:  list[dict]  — records from Moat Analysis Agent
OUTPUT: list[dict]  — same records, margin_score filled in

EXAMPLE:
  NVIDIA  → operating_margin_pct = 60.38 → margin_score = 5  (>40%)
  Arista  → operating_margin_pct = 42.82 → margin_score = 5  (>40%)
  Vertiv  → operating_margin_pct = 20.40 → margin_score = 3  (>20%)
  Eaton   → operating_margin_pct = 24.50 → margin_score = 3  (>20%)
  Fluor   → operating_margin_pct = -2.20 → margin_score = 1  (≤10%)

DO NOT:
- Use a score of 0 — minimum is always 1.
- Hard-code the band thresholds — always use schema.MARGIN_SCORE_BANDS.
- Change any other field in the record.
"""

from schema import MARGIN_SCORE_BANDS


def run(records: list[dict]) -> list[dict]:
    # TODO: implement this agent
    # Loop, apply MARGIN_SCORE_BANDS to operating_margin_pct,
    # write result into margin_score, return records
    return records