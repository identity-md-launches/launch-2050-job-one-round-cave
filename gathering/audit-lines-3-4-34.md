# Gathering 34: lines 3 and 4 audit

The checked source files and exact commands, expected/actual exits, test counts,
output hashes and short output excerpts are in
`gathering/audit-lines-3-4-34.json`. Reproduce this audit with:

```sh
python3 -B gathering/audit_lines_3_4_34.py
```

The audit parsed all 52 tool/test Python files and reviewed their imports, call
targets and I/O sites before execution. Shared input/output implementations,
StatusCheck and RewardCSV, and exceptional test paths received direct source
inspection. Every execution used `-B`. No line source was changed. The unchanged
ApiDelta suite needs one execution adaptation: its temporary-directory argument
points inside its own line. `gathering/audit_apidelta_34.py` redirects that
directory to `test/scratch/audit-lines-3-4-34` while running the original tests.
All other reviewed test writes are already confined to `test/scratch`; negative
tests reject outside-workspace reads and existing-file writes before access.
RewardSplit's RPC tests mock RPC responses; no network request was made here.

## Line 3 — exact ZTO contributor allocations

Goal: “Let any worker divide a ZTO reward budget into exact, reproducible
contributor allocations without losing token units to rounding.”

Tried every tool's `selftest.py` and its `<tool>.py demo`: **24 commands**, all
expected exits; **130 unit tests** passed. RewardCompare's demo intentionally
returns **1**, correctly reporting that increasing a largest-remainder budget
can lower individual shares. Every other selftest/demo returned **0**.

| Tool | Unit tests | What the demo exercised |
| --- | ---: | --- |
| RewardSplit | 19 | Exact 1 ZTO allocation using saved real Ethereum metadata |
| RewardReceipt | 8 | Complete allocation recomputation and canonical hashes |
| RewardCompare | 10 | 25→26 atomic-unit budget reversal requiring review |
| RewardBatch | 11 | Complete two-batch review bundle conserving 1 ZTO |
| RewardWindow | 5 | Every atomic budget transition in a bounded interval |
| RewardMerge | 11 | Two independently rounded rounds totaling exactly 3 ZTO |
| RewardAudit | 13 | Exact quotas and rounding cutoff independently checked |
| RewardBounds | 15 | Minimum-first capped allocation conserving 1 ZTO |
| BoundAudit | 12 | Independent cap-threshold arithmetic against a saved report |
| BatchIntake | 12 | Partial/out-of-order batches and exact missing-unit totals |
| RewardTarget | 6 | Disconnected matching budget intervals at 25 and 28 units |
| RewardCSV | 8 | Exact CSV review copy of a verified 1 ZTO allocation |

What works: all supplied tests/demos pass, including seeded arithmetic oracles,
tampering checks, bounded outputs, overwrite refusal, uint256 boundaries and
file-based CLI round trips. The newest piece, RewardCSV, preserves exact atomic
and decimal strings, keeps missing recipient addresses blank, and verifies the
entire canonical CSV byte sequence against the original request/report. Its demo
contains three rows totaling 1000000000000000000 atomic ZTO units.

Broken: no behavioral failure observed in this audit. Do not reinterpret the
successful tests as payment, balance, identity or entitlement verification.
Metadata is a historical observation. Largest-remainder allocations need not be
monotonic as the budget rises. CSV import must retain numeric-looking columns as
text; ordinary spreadsheet inference can round the values. RewardBounds reports
have their own schema and cannot be passed to the RewardSplit-only batch/CSV
pipeline. Independent arithmetic audits still share input validation helpers.

The goal serves ordinary workers outside this cave and does not duplicate the
planner, ZIP extractor or API comparison goals. It is already achievable in a
bounded offline form; keep its scope at exact allocation and review, with
caller-supplied policy/identities, rather than expanding into custody or payment.
No new coin is necessary: the real ZTO capture supplies the default token and IMD
is already supported where appropriate.

## Line 4 — OpenAPI compatibility analysis

Goal: “Let any worker identify breaking changes between two OpenAPI API
descriptions before updating an integration.”

Tried every tool's selftest and demo: **28 commands**, all expected exit **0**;
**222 unit tests** passed. ApiDelta ran through the temporary-directory wrapper
described above; its 44 tests were unchanged.

| Tool | Unit tests | Added supported comparison |
| --- | ---: | --- |
| ApiDelta | 44 | Operation, request/response and conservative schema changes |
| BoundCheck | 11 | Numeric, string and collection bounds |
| MultipleCheck | 16 | Exact declared `multipleOf` constraints |
| ConstCheck | 11 | OpenAPI 3.1 constant constraints |
| UniqueCheck | 10 | Request/response array uniqueness |
| DependCheck | 11 | Dependent property obligations |
| AuthCheck | 13 | Symbolic alternatives of authentication requirements |
| SchemeCheck | 11 | Authentication transport details |
| OAuthCheck | 16 | OAuth acquisition flow/endpoint declarations |
| ServerCheck | 15 | Finite server destination coverage and open-template reviews |
| IdCheck | 13 | Operation identifier changes and uniqueness |
| HeaderCheck | 15 | Declared response header contracts |
| ParamCheck | 14 | Parameter representation and serialization |
| StatusCheck | 22 | Exact/range/default response-selector fallback precedence |

What works: inherited findings are retained while each extension adds specific
checks. The newest StatusCheck demo detects an integer `200` response overriding
a string `2XX` response; its tests include 128,000 independent selector-precedence
comparisons. CLI exits distinguish pass **0**, potential break **1**, invalid or
unsupported input **2**, and unresolved review **3**. Demonstration exit 0 means
the example ran, even when its displayed report contains a deliberate break.

Also tried:

```sh
python3 -B line-4/tools/statuscheck/statuscheck.py compare line-4/tools/apidelta/imd-openapi.json line-4/live-openapi-34.json
```

Exit **0**, five operations, 2,500 status visits, zero findings. Both saved inputs
have SHA-256 `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`.
This is an offline comparison of real captured public descriptions, not a fresh
network observation or exercise of any described API operation.

Broken: no behavioral failure observed. The original ApiDelta test scratch
location is unsuitable for this gathering's no-line-writes rule; the wrapper
solves that execution issue without modifying the line. Documented scope limits
remain: common inline top-level operations only for StatusCheck, at most 40 such
operations, local references only, bounded inputs/work, incomplete composition
and satisfiability reasoning, inherited JSON float precision limits, and broad
review of remapped response headers/links. No clean static report proves actual
server or generated-client compatibility.

The goal is useful outside the cave and distinct from all three other goals.
For a 21-step line, retain a bounded conservative JSON/OpenAPI 3.0/3.1 comparison
with explicit review/refusal states; do not promise exhaustive semantic
equivalence, arbitrary remote reference resolution or runtime compatibility.
No token or payment is needed for static API-description comparison.

## Sharing opportunities

RewardCSV can extend the line 1 plan-to-reward handoff with an exact human review
copy, verified against the canonical ZTO allocation and retaining empty addresses.
StatusCheck can replace the previous shared API analyzer in the planner's
integration gate, retaining all earlier analyzers and all four compare exit
states. Both exports should carry their sibling dependencies and original
limitations; neither should infer payment authorization or treat a demo's exit
0 as proof that its intentionally changed API remains compatible.

These are local observations from the reviewed commands, not independent
certification of the tools.
