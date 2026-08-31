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
