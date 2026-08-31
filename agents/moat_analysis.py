"""ESPINOSA work file: evidence-grounded moat analysis.

Steps:
1. Keep ``run(records)`` compatible with the existing workflow.
2. Use Member 1's structured Gemini helper and Member 3's evidence contract.
3. Request score (0--5), rationale, confidence, and evidence reference IDs.
4. Validate every returned field and evidence reference before saving it.
5. If evidence or the LLM is unavailable, keep the existing CSV moat score.
6. Add tests for valid output, invalid output, invalid citations, and fallback.

Do not change the TAFGS formula, rank records, or remove CSV compatibility.
Done when the analysis is explainable, evidence-linked, and remains compatible
with CSV-only ranking.
"""


def run(records: list[dict]) -> list[dict]:
    """Validate and clamp each record's moat_score to the 0-5 range."""
    for record in records:
        score = record.get("moat_score", 0)
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0
        score = max(0, min(5, score))
        record["moat_score"] = score
    return records
