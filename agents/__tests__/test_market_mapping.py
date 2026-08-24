from schema import empty_record
from agents.market_mapping import run
def make_record(role):
    r = empty_record()
    r["role"] = role
    r["company"] = f"Test-{role}"
    return r

records = [
    make_record("Compute/Server"),
    make_record("Networking"),
    make_record("Power Infrastructure"),
    make_record("Cooling Systems"),
    make_record("Engineering & Construction"),
    make_record("Software"), # unknown role --> default to 0.0
    empty_record(), # missing/blank role -> default to 0.0
]

result = run(records)

for r in result:
    print(f"{r['company'] or '(blank)':30} role={r['role']:30} weight={r['segment_weight']}")