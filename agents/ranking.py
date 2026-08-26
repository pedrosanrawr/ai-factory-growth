"""
Agent 7: Ranking Agent
Owner: Flores

GOAL:
Compute the final TAFGS score for each company using the formula
defined in the project brief, then sort all companies by the selected
ranking priority and assign final ranks (1 = best).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TAFGS FORMULA (from the project brief — this is the core formula,
do not change it):

  TAFGS = (Moat Score × Operating Margin Score) × Forecast AI-Driven Growth

  In code:
    base_tafgs = moat_score * margin_score * (adjusted_growth_pct / 100)

  NOTE: adjusted_growth_pct is divided by 100 to convert from % to decimal.
  NOTE: Use adjusted_growth_pct (from Risk Adjustment Agent) — NOT
        the raw growth_forecast_pct from the CSV.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ADDITIONAL CONFIGURATION — Power Efficiency Weighting:
  The UI provides a Power Efficiency Weighting slider (1.0–2.0x).
  This is an ADDITIONAL multiplier applied ON TOP of the base TAFGS
  — it does not replace or modify the core brief formula above.
  Think of it as a configurable boost that rewards companies with
  higher Efficiency Scores when the user increases the weight.

  efficiency_factor = 1 + ((clamp(eff_score, 1, 5) - 1) / 4) *
                          (clamp(power_efficiency_weight, 1.0, 2.0) - 1)
  tafgs_score = base_tafgs * efficiency_factor

  Behavior of efficiency_factor at default weight (1.2x):
    eff_score=1 → factor=1.00  (no boost — lowest efficiency)
    eff_score=3 → factor=1.10  (10% boost)
    eff_score=5 → factor=1.20  (20% boost — highest efficiency)

  Behavior at weight=1.0x:
    efficiency_factor always = 1.00 regardless of eff_score
    → pure brief formula, no boost applied

  Behavior at weight=2.0x:
    eff_score=1 → factor=1.00  (no boost)
    eff_score=5 → factor=2.00  (100% boost — maximum amplification)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARIABLES YOU WILL READ FROM THE RECORD:
- record["moat_score"]            →  int (0–5), from Moat Analysis Agent
- record["margin_score"]          →  int (1–5), from Margin Analysis Agent
- record["adjusted_growth_pct"]   →  float, from Risk Adjustment Agent
- record["eff_score"]             →  int (1–5), from CSV
- record["operating_margin_pct"]  →  float, needed to determine Status field

VARIABLES YOU WILL FILL:
- record["tafgs_score"]  →  float (final score after brief formula + config)
- record["rank"]         →  int (1 = highest tafgs_score)
- record["status"]       →  str ("Profitable" or "Unprofitable")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS FIELD:
  Fill this before sorting:
    record["status"] = "Profitable" if record["operating_margin_pct"] > 0
                       else "Unprofitable"

SORTING OPTIONS (based on ranking_priority parameter):
  "Profitability First" → sort by (status=="Profitable" DESC, tafgs_score DESC)
  "Growth % (Highest)"  → sort by adjusted_growth_pct DESC
  "TAFGS Score"         → sort by tafgs_score DESC (default)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Loop through every record:
   a. Fill record["status"] based on operating_margin_pct
   b. Compute base_tafgs = moat_score * margin_score * (adjusted_growth_pct / 100)
   c. Compute efficiency_factor using eff_score and power_efficiency_weight
   d. Compute tafgs_score = base_tafgs * efficiency_factor
   e. Write tafgs_score into record["tafgs_score"]
2. Sort the full list based on ranking_priority.
3. Take the top 20: top_20 = sorted_records[:20]
4. Assign ranks: for i, record in enumerate(top_20): record["rank"] = i + 1
5. Return top_20 only — NOT the full list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES (at default power_efficiency_weight=1.2):

  NVIDIA (NVDA) — eff_score=5:
    base_tafgs        = 5 * 5 * (42.57/100)       = 10.643
    efficiency_factor = 1 + ((5-1)/4) * (1.2-1)   = 1.20
    tafgs_score       = 10.643 * 1.20              = 12.771

  Broadcom (AVGO) — eff_score=4:
    base_tafgs        = 5 * 5 * (32.20/100)        = 8.050
    efficiency_factor = 1 + ((4-1)/4) * (1.2-1)    = 1.15
    tafgs_score       = 8.050 * 1.15               = 9.258

  Fluor (FLR) — eff_score=1:
    base_tafgs        = 3 * 1 * (12.15/100)        = 0.365
    efficiency_factor = 1 + ((1-1)/4) * (1.2-1)    = 1.00
    tafgs_score       = 0.365 * 1.00               = 0.365

  At weight=1.0 (pure brief formula, no boost):
    NVIDIA: base_tafgs = 10.643, efficiency_factor = 1.00 → tafgs = 10.643
    Fluor:  base_tafgs = 0.365,  efficiency_factor = 1.00 → tafgs = 0.365

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DO NOT:
- Return more than 20 records.
- Use growth_forecast_pct (raw) — always use adjusted_growth_pct.
- Apply risk_discount_pct here — that is already baked into
  adjusted_growth_pct by the Risk Adjustment Agent.
- Remove or modify the core brief formula (base_tafgs) — the
  efficiency_factor is additive on top of it, not a replacement.
"""

