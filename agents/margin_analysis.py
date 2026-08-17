"""
Agent 4: Margin Analysis Agent
Owner: Navarra

GOAL:
Convert each company's raw operating margin percentage into a
normalized 1–5 score using the official scoring bands from the
project brief. This score feeds directly into the TAFGS formula
in the Ranking Agent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARIABLES YOU WILL READ FROM THE RECORD:
- record["operating_margin_pct"]  →  float
  Examples: 60.38 (NVIDIA), 20.40 (Vertiv), -2.20 (Fluor)

VARIABLES YOU WILL FILL:
- record["margin_score"]  →  int (1–5)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORING BANDS (from the project brief — defined in schema.MARGIN_SCORE_BANDS):
  Operating Margin %  →  Score
  > 40%               →  5
  > 30%               →  4
  > 20%               →  3
  > 10%               →  2
  ≤ 10% or negative   →  1

  IMPORTANT: Minimum score is always 1 — never 0.
  Even negative margins (e.g. Fluor at -2.2%) still score 1.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Import MARGIN_SCORE_BANDS from schema.
2. Loop through every record.
3. Get the margin: margin = record.get("operating_margin_pct", 0.0)
4. Loop through MARGIN_SCORE_BANDS:
     for threshold, score in MARGIN_SCORE_BANDS:
         if margin > threshold:
             record["margin_score"] = score
             break
   else:
       record["margin_score"] = 1
5. Return the updated list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES:

  NVIDIA (NVDA):
    operating_margin_pct = 60.38
    60.38 > 40 → margin_score = 5

  Broadcom (AVGO):
    operating_margin_pct = 64.90
    64.90 > 40 → margin_score = 5

  Vertiv (VRT):
    operating_margin_pct = 20.40
    20.40 > 20 → margin_score = 3

  GE Vernova (GEV):
    operating_margin_pct = 8.40
    8.40 ≤ 10 → margin_score = 1

  Fluor (FLR):
    operating_margin_pct = -2.20
    -2.20 ≤ 10 → margin_score = 1  (negative still scores 1)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT:  list[dict]  — records from Moat Analysis Agent
OUTPUT: list[dict]  — same records, margin_score (1–5) filled in

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