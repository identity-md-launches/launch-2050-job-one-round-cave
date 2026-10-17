# Gateplan

Gateplan finds an offline work schedule that meets both a final time budget and
named intermediate handoff deadlines. It accepts the same task graph as
Workplan and the same `gates` object as Gatecheck. It searches for a plan,
including choices that leave a worker idle so an upcoming handoff can start
promptly. It executes no task labels.

From the repository root, run the working example:

```sh
python3 -B line-1/tools/gateplan/gateplan.py --demo --workers 1 --budget 7
```

Observed locally: the one-worker plan starts `release`, finishes `handoff` at
minute 3, then finishes `background` at minute 7. With budget 6, it proves the
same input infeasible. Six built-in checks passed. An independent minute-grid
oracle agreed on 120 seeded small dependency graphs with handoff deadlines.

For your own JSON files, use:

```sh
python3 -B line-1/tools/gateplan/gateplan.py --tasks tasks.json --gates gates.json --workers 2 --budget 12
```

Example gates file: `{"gates":[{"id":"review","tasks":["build","test"],"due":9}]}`.
Each named task must finish by its gate's `due`; a task in several gates must
meet the earliest one. Successful output includes a complete `plan` suitable
for Plancheck and Gatecheck. Exit 0 means a feasible shortest gated plan was
found, 2 means exhaustive search proved infeasible, and 1 means invalid input
or the state cap prevented a proof. No partial schedule is returned with a
proof claim. A `--max-states` value up to 500000 can raise the search bound.

This exact search is deliberately bounded to **10 tasks**, **4 workers**, and
integer minute durations, due times and budgets from 0 to 10000 (task durations
must be positive). The default state cap is 100000. It reads only ordinary JSON
files inside the current workspace, at most 100 KB each. It uses only Python's
standard library plus the unchanged sibling Plancheck and Gatecheck sources.
Keep those sibling folders beside Gateplan when copying it. Estimates and
worker availability are caller supplied; this is no forecast of actual work.

Run the built-in checks with:

```sh
python3 -B line-1/tools/gateplan/gateplan.py --self-test
```
