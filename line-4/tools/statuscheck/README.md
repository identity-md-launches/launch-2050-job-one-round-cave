# StatusCheck

Detect response-schema changes hidden by OpenAPI status fallbacks. Python 3.9+,
standard library only; keep this folder beside the earlier line 4 analyzer folders.
No installation, network, wallet or configuration is needed. From the repository root:

```sh
python3 -B line-4/tools/statuscheck/statuscheck.py demo
```

The demo uses a real saved public IMD operation, replacing its response declarations
**hypothetically in memory**. An old `2XX` string response acquires an explicit
`200` integer response. StatusCheck finds the schema incompatibility that an
exact-selector-only comparison leaves for review. It reports one potential break
and two reviews, then exits 0. These declarations are not claims about IMD behavior.
No described operation is invoked.

Compare saved JSON descriptions inside the current workspace:

```sh
python3 -B line-4/tools/statuscheck/statuscheck.py compare line-4/tools/apidelta/imd-openapi.json line-4/live-openapi-34.json
```

Compare exits: **0** no detected break, **1** potential breaking change, **2**
invalid/unsupported input or resource/file error, **3** unresolved review only.
Reports on stdout include exact input-byte SHA-256 hashes. A 0 is a pass only for
the supported static subset, not a runtime compatibility guarantee.

## What it adds

For every common inline top-level path operation, enumerate HTTP codes 100–599.
Select an exact code first, then its uppercase class range (`1XX` through `5XX`),
then `default`. This follows the official
[OpenAPI 3.1 Responses Object](https://spec.openapis.org/oas/v3.1.0.html#responses-object).
Group codes with the same old/new selector pair and report their exact sets in
`selector_groups`; the finding points to the selected new declaration, or the
old declaration when coverage disappears. No invented JSON-pointer path is used.

When both selected declarations exist but their keys differ, reuse the inherited
response-direction media and schema rules across those declarations. An old
response allowing number and a new response allowing integer is safe for that
type rule; the reverse is potentially breaking. Selector changes always retain a
review because status emission and client dispatch are unknown. Losing description
coverage is a review, not proof that the server stopped returning a status.

Earlier analyzers still compare matching keys and retain **all** their findings,
including reviews. Non-content metadata across remapped selectors gets a broad
review; headers and links are not individually analyzed across different keys.
Unchanged selector spelling with a changed reference target remains covered by
the inherited analyzers. Local references are resolved independently in each input;
no external reference is fetched.

All response selectors and resolved response objects in common operations are
validated, even when unchanged: exact 100–599, uppercase class ranges, `default`,
and ignored `x-` extensions only. Content must be an object. This is not complete
OpenAPI validation. Unused components, removed/added operations, callbacks and
webhooks remain outside this extension's validation scope.

## Limits

At most 20,000 concrete-status visits (40 common operations), plus inherited
limits of 1 MiB per input, 50,000 JSON nodes, depth 80, 20,000 schema visits,
2,000 findings and earlier security/server/header/parameter budgets. A limit
refuses the entire comparison; it never returns a partial pass. Grouping avoids
repeating one schema analysis per status. Unsupported schema composition,
reference semantics, float precision and all earlier limitations remain.

This is conservative description analysis. It does not prove a status or value
can occur, infer undocumented runtime acceptance, evaluate full schema
satisfiability, run a client or call an API. Changes to annotations can leave
reviews even when the interpreted schemas agree. Static comparison needs no
coin, price, balance or payment.

## What happened when tried

On 2026-10-17 all **22 new tests** and **200 inherited tests** passed (14 suites,
222 tests). The selector oracle independently painted concrete status tables for
256 subsets, then checked all 500 statuses: 128,000 precedence comparisons.
Other checks cover exact/range/default overrides, response direction, fallback
following deletion, added/lost coverage, local references and cycles, unchanged
invalid selectors, malformed operations, media changes, inherited findings,
resource refusal, nonmutation, deterministic ordering and all four CLI exits.

A read-only GET of `https://api.imd.fun/openapi.json` with User-Agent
`Pepeolithic-StatusCheck/34.0` returned 23,132 bytes identical to the historical
capture (SHA-256 `be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a`).
Comparing them found five operations and zero findings. No described API operation
was called. Evidence: [check results](../../check-results-34.json) and
[public capture](../../live-openapi-34.json). These are local observations.

```sh
python3 -B line-4/tools/statuscheck/selftest.py
python3 -B line-4/check-34.py
```

The second command reruns all 14 suites and offline demos/capture comparisons;
optional `--live` repeats the public-description GET and refreshes this round's
capture and evidence only.
