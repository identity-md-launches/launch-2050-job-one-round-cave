# RewardCSV

RewardCSV makes a deterministic CSV review copy of a RewardSplit allocation, only after RewardReceipt recomputes and verifies the entire source report. Atomic units and decimal amounts are exported as exact strings, never floats. Every row carries the same canonical source-report SHA-256, Ethereum chain ID and real token contract. Missing recipient addresses remain empty; no recipient is invented. Zero-unit contributors remain present.

Run from the repository root, with Python's standard library and the sibling tools intact:

```sh
python3 -B line-3/tools/rewardcsv/rewardcsv.py demo
```

Tried here: the offline demo returned 0 and printed three illustrative address-free roles sharing exactly 1 ZTO. `build` has `333333333333333334` atomic units; `research` and `review` each have `333333333333333333`. This uses the bundled historical real Ethereum ZTO metadata, not a live balance or a hypothetical token. Nothing signs, sends, pays or posts.

For real inputs, retain the original request, exact allocation report and metadata capture:

```sh
python3 -B line-3/tools/rewardcsv/rewardcsv.py export --request REQUEST.json --report REPORT.json --output REVIEW.csv
python3 -B line-3/tools/rewardcsv/rewardcsv.py verify --request REQUEST.json --report REPORT.json --csv REVIEW.csv
```

Both commands accept `--metadata PATH`, defaulting to the inherited ZTO capture. Export defaults to stdout. A named output must be a new workspace file; overwrites are refused. Verification prints a JSON receipt containing the CSV hash and source verification receipt. Exit 0 means successful export or exact verification; exit 2 means invalid inputs, altered CSV, a resource limit or I/O error.

Columns are `id,address,units,amount,rounding_unit_awarded,chain_id,token_address,report_sha256`. Rows follow the source's ASCII ID ordering. Encoding is ASCII, all fields are quoted, and lines end with LF, including the final line. Verification compares exact bytes: even changing line endings, adding a BOM, reordering rows or resaving quotes is refused. It is an exact review-copy check, not a general CSV parser. This tool accepts RewardSplit reports only, not RewardBounds or RewardMerge schemas.

**Import every column as text in spreadsheet software.** CSV quoting does not stop automatic numeric conversion. Opening a CSV with default spreadsheet settings can round large integers, strip leading zeroes from IDs, or change decimals. Keep the original CSV and JSON sources; verify the original bytes before relying on a copy. Token symbols and arbitrary labels are deliberately omitted. Contributor IDs already follow RewardSplit's restricted ASCII grammar and cannot begin with a formula operator. This does not guarantee the behavior of every spreadsheet importer.

Inputs and CSV outputs are bounded to 256 KiB each; source rosters are bounded to 1,000 contributors. Some otherwise valid large rosters produce an oversize CSV and are refused before output. Paths resolve inside the current workspace. Keep the original inputs: hashes cannot recover them. Historical token metadata is an observation, and unsigned hashes establish arithmetic/input agreement only, not identity, entitlement, custody, current balances or payment.

```sh
python3 -B line-3/tools/rewardcsv/selftest.py
```

Eight tests passed: 100 seeded round trips, exact large integers through uint256 maximum, zero rows, missing addresses, full source tampering, CSV/line-ending/BOM tampering, formula-like IDs, oversize refusal, and CLI export/verify/overwrite and duplicate-key checks. Test fixtures use `test/scratch/` and are removed automatically.
