"""Funnel stats computed from YOUR rows only.

Every number here is a count or a rate over your own file, printed with
its n= so small samples look like small samples. There are no benchmarks:
this tool does not know and will not invent what a "good" conversion rate
is.
"""

from datetime import date

from .store import STAGES, TERMINAL

# the forward path, best case; 'watching' is a wishlist, not a funnel stage
ORDER = ["applied", "oa", "interview", "onsite", "offer"]
REACHED = {s: i for i, s in enumerate(ORDER)}  # stage -> furthest rank


def stage_counts(rows):
    counts = {}
    for r in rows:
        counts[r["stage"]] = counts.get(r["stage"], 0) + 1
    return counts


def furthest(row):
    """Best stage a row ever reached: current stage, unless it's terminal
    and we can't tell how far it got - then we count it by its terminal
    state honestly (rejected could have been at any stage)."""
    stage = row["stage"]
    if stage in REACHED:
        return REACHED[stage]
    return None


def conversions(rows):
    """For each forward stage, how many of the rows that reached the
    previous stage also reached this one. Rejected/ghosted rows are left
    out of 'reached' math unless their current stage is on the forward
    path - a rejection doesn't say which stage it came from."""
    hits = {s: 0 for s in ORDER}
    for r in rows:
        f = furthest(r)
        if f is None:
            continue
        for s, i in REACHED.items():
            if i <= f:
                hits[s] += 1
    steps = []
    prev, prev_n = None, None
    for s in ORDER:
        n = hits[s]
        rate = (n / prev_n) if prev_n else None
        steps.append((prev, s, prev_n, n, rate))
        prev, prev_n = s, n
    unknown = sum(1 for r in rows
                  if furthest(r) is None and r["stage"] in TERMINAL)
    return steps, unknown


def due_followups(rows, today=None):
    today = str(today or date.today())
    due = [r for r in rows
           if r["followup"] and r["followup"] <= today
           and r["stage"] not in ("offer", "rejected", "ghosted", "withdrawn")]
    due.sort(key=lambda r: r["followup"])
    return due


def stale(rows, days=14, today=None):
    """Active rows with no touch in `days` days - the ghosting-your-own-
    pipeline check. Rows without an applied date are skipped."""
    today = date.fromisoformat(str(today or date.today()))
    out = []
    for r in rows:
        if r["stage"] in TERMINAL or r["stage"] == "watching":
            continue
        marker = r["last_touch"] or r["applied"]
        if not marker:
            continue
        age = (today - date.fromisoformat(marker)).days
        if age >= days:
            out.append((r, age))
    out.sort(key=lambda ra: -ra[1])
    return out


def summary(rows, today=None):
    counts = stage_counts(rows)
    return {
        "total": len(rows),
        "counts": counts,
        "active": sum(counts.get(s, 0) for s in STAGES[1:]),
        "offers": counts.get("offer", 0),
        "rejected": counts.get("rejected", 0),
        "due": len(due_followups(rows, today)),
    }
