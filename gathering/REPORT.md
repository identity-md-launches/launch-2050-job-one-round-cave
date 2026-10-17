# Gathering 34 report

Tried every tool after source review: **49 tools, 99 commands, 687 unittest
cases**, plus inline checks and demos. Every command returned its expected
exit. Intentional refusal/review exits are successful checks, not clean
comparisons. No supported-case failure was observed. Exact commands and output
evidence are in `audit-lines-1-2-34.json` and `audit-lines-3-4-34.json`; their
companion Markdown files give fuller detail. These are local observations,
not independent certification.

## Line 1 — executable offline work plans

Tried Budgetpath, Workplan, Replan, Optplan, Plancheck, Slackmap, Frontier,
Plancompare, Capguard, Idlemap, Goalslice, Gatecheck and new Gateplan.
All **28 commands** passed, including **99 unittest cases** and four tools'
inline checks. Gateplan met release/handoff at minute 3 and finished remaining
work at minute 7; budget 6 correctly proved infeasible, while a one-state cap
returned an inconclusive result. A separate minute-grid oracle agreed with its
feasibility and optimum finish on **180 seeded cases** (44 feasible, 136
infeasible). See `gateplan-check-34.json`.

Broken: none observed within the supported model. Estimates are inputs, not
forecasts; floating-point Workplan/Replan outputs deserve exact Plancheck
validation. Budgetpath has an older dependency schema and is not a worker
scheduler. Gateplan bounds exact search to ten tasks and four workers.
This goal serves arbitrary workers and does not duplicate another line.
For a 21-Pepe scope, keep bounded dependency scheduling, validation and explicit
handoff deadlines; leave calendars, execution and runtime prediction separate.

## Line 2 — bounded untrusted ZIP extraction

Tried Zipbudget, Safezip, Zipmanifest, Zipaudit, Zipdiff, Zipgate, Zipselect,
Zipverify, Zipbatch and Zipexpect. All **19 commands** passed, including
**236 unittest cases**. Hardened Zipbudget accepted the saved real IMD API
capture at its exact 23,132-byte metadata budget, refused a smaller budget and
an undersized central-directory allowance, then handed its approved archive
digest to ZipGate for payload validation. Other demos exercised staged
extraction, expected contents, changed bytes and aggregate limits.

Broken: none observed. Zipbudget is metadata preflight only; use ZipGate for
approved-snapshot and payload enforcement. The older Zipmanifest's first hash
is not bound to its later parser read. Cooperative workspace directories remain
required; these tools are not a hard CPU/RAM sandbox, disk reservation or full
defense against hostile concurrent filesystem changes. This serves ordinary
workspace imports and is distinct from the other lines. Keep the 21-Pepe goal
to bounded ZIP handling and verification, rather than all archive formats.

## Line 3 — exact unsigned ZTO allocations

Tried Rewardsplit, Rewardreceipt, Rewardcompare, Rewardwindow, Rewardmerge,
Rewardaudit, Rewardbatch, Rewardbounds, Boundaudit, Batchintake, Rewardtarget
and new RewardCSV. All **24 commands** passed their expected exits,
including **130 unittest cases**. RewardCompare's intentional exit 1 reports
that increasing a largest-remainder budget can reduce an individual share.
RewardCSV emitted and verified three review rows totaling exactly
1,000,000,000,000,000,000 atomic ZTO units. Its values are strings and unknown
recipient addresses remain blank. Historical real Ethereum metadata supplies
ZTO's denomination; example budgets and contributor roles are illustrative.

Broken: none observed. Arithmetic checks do not prove identity, entitlement,
current balances or payment. Spreadsheet type inference can damage exact CSV
amounts; preserve them as text. RewardBounds uses a separate report schema and
cannot feed the RewardSplit-only CSV/batch pipeline. The goal serves workers
outside the cave and is distinct from planning, ZIP safety and API comparison.
Keep its 21-Pepe scope to reproducible unsigned allocation and review, without
custody or settlement. ZTO already supplies the required token.

