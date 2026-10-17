#!/usr/bin/env python3
"""Compare a hypothetical response fallback change in SHA-approved API ZIPs."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

import api_bundle


def demo():
    capture = Path(__file__).with_name('imd-openapi.json').read_bytes()
    old = json.loads(capture)
    operation = old['paths']['/requests/quote']['post']
    operation['responses'] = {'2XX': {'description': 'Hypothetical response',
        'content': {'application/json': {'schema': {'type': 'string'}}}}}
    new = copy.deepcopy(old)
    new['paths']['/requests/quote']['post']['responses']['200'] = {
        'description': 'Hypothetical response',
        'content': {'application/json': {'schema': {'type': 'integer'}}}}
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='status-bundle-', dir=scratch) as folder:
        paths, hashes = [], []
        for name, document in [('old', old), ('new', new)]:
            path = Path(folder) / (name + '.zip')
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr(zipfile.ZipInfo('docs/openapi.json'), json.dumps(document))
            paths.append(path)
            hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
        args = dict(member='docs/openapi.json', old_sha256=hashes[0], new_sha256=hashes[1],
                    seconds=10)
        previous = api_bundle.compare(*paths, parameters=True, **args)
        changed = api_bundle.compare(*paths, statuses=True, **args)
        unchanged = api_bundle.compare(paths[0], paths[0], member=args['member'],
                    old_sha256=hashes[0], new_sha256=hashes[0], statuses=True)
        assert previous['status'] == 'review_required'
        assert unchanged['findings'] == []
        assert changed['status'] == 'breaking'
        assert any(f['code'] == 'schema_type_incompatible' for f in changed['findings'])
        assert changed['selector_groups'] == [{
            'operation': '/paths/~1requests~1quote/post',
            'old_selector': '2XX', 'new_selector': '200', 'statuses': [200]}]
        return dict(baseline_source='https://api.imd.fun/openapi.json',
                    baseline_sha256=hashlib.sha256(capture).hexdigest(),
                    trial='Hypothetical 200 integer override of a 2XX string response on a saved IMD path.',
                    network_used=False, files_extracted=0,
                    previous_status=previous['status'], unchanged_status=unchanged['status'],
                    changed=changed)


if __name__ == '__main__':
    print(json.dumps(demo(), indent=2))
