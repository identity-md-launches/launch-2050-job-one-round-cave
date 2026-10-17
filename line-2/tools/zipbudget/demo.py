#!/usr/bin/env python3
"""Offline public-data preflight, followed by digest-bound SafeZip validation."""
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile
from zipbudget import inspect, local_path, Rejected
from zipgate import process


def main():
    capture = local_path(Path(__file__).resolve().parents[1] / 'safezip/imd-openapi.json')
    with capture.open('rb') as reader:
        payload = reader.read(65537)
    assert hashlib.sha256(payload).hexdigest() == 'be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a'
    scratch = local_path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix='zipbudget-demo-') as folder:
        archive = Path(folder) / 'public-description.zip'
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as writer:
            writer.writestr('docs/imd/openapi.json', payload)
        report = inspect(archive, 1, len(payload), max_entries=1)
        assert report['ok'] and not report['content_checked']
        refusal = inspect(archive, 1, len(payload)-1)
        assert not refusal['ok']
        checked = process(archive, expected_sha256=report['archive_sha256'])
        assert checked['content_checked'] and checked['total_bytes'] == len(payload)
        try:
            inspect(archive, 1, len(payload), directory_bytes=1)
        except Rejected as error:
            directory_refusal = str(error)
        else:
            raise AssertionError('directory cap was ignored')
        print(json.dumps({'ok': True, 'source': 'https://api.imd.fun/openapi.json',
                          'historical_capture': True, 'network_used': False,
                          'report': report, 'byte_budget_refused': True,
                          'directory_refusal': directory_refusal,
                          'digest_bound_payload_validation_passed': True,
                          'extracted': False}, indent=2))


if __name__ == '__main__':
    main()