from decimal import ROUND_HALF_UP, Decimal


def _round_half_up(value: float, decimals: int = 3) -> float:
    """
    Round using standard "round half up" behavior (0.3645 -> 0.365),
    matching the spec's worked examples.

    Python's built-in round() uses banker's rounding on the raw binary
    float value, which can quietly round the wrong way for numbers that
    land near a .5 boundary at the target precision (12.15/100 is not
    exactly representable in binary, so round(0.3645, 3) gives 0.364
    instead of 0.365). Going through Decimal(str(value)) uses the
    human-readable decimal string instead of the raw binary value, which
    avoids that trap.
    """
    quantizer = Decimal(1).scaleb(-decimals)  # e.g. decimals=3 -> Decimal('0.001')
    return float(Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP))


def run(
    records: list[dict],
    ranking_priority: str = "TAFGS Score",
    power_efficiency_weight: float = 1.2,
) -> list[dict]:
    scored = []

    for original in records:
        record = dict(original)  # don't mutate the caller's data

        # --- a. Status field (fill before sorting) ---
        operating_margin_pct = record.get("operating_margin_pct", 0.0) or 0.0
        record["status"] = "Profitable" if operating_margin_pct > 0 else "Unprofitable"

        # --- b. Core brief formula (do not change) ---
        moat_score = record.get("moat_score", 0) or 0
        margin_score = record.get("margin_score", 0) or 0
        adjusted_growth_pct = record.get("adjusted_growth_pct", 0.0) or 0.0
        base_tafgs = moat_score * margin_score * (adjusted_growth_pct / 100)

        # --- c. Power Efficiency Weighting (configurable boost on top) ---
        eff_score = _clamp(record.get("eff_score", 1), 1, 5)
        weight = _clamp(power_efficiency_weight, 1.0, 2.0)
        efficiency_factor = 1 + ((eff_score - 1) / 4) * (weight - 1)

        # --- d/e. Final score ---
        record["tafgs_score"] = _round_half_up(base_tafgs * efficiency_factor, 3)

        scored.append(record)

    # --- 2. Sort the full list based on ranking_priority ---
    if ranking_priority == "Profitability First":
        scored.sort(
            key=lambda r: (r["status"] == "Profitable", r["tafgs_score"]), reverse=True
        )
    elif ranking_priority == "Growth % (Highest)":
        scored.sort(
            key=lambda r: r.get("adjusted_growth_pct", 0.0) or 0.0, reverse=True
        )
    else:
        # "TAFGS Score" and any unrecognized value fall back to this default
        scored.sort(key=lambda r: r["tafgs_score"], reverse=True)

    # --- 3. Take the top 20 ---
    top_20 = scored[:20]

    # --- 4. Assign ranks ---
    for i, record in enumerate(top_20):
        record["rank"] = i + 1

    # --- 5. Return top 20 only ---
    return top_20


def _clamp(value, lo, hi):
    """Clamp a value between lo and hi, safely handling non-numeric input."""
    try:
        return max(lo, min(hi, float(value)))
    except (ValueError, TypeError):
        return lo
