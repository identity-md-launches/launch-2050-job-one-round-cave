# ZipBudget — bounded metadata preflight

Quickly check a ZIP's declared file count and uncompressed byte total without
reading member payloads or extracting anything. Python standard library only;
keep the shipped sibling `../zipgate/` and `../safezip/` folders together.
No installation, network, wallet, environment lookup or transaction is needed.

From the repository root, run this one-command offline demonstration:

```sh
python3 -B line-2/tools/zipbudget/demo.py
```

Tried here: the bundled historical public IMD API description (23,132 bytes,
provenance in `../safezip/sample-source.json`) passed an exact byte budget.
A one-byte-smaller budget was refused. A directory cap of one byte was refused
before Python's ZIP parser. The accepted report's digest was then passed to
ZipGate, which fully validated the payload against those identical ZIP bytes.
No extraction or live API request occurred; this does not claim fresh data.

For a ZIP already inside your workspace:

```sh
python3 -B line-2/tools/zipbudget/zipbudget.py incoming.zip --max-files 100 --max-bytes 1000000 --max-entries 1000 --archive-bytes 33554432 --directory-bytes 2097152
```

Paths must stay inside the current working directory without symlinks. Missing
or nonregular sources are refused. The API keeps the original three positional
arguments: `inspect(path, max_files, max_bytes)`. New limits are keyword-only,
with the defaults shown above. Every limit must be a positive integer (API
booleans are rejected). All ZIP entries, including directories, consume the
`max_entries` gate; only nondirectory entries consume `max_files` and `max_bytes`.

Success exits 0; a declared file/byte budget breach exits 1; malformed archives,
parser bounds, I/O errors or invalid options exit 2. A report retains the old
`ok`, `files`, `bytes` and successful `entries` fields. New fields include:

- `archive_sha256`: digest of the exact captured archive, for later digest-bound
  ZipGate inspection/extraction. A digest does not authenticate a publisher.
- `archive_bytes` and `preflight`: captured size and central-directory counts.
- `content_checked: false`: metadata preflight never validates member data.
- `counts_complete`: false on early budget breach; refused counts are partial.

## Bounds and limitations

Before `ZipFile` is constructed, input capture is limited to `archive_bytes`
(with one extra byte read to detect growth). ZipGate checks both declared and
actual directory entry counts and the directory's byte length. Parsing and
reporting then use that same in-memory snapshot, so replacing the pathname
cannot change the reported digest or inventory. No member is decompressed.

ZipGate's conservative classic, single-disk ZIP format restrictions apply:
no central ZIP64, executable prefix, trailing bytes or noncontiguous directory.
Valid unsupported layouts may be refused. See ZipGate's README for details.
This bounds input sizes, not exact interpreter memory or elapsed time; snapshot
copies and Python objects add overhead. Work in a cooperative directory without
hostile concurrent filesystem mutation. There is no operating-system sandbox.

An `ok` report **does not authorize extraction**. Member names, special types,
collisions, compression, CRCs and payload sizes remain unchecked; a traversal
name can pass metadata budgeting. Use ZipGate's full inspection/extraction
with the reported digest, and review the contents before executing anything.
Directory payload sizes are ignored here, as in the original counter; full
validation rejects nonempty directory entries. No coin is needed.

Run the adversarial checks:

```sh
python3 -B line-2/tools/zipbudget/selftest.py
```

Tried here: 20 new tests and 28 unchanged ZipGate tests passed. Cases include
exact boundaries, directory-only floods, forged entry counts, all truncations,
workspace/symlink refusal, invalid API options, growing input, pathname
replacement, no payload reads and CLI exit codes. These are local observations,
not a security certification.
