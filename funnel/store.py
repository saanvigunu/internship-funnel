"""Storage: one plain CSV you can open in any spreadsheet app.

Columns: id, company, role, stage, applied, last_touch, followup, link, notes
- stage is one of STAGES below (or a terminal state)
- dates are ISO (2026-11-26); followup is when you next owe this one a nudge

The file is yours. Nothing syncs anywhere.
"""

import csv
import os
import re

STAGES = ["watching", "applied", "oa", "interview", "onsite"]
TERMINAL = ["offer", "rejected", "ghosted", "withdrawn"]
ALL_STAGES = STAGES + TERMINAL

FIELDS = ["id", "company", "role", "stage", "applied",
          "last_touch", "followup", "link", "notes"]

DEFAULT_FILE = os.path.join(os.path.expanduser("~"), ".local", "share",
                            "internship-funnel", "applications.csv")


def data_file():
    return os.environ.get("FUNNEL_FILE", DEFAULT_FILE)


def load(path=None):
    path = path or data_file()
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row.setdefault("notes", "")
    return rows


def save(rows, path=None):
    path = path or data_file()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def valid_date(text):
    if not text:
        return True
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", text))


def add(rows, company, role, stage="applied", applied="",
        followup="", link="", notes="", today=""):
    if stage not in ALL_STAGES:
        raise ValueError(f"stage must be one of: {', '.join(ALL_STAGES)}")
    for label, value in (("applied", applied), ("followup", followup)):
        if not valid_date(value):
            raise ValueError(f"bad {label} date {value!r} (use YYYY-MM-DD)")
    new_id = max((int(r["id"]) for r in rows), default=0) + 1
    row = {"id": str(new_id), "company": company.strip(), "role": role.strip(),
           "stage": stage, "applied": applied or today, "last_touch": today,
           "followup": followup, "link": link.strip(), "notes": notes.strip()}
    rows.append(row)
    return row


def get(rows, row_id):
    for r in rows:
        if r["id"] == str(row_id):
            return r
    raise KeyError(row_id)


def move(rows, row_id, stage, today=""):
    if stage not in ALL_STAGES:
        raise ValueError(f"stage must be one of: {', '.join(ALL_STAGES)}")
    row = get(rows, row_id)
    row["stage"] = stage
    row["last_touch"] = today
    return row
