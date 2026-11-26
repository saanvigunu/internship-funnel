"""internship-funnel command line.

    python3 -m funnel add "Company" "Role" [--stage applied] [--followup 2026-12-01]
    python3 -m funnel list [--stage interview]
    python3 -m funnel move <id> <stage>          # e.g. move 7 oa
    python3 -m funnel followup <id> <date>       # when you next owe a nudge
    python3 -m funnel note <id> "text"
    python3 -m funnel due                        # follow-ups due today or overdue
    python3 -m funnel stale [days]               # active apps untouched 14+ days
    python3 -m funnel stats                      # the funnel, from your data only
    python3 -m funnel sample                     # load the labeled sample file

Data lives in ~/.local/share/internship-funnel/applications.csv
(override with FUNNEL_FILE). It's a plain CSV - open it anywhere.
"""

import sys
from datetime import date

from . import stats as st
from . import store

USAGE = __doc__


def _today():
    return str(date.today())


def _flag(args, name):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
        return ""
    return None


def cmd_add(args):
    positional = [a for a in args if not a.startswith("-")]
    flags = {f: _flag(args, f) for f in ("--stage", "--applied", "--followup",
                                         "--link", "--notes")}
    positional = [a for a in positional if a not in flags.values()]
    if len(positional) < 2:
        sys.exit('add needs a company and a role: add "Acme" "SWE Intern"')
    rows = store.load()
    try:
        row = store.add(rows, positional[0], positional[1],
                        stage=flags["--stage"] or "applied",
                        applied=flags["--applied"] or "",
                        followup=flags["--followup"] or "",
                        link=flags["--link"] or "",
                        notes=flags["--notes"] or "", today=_today())
    except ValueError as exc:
        sys.exit(str(exc))
    store.save(rows)
    print(f"added #{row['id']}: {row['company']} - {row['role']} [{row['stage']}]")


def cmd_list(args):
    rows = store.load()
    stage = _flag(args, "--stage")
    if stage:
        rows = [r for r in rows if r["stage"] == stage]
    if not rows:
        print("nothing here yet - `add` one or `sample` to see the shape")
        return
    for r in rows:
        fu = f"  (nudge {r['followup']})" if r["followup"] else ""
        print(f"#{r['id']:<3} [{r['stage']:<9}] {r['company']:<22} {r['role']}{fu}")
    print(f"{len(rows)} application(s)", file=sys.stderr)


def cmd_move(args):
    if len(args) < 2:
        sys.exit("move needs an id and a stage, e.g. `move 7 interview`")
    rows = store.load()
    try:
        row = store.move(rows, args[0], args[1], today=_today())
    except KeyError:
        sys.exit(f"no application #{args[0]}")
    except ValueError as exc:
        sys.exit(str(exc))
    store.save(rows)
    print(f"#{row['id']} {row['company']} -> {row['stage']}")


def cmd_followup(args):
    if len(args) < 2:
        sys.exit("followup needs an id and a date: followup 7 2026-12-01")
    if not store.valid_date(args[1]):
        sys.exit(f"bad date {args[1]!r} (use YYYY-MM-DD)")
    rows = store.load()
    try:
        row = store.get(rows, args[0])
    except KeyError:
        sys.exit(f"no application #{args[0]}")
    row["followup"] = args[1]
    store.save(rows)
    print(f"#{row['id']} {row['company']}: nudge on {row['followup']}")


def cmd_note(args):
    if len(args) < 2:
        sys.exit('note needs an id and text: note 7 "recruiter is Mia"')
    rows = store.load()
    try:
        row = store.get(rows, args[0])
    except KeyError:
        sys.exit(f"no application #{args[0]}")
    row["notes"] = (row["notes"] + " | " if row["notes"] else "") + " ".join(args[1:])
    store.save(rows)
    print(f"#{row['id']} {row['company']}: noted")


def cmd_due(args):
    rows = store.load()
    due = st.due_followups(rows)
    if not due:
        print("no follow-ups due. nice.")
        return
    print(f"{len(due)} follow-up(s) due:")
    for r in due:
        print(f"  #{r['id']:<3} {r['followup']}  {r['company']} - {r['role']} [{r['stage']}]")


def cmd_stale(args):
    days = int(args[0]) if args else 14
    rows = store.load()
    cold = st.stale(rows, days=days)
    if not cold:
        print(f"no active application has gone {days}+ days untouched")
        return
    print(f"active, untouched {days}+ days:")
    for r, age in cold:
        print(f"  #{r['id']:<3} {age}d  {r['company']} - {r['role']} [{r['stage']}]")


def cmd_stats(args):
    rows = store.load()
    if not rows:
        print("no data yet - `add` one or `sample` to see the shape")
        return
    s = st.summary(rows)
    print(f"{s['total']} applications: {s['active']} active, "
          f"{s['offers']} offer(s), {s['rejected']} rejected, "
          f"{s['due']} follow-up(s) due")
    counts = s["counts"]
    for stage in store.ALL_STAGES:
        if counts.get(stage):
            print(f"  {stage:<10} {counts[stage]}")
    print("\nconversions (of the rows that reached each stage):")
    steps, unknown = st.conversions(rows)
    for prev, stage, prev_n, n, rate in steps:
        if prev is None:
            print(f"  {stage:<10} {n} total")
        elif prev_n:
            print(f"  {prev} -> {stage:<9} {n}/{prev_n}"
                  + (f"  ({rate:.0%})" if rate is not None else ""))
    if unknown:
        print(f"  ({unknown} rejected/ghosted/withdrawn row(s) excluded - "
              f"a rejection doesn't say which stage it came from)")
    print("\nevery rate above is computed from YOUR file only - "
          "there is no benchmark to compare against here.")


def cmd_sample(args):
    import shutil
    src = store.os.path.join(store.os.path.dirname(store.os.path.abspath(__file__)),
                             store.os.pardir, "data", "sample.csv")
    dest = store.data_file()
    rows = store.load()
    if rows:
        sys.exit(f"your file already has {len(rows)} rows - not overwriting "
                 f"({dest}). Move it aside first if you want the sample.")
    store.os.makedirs(store.os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(src, dest)
    print(f"sample data loaded into {dest}")
    print("these are FICTIONAL companies for trying the commands - "
          "delete the file to start your real list.")


COMMANDS = {"add": cmd_add, "list": cmd_list, "move": cmd_move,
            "followup": cmd_followup, "note": cmd_note, "due": cmd_due,
            "stale": cmd_stale, "stats": cmd_stats, "sample": cmd_sample}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd = COMMANDS.get(argv[0])
    if cmd is None:
        print(USAGE, file=sys.stderr)
        return 2
    cmd(argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
