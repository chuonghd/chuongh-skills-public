"""Daily spend alarm: halt generation each time today's spend crosses another $10 step.

Today's spend is summed from the ledger (successful runs, local date). At $10 the
script stops before calling any API until the user acknowledges that step with
`--ack-daily-spend 10`; the acknowledgement is stored for the day, so generation
continues until $20 needs `--ack-daily-spend 20`, and so on. Each day starts fresh.
"""

import json
from datetime import date, datetime

ALERT_STEP_USD = 10
ACK_FILE = "daily-spend-ack.json"
HALT_EXIT_CODE = 3  # distinct from errors (1) and argparse usage (2)


def spent_today(ledger_path):
    """Total cost_usd of today's successful generations."""
    if not ledger_path.exists():
        return 0.0
    today, total = date.today(), 0.0
    for line in ledger_path.read_text().splitlines():
        rec = json.loads(line)
        if rec.get("status") == "ok" and rec.get("cost_usd") and datetime.fromisoformat(rec["created_at"]).date() == today:
            total += rec["cost_usd"]
    return total


def _acknowledged_today(store):
    path = store / ACK_FILE
    data = json.loads(path.read_text()) if path.exists() else {}
    return data.get("acknowledged_usd", 0) if data.get("date") == date.today().isoformat() else 0


def status(store, ledger_path):
    """{spent_today_usd, reached_usd, acknowledged_usd, halted} for dry runs and checks."""
    spent = spent_today(ledger_path)
    reached = int(spent // ALERT_STEP_USD) * ALERT_STEP_USD  # highest $10 step reached today (0 if none)
    acked = _acknowledged_today(store)
    return {"spent_today_usd": round(spent, 4), "reached_usd": reached, "acknowledged_usd": acked,
            "halted": reached > 0 and acked < reached}


def check(store, ledger_path, ack_usd):
    """Record a valid acknowledgement, then halt (exit 3) if today's reached step is still unacknowledged."""
    st = status(store, ledger_path)
    if ack_usd is not None:
        if ack_usd != st["reached_usd"] or ack_usd == 0:
            raise SystemExit(f"--ack-daily-spend {ack_usd} doesn't match today's alert. Today's spend is ${st['spent_today_usd']:.2f}; "
                             + (f"the step to acknowledge is {st['reached_usd']}." if st["reached_usd"] else "no alert is active."))
        (store / ACK_FILE).write_text(json.dumps({"date": date.today().isoformat(), "acknowledged_usd": ack_usd,
                                                  "acknowledged_at": datetime.now().astimezone().isoformat()}, indent=2))
        st["acknowledged_usd"], st["halted"] = ack_usd, False
    if st["halted"]:
        print(f"DAILY SPEND ALERT: today's image generation spend is ${st['spent_today_usd']:.2f}, "
              f"past the ${st['reached_usd']} alert. Nothing was generated.\n"
              f"Ask the user whether to continue. Only if they say yes, re-run with --ack-daily-spend {st['reached_usd']} "
              f"(generation then continues until ${st['reached_usd'] + ALERT_STEP_USD}).")
        raise SystemExit(HALT_EXIT_CODE)
    return st
