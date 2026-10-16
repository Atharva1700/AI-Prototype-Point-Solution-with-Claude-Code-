"""Measures the prototype's time per claim on a fixed, generated batch of claims.

Measures compute time only. It does not measure the manual process, which needs a
time study on the real team (see docs/before_after.md).
"""

import random
import sys
import time
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.policy import check_claim  # noqa: E402

N = 2000
SEED = 123


def generate(n, today):
    rng = random.Random(SEED)
    claims = []
    for _ in range(n):
        claims.append({
            "employee": f"E{rng.randint(1, 50)}",
            "merchant": f"M{rng.randint(1, 30)}",
            "category": rng.choice(["travel", "meals", "lodging", "supplies"]),
            "amount": Decimal(rng.randint(100, 60000)) / 100,
            "expense_date": today - timedelta(days=rng.randint(0, 70)),
            "has_receipt": rng.random() < 0.8,
        })
    return claims


def main():
    today = date.today()
    claims = generate(N, today)
    history = claims[:200]

    start = time.perf_counter()
    verdicts = [check_claim(c, history, today)["verdict"] for c in claims]
    direct = time.perf_counter() - start

    client = TestClient(app)
    payloads = [{
        "claim": {**c, "amount": str(c["amount"]), "expense_date": c["expense_date"].isoformat()},
        "history": [],
    } for c in claims]
    start = time.perf_counter()
    statuses = [client.post("/claims/check", json=p).status_code for p in payloads]
    api = time.perf_counter() - start

    counts = {v: verdicts.count(v) for v in sorted(set(verdicts))}
    print(f"claims: {N}   seed: {SEED}")
    print(f"policy only: {direct * 1000 / N:.3f} ms per claim")
    print(f"HTTP round trip in-process: {api * 1000 / N:.3f} ms per claim")
    print(f"all responses 200: {all(s == 200 for s in statuses)}")
    print(f"verdict mix: {counts}")


if __name__ == "__main__":
    main()
