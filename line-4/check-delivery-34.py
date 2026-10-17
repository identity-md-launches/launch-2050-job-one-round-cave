#!/usr/bin/env python3
"""Workspace-only round 34 artifact/record checks; no network or environment reads."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def git(*args):
    return subprocess.check_output(['git', *args])


def main():
    wall = Path('artifacts/line-4/wall-v15.png').read_bytes()
    canonical = Path('artifacts/line-4/wall.png').read_bytes()
    record = json.loads(Path('dist/line-4/34.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + hashlib.sha256(wall).hexdigest()
    assert wall == canonical
    assert wall[:8] == b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II', wall[16:24]) == (1254, 1254)
    attrs = record['attributes']
    assert all(set(a) == {'trait_type', 'value'} for a in attrs)
    assert [a['trait_type'] for a in attrs] == ['Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing']
    assert [a['value'] for a in attrs[:4]] == ['Lava', 'Line 4', 34, 'StatusCheck']
    assert type(attrs[2]['value']) is int
    records = sorted(Path('dist/line-4').glob('[0-9][0-9].json'))
    assert len(records) == 34 and records[-1].name == '34.json'
    older = git('ls-tree', '-r', '--name-only', 'HEAD', '--', 'dist/line-4').decode().splitlines()
    for name in older:
        assert Path(name).read_bytes() == git('show', 'HEAD:' + name), name
    assert Path('line-4/GOAL.md').read_bytes() == git('show', 'HEAD:line-4/GOAL.md')
    preview = Path('dist/line-4/34.jpg').read_bytes()
    assert preview == Path('artifacts/line-4/34.jpg').read_bytes()
    assert preview.startswith(b'\xff\xd8') and preview.endswith(b'\xff\xd9') and len(preview) < 100000
    paths = set(git('diff', '--name-only', 'HEAD').decode().splitlines())
    paths.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    allowed = ('line-4/', 'artifacts/line-4/', 'dist/line-4/', 'test/scratch/')
    assert all(p.startswith(allowed) for p in paths), sorted(paths)
    for name in paths:
        p = Path(name)
        if p.is_file() and not name.startswith(('artifacts/', 'test/scratch/')):
            assert p.stat().st_size <= 100000, name
    checks = json.loads(Path('line-4/check-results-34.json').read_text())
    assert len(checks['suites']) == 14 and all(s['exit'] == 0 for s in checks['suites'])
    assert checks['live']['comparison']['operations_compared'] == 5
    assert checks['live']['comparison']['findings'] == []
    result = dict(status='passed', number=34, earlier_files_unchanged=len(older), goal_unchanged=True,
                  scope_passed=True, size_limits_passed=True, suites_passed=14,
                  wall_dimensions=[1254,1254], wall_format='PNG', wall_bytes=len(wall),
                  preview_dimensions=[512,512], preview_format='JPEG', preview_bytes=len(preview),
                  sha256=hashlib.sha256(wall).hexdigest())
    Path('line-4/delivery-check-34.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
