#!/usr/bin/env python3
"""Report whether a ZIP's declared entries fit explicit count/byte budgets."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'zipgate'))
from zipgate import Rejected, directory_gate, local_path, positive


def inspect(path, max_files, max_bytes, *, archive_bytes=33554432,
            max_entries=1000, directory_bytes=2097152):
    """Budget declared metadata from one bounded snapshot; never read payloads.

    The returned digest binds this report to the captured archive, not a later
    version of its path. An ok report does not approve extraction or content.
    """
    for name, value in [('max_files', max_files), ('max_bytes', max_bytes),
                        ('archive_bytes', archive_bytes), ('max_entries', max_entries),
                        ('directory_bytes', directory_bytes)]:
        positive(name, value)
    source = local_path(path)
    if not source.is_file() or source.stat().st_size > archive_bytes:
        raise Rejected('archive missing, nonregular, or over archive byte limit')
    data = bytearray()
    with source.open('rb') as reader:
        if not stat.S_ISREG(os.fstat(reader.fileno()).st_mode):
            raise Rejected('archive must be regular')
        while True:
            chunk = reader.read(min(65536, archive_bytes - len(data) + 1))
            if not chunk:
                break
            if len(data) + len(chunk) > archive_bytes:
                raise Rejected('archive byte limit exceeded while reading')
            data.extend(chunk)
    gate = directory_gate(data, entries=max_entries, directory_bytes=directory_bytes)
    context = {'archive_sha256': hashlib.sha256(data).hexdigest(),
               'archive_bytes': len(data), 'preflight': gate,
               'content_checked': False}
    with io.BytesIO(data) as snapshot, zipfile.ZipFile(snapshot) as archive:
        total = 0
        entries = []
        for info in archive.infolist():
            if info.is_dir():
                continue
            total += info.file_size
            entries.append({"name": info.filename, "bytes": info.file_size})
            if len(entries) > max_files or total > max_bytes:
                return {"ok": False, "reason": "budget exceeded", "files": len(entries),
                        "bytes": total, "counts_complete": False, **context}
    return {"ok": True, "files": len(entries), "bytes": total, "entries": entries,
            "counts_complete": True, **context}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--max-bytes", type=int, default=1_000_000)
    parser.add_argument("--archive-bytes", type=int, default=33554432)
    parser.add_argument("--max-entries", type=int, default=1000)
    parser.add_argument("--directory-bytes", type=int, default=2097152)
    args = parser.parse_args(argv)
    if min(args.max_files, args.max_bytes, args.archive_bytes,
           args.max_entries, args.directory_bytes) < 1:
        parser.error("budgets must be positive")
    try:
        result = inspect(args.archive, args.max_files, args.max_bytes,
                         archive_bytes=args.archive_bytes, max_entries=args.max_entries,
                         directory_bytes=args.directory_bytes)
    except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError) as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
