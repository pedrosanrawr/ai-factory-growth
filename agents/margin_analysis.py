from schema import MARGIN_SCORE_BANDS


def run(records: list[dict]) -> list[dict]:
    for record in records:
        margin = record.get("operating_margin_pct", 0.0)

        for threshold, score in MARGIN_SCORE_BANDS:
            if margin > threshold:
                record["margin_score"] = score
                break
        else:
            record["margin_score"] = 1

    return records