# internship-funnel

A local CLI that treats internship applications like a funnel: stages,
follow-up dates, and conversion stats computed from your own data.

I built this because my applications lived in a spreadsheet I stopped
opening. The questions I actually have are smaller: what do I owe a
nudge today, what's gone quiet, and is my funnel working - answered from
the terminal, from my own file.

## usage

```bash
python3 -m funnel sample                          # load the fictional sample to try it
python3 -m funnel add "Acme" "SWE Intern" --followup 2026-12-01
python3 -m funnel list --stage interview
python3 -m funnel move 7 oa                       # stage transitions
python3 -m funnel followup 7 2026-12-05           # when you next owe a nudge
python3 -m funnel note 7 "recruiter is Mia"
python3 -m funnel due                             # follow-ups due or overdue
python3 -m funnel stale                           # active apps untouched 14+ days
python3 -m funnel stats                           # the funnel, from your data
```

stdlib only, nothing to install. Tests:

```bash
python3 -m unittest discover    # 26 tests, no network
```

## the stages

`watching` is a wishlist (opens later, apply then). The funnel itself:
`applied -> oa -> interview -> onsite -> offer`, with `rejected`,
`ghosted` and `withdrawn` as honest endings. Watching rows never count in
the funnel math.

## where your data lives

One plain CSV: `~/.local/share/internship-funnel/applications.csv`
(override with `FUNNEL_FILE`). Open it in any spreadsheet app, edit it,
back it up, delete it. Nothing syncs anywhere.

## honesty notes

- Every rate in `stats` is computed from YOUR file only, printed with
  its n=. There is no benchmark in this tool, because it doesn't know
  one - a 60% applied->oa rate means exactly what your own rows say,
  nothing more.
- Rejected/ghosted/withdrawn rows are excluded from stage-by-stage rates,
  and the output says so: a rejection email doesn't say which stage it
  came from, so the tool refuses to guess.
- `data/sample.csv` is 14 FICTIONAL companies (example.invalid links) for
  trying the commands. Your real list is yours; it never belongs in a
  repo.
