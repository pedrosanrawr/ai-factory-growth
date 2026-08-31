from schema import SEGMENT_WEIGHTS


def run(records: list[dict]) -> list[dict]:
    """Assign the schema-defined weight for each record's AI Factory role."""
    for record in records:
        role = record.get("role", "")
        record["segment_weight"] = SEGMENT_WEIGHTS.get(role, 0.0)

    return records
