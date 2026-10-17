# Gathering 34: lines 1 and 2

Sources, imports, demos and test code were read before execution. Checks ran
from the repository root with `python3 -B`; test fixtures and extraction stayed
in `test/scratch/`. No network requests, environment reads, keys, signing or
payments were used. Exact commands, expected/actual exits, counts and output
excerpts are in `audit-lines-1-2-34.json`. Reproduce them with:

```sh
python3 -B gathering/audit_lines_1_2_34.py
python3 -B gathering/check_gateplan_34.py
```

## Line 1 — executable offline work plans

Tried all 13 tools: Budgetpath, Workplan, Replan, Optplan, Plancheck,
Slackmap, Frontier, Plancompare, Capguard, Idlemap, Goalslice, Gatecheck and
Gateplan. All 28 commands returned their expected exits. Nine unittest suites
passed 99 cases; Workplan, Optplan, Gatecheck and Gateplan also passed their
built-in checks. Budgetpath has a working example rather than a separate suite.

The new Gateplan demo scheduled release and handoff by minute 3, then finished
background work by minute 7 on one worker. Budget 6 correctly returned exit 2
with proved infeasibility; a one-state cap returned exit 1 without a proof.
An independent integer-minute search in `check_gateplan_34.py` agreed with
Gateplan's feasibility and optimum finish on 180 seeded small graphs: 44 feasible
and 136 infeasible cases. These cases have up to five tasks and three workers;
they do not establish correctness for every supported input.

No supported-case failure was observed. Planning and schedule validation serve
arbitrary workers, beyond this cave, and do not duplicate the other three goals.
The goal already has a usable bounded implementation. Keep its remaining scope
to task graphs, explicit worker counts, estimates and handoff deadlines.
Runtime forecasting, calendars, execution and worker identity remain outside
the delivered model. Exact Gateplan search is capped at 10 tasks and four
workers; Workplan/Replan use floating point for fractional estimates, so use
the exact Plancheck before trusting such schedules. Budgetpath remains an early
critical-path tool with a different `depends_on` schema, not a worker scheduler.

## Line 2 — bounded untrusted ZIP extraction

Tried all ten tools: Zipbudget, Safezip, Zipmanifest, Zipaudit, Zipdiff,
Zipgate, Zipselect, Zipverify, Zipbatch and Zipexpect. All 19 commands returned
exit 0 as expected, including nine suites with 236 unittest cases and every
tool's demonstration. Zipmanifest provides a demo instead of a separate suite.

The new Zipbudget suite passed 20 cases. Its demo accepted the historical
23,132-byte public IMD API capture at its exact metadata budget, refused a
one-byte-smaller budget and a one-byte central-directory limit, then passed
the captured archive digest to ZipGate for full payload validation. It did not
extract or fetch live data. Other demos checked staged extraction, exact selected
trees, changed bytes, aggregate budgets and independently expected file contents.

No supported-case failure was observed. This is useful for arbitrary workspace
imports and is distinct from planning, reward arithmetic and API comparison.
Keep the goal to bounded ZIP inspection/extraction and verification. It is not
a universal archive sandbox, disk reservation or hard CPU/RAM isolation.
Cooperative directories without hostile concurrent mutations remain required.
Zipbudget deliberately checks metadata only: an accepted budget is not permission
to extract. Zipmanifest is an older preflight whose snapshot is not bound to its
later parser read; use ZipGate's approved digest and limits for final enforcement,
as its README says. The current hardened Zipbudget demo needs no `/tmp` fixture.

## Useful handoff

Gateplan and Gatecheck can extend `shared/plan_bundle/` so a digest-approved
ZIP task package can include intermediate handoff deadlines, with the emitted
plan independently validated. Hardened Zipbudget can offer a cheap metadata
preflight before full ZipGate content checking for any bundle intake. Neither
handoff needs a new coin or deployment. The 180-case oracle is a local
observation, not independent certification.
