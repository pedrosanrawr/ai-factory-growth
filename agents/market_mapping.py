"""
Agent 1: Market Mapping Agent
Owner: Igot

GOAL:
Assign a capital-stack weight to each company based on its AI Factory segment.
This weight represents how much of the total AI Factory dollar spend flows
through that segment (e.g. Compute gets 40%, Networking 20%, etc.)

VARIABLES YOU WILL USE FROM THE RECORD:
- record["role"]  →  the company's AI Factory segment (string)
  Example values: "Compute/Server", "Networking", "Power Infrastructure",
                  "Cooling Systems", "Engineering & Construction"

VARIABLE YOU WILL FILL:
- record["segment_weight"]  →  float between 0.0 and 1.0
  This is looked up from schema.SEGMENT_WEIGHTS using record["role"] as the key.

SEGMENT WEIGHTS (defined in schema.py — import and use directly):
  "Compute/Server"              → 0.40
  "Networking"                  → 0.20
  "Power Infrastructure"        → 0.15
  "Cooling Systems"             → 0.15
  "Engineering & Construction"  → 0.10

WHAT TO DO:
1. Import SEGMENT_WEIGHTS from schema.
2. Loop through every record in the input list.
3. Get the company's role: role = record["role"]
4. Look it up in SEGMENT_WEIGHTS: record["segment_weight"] = SEGMENT_WEIGHTS.get(role, 0.0)
   - Use .get() with a default of 0.0 so unknown roles don't crash the app.
5. Return the updated list.

INPUT:  list[dict]  — list of company records from Company Ingestion Agent
OUTPUT: list[dict]  — same list, now with segment_weight filled in per record

EXAMPLE:
  Input:  {"company": "NVIDIA Corporation (NVDA)", "role": "Compute/Server", ...}
  Output: {"company": "NVIDIA Corporation (NVDA)", "role": "Compute/Server",
           "segment_weight": 0.40, ...}

DO NOT:
- Change any other field in the record.
- Hard-code the weights inside this function — always use schema.SEGMENT_WEIGHTS.
- Return a new list of records — modify in place and return the same list.
"""

from schema import SEGMENT_WEIGHTS


def run(records: list[dict]) -> list[dict]:
    # TODO: implement this agent
    # Loop through records, assign segment_weight from SEGMENT_WEIGHTS
    # Return the updated records list
    return records