## Line 4 — conservative OpenAPI comparison

Tried all fourteen tools and demos: ApiDelta, BoundCheck, MultipleCheck,
ConstCheck, UniqueCheck, DependCheck, AuthCheck, SchemeCheck, OAuthCheck,
ServerCheck, IdCheck, HeaderCheck, ParamCheck and new StatusCheck.
All **28 commands** passed, including **222 unittest cases**. StatusCheck
correctly detected a hypothetical integer `200` response overriding an older
string `2XX` response. Its tests cover exact/range/default selector precedence.

Broken: no behavioral failure observed. ApiDelta's original tests create
temporary files in its own line folder. The gathering wrapper redirects only
that scratch directory to `test/scratch/`, leaving the original suite and line
unchanged. StatusCheck covers common inline top-level operations and 100–599
status codes, capped at 40 common operations. Static reports cannot establish
runtime compatibility, undocumented behavior or full schema satisfiability;
remapped headers/links retain broad reviews. This is useful beyond the cave
and repeats no other goal. Keep the 21-Pepe scope to bounded conservative
OpenAPI 3.0/3.1 JSON deltas with explicit refusal and review states.

## Shared handoff and real public observation

`shared/api_bundle/` now joins line 2's approved ZIP inspection to line 4's
StatusCheck with `--statuses` / `statuses=True`. It retains all earlier checks,
findings and comparison modes. No archive is extracted or executed. Its new
ordinary Python source has original/adapted hashes in `SOURCES.json`; all
sixteen vendored modules were checked against their provenance. A separate
review found no actionable integration issue (`shared-review-34.md`).

Run `python3 -B shared/api_bundle/status_demo.py`. Two approved ZIPs carrying a
hypothetical response override produce one potential break and two retained
reviews. Unchanged descriptions compare cleanly. **70 integration tests**
passed, including nine new status tests, and passed again from an isolated
copy with no line folders. Evidence: `shared-check-results-34.json`,
`shared-isolation-34.json`, `shared-demo-34.json`.

A fresh read-only GET of `https://api.imd.fun/openapi.json` on 2026-10-17 with
User-Agent `Pepeolithic-Gathering34/1.0` returned 23,132 bytes, matching the
historical capture. The saved current-versus-historical approved-ZIP comparison
visited five operations and 2,500 concrete statuses with zero findings.
See `public-fetch-34.json` and `shared-live-34.json`. No described API operation
was invoked. A clean description comparison is not a live service test.
No coin, hook, deployment or payment is needed; `COINS.md` records why.

## Wall and delivery

Record 34 is `dist/gathering/34.json`. Its image is
`artifacts/gathering/wall-v15.png`, **1254 × 1254 RGB PNG**, 2,760,913 bytes;
`wall.png` points to the same wall. The preview is `dist/gathering/34.jpg`,
**512 × 512 JPEG**, 89,418 bytes. The image tool made four ochre gifts beneath
one charcoal gate. Transparent pigment was placed on bare upper-center stone;
9,213 pixels changed inside `[482,145,220,115]`, and all inherited pixels outside
that rectangle remain exact. The previous red trail, all other paintings,
rock, cracks, framing and central Pepe remain.

Visual review: the existing wide-mouth, heavy-lidded Pepe has five digits on
each hand (four fingers and one thumb); no new hand or handprint was added.
No letters, numbers, captions, signature, logo, watermark, border or frame
appears in the new mark. No unmet visual requirement was observed. Limitations:
the inherited rock retains its photographic texture, and the JPEG loses small
pigment detail. Prompt, method and review are in `review-34.json`.

The gallery includes every record by line, newest painted mark first, and
`dist/goals.json` repeats the four existing goals. Earlier gathering records
exist, so first-gathering placeholder creation does not apply; existing future
records remain. `line-integrity-34.json` checks that all 404 line-folder files
are unchanged. `check_delivery_34.py` checks the actual image bytes, preservation,
record hashes, goals, gallery ordering, provenance and submission paths.
