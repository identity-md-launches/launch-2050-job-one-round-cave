#!/usr/bin/env python3
"""Bounded offline OpenAPI response-selector fallback comparison (stdlib only)."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys

spec = importlib.util.spec_from_file_location('statuscheck_param',
    Path(__file__).resolve().parents[1] / 'paramcheck/paramcheck.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
api = previous.api
MAX_STATUS_VISITS = 20000


def selectors(document, operation):
    api.require(isinstance(operation, dict), 'operation must be an object')
    raw = operation.get('responses', {})
    api.require(isinstance(raw, dict), 'responses must be an object')
    result = {}
    for key, value in sorted(raw.items()):
        if key.startswith('x-'):
            continue
        api.require(key == 'default' or re.fullmatch(r'[1-5](?:[0-9]{2}|XX)', key),
                    'unsupported response selector: ' + key)
        item = document.resolve(value)
        api.require(isinstance(item, dict), 'response must resolve to an object')
        api.require(isinstance(item.get('content', {}), dict), 'response content must be an object')
        result[key] = item
    return result


def selected(mapping, status):
    """Explicit HTTP code takes precedence over class range, then default."""
    for key in (str(status), str(status // 100) + 'XX', 'default'):
        if key in mapping:
            return key
    return None


class Analyzer(previous.Analyzer):
    def __init__(self, old, new):
        super().__init__(old, new)
        self.status_visits = 0
        self.selector_groups = []

    def operation(self, path, method, old_item, new_item):
        # Validate selectors before the older exact-key analyses run.
        a = selectors(self.old, old_item[method])
        b = selectors(self.new, new_item[method])
        super().operation(path, method, old_item, new_item)
        groups = {}
        self.status_visits += 500
        api.require(self.status_visits <= MAX_STATUS_VISITS,
                    'status visits exceed 20000; compare at most 40 common operations')
        for status in range(100, 600):
            pair = selected(a, status), selected(b, status)
            if pair[0] != pair[1]:
                groups.setdefault(pair, []).append(status)
        base = api.pointer('/paths', path) + '/' + method + '/responses'
        # Insertion order follows ascending concrete HTTP status, independent of input order.
        for (old_key, new_key), statuses in groups.items():
            loc = api.pointer(base, new_key if new_key is not None else old_key)
            self.selector_groups.append(dict(operation=api.pointer('/paths', path) + '/' + method,
                old_selector=old_key, new_selector=new_key, statuses=statuses))
            self.emit('review', 'response_selector_changed', loc,
                'Effective response selector changed from %s to %s for %d HTTP statuses '
                '(first %d). See selector_groups for the exact set; runtime emission is unknown.' %
                (old_key, new_key, len(statuses), statuses[0]))
            if old_key is None or new_key is None:
                continue
            # Earlier analyzers compare only identical selector keys. Reuse the full
            # inherited response-direction schema rules across remapped selectors.
            self.content(a[old_key].get('content', {}), b[new_key].get('content', {}),
                         loc + '/content', 'response')
            self.changed({k: v for k, v in a[old_key].items() if k != 'content'},
                         {k: v for k, v in b[new_key].items() if k != 'content'}, loc,
                         'response_fallback_metadata_changed',
                         'Effective response metadata differs across selectors; review headers and links.')


def compare(old, new):
    analyzer = Analyzer(old, new)
    result = analyzer.run()
    result.update(extension='statuscheck-v1 (includes paramcheck and earlier analyzers)',
        status_visits=analyzer.status_visits, selector_groups=analyzer.selector_groups,
        status_scope='100..599; common inline top-level operations; exact > class > default')
    return result


def demo():
    capture = Path(__file__).resolve().parents[1] / 'apidelta/imd-openapi.json'
    old, digest = api.load(capture)
    old = copy.deepcopy(old)
    path = sorted(old['paths'])[0]
    method = sorted(old['paths'][path].keys() & api.METHODS)[0]
    # Replace only in-memory response maps. These are hypothetical contracts.
    old['paths'][path][method]['responses'] = {'2XX': {'description': 'Hypothetical',
        'content': {'application/json': {'schema': {'type': 'string'}}}}}
    new = copy.deepcopy(old)
    new['paths'][path][method]['responses']['200'] = {'description': 'Hypothetical',
        'content': {'application/json': {'schema': {'type': 'integer'}}}}
    result = compare(old, new)
    api.require(any(f['code'] == 'schema_type_incompatible' for f in result['findings']),
                'demo failed to detect the override schema break')
    result.update(capture_sha256=digest, baseline_source='https://api.imd.fun/openapi.json',
        demo='Hypothetical 200 integer override of a 2XX string on a real saved IMD path. '
             'Response maps are invented in memory; no API operation is called.')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    diff = commands.add_parser('compare')
    diff.add_argument('old')
    diff.add_argument('new')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            old, oh = api.load(args.old)
            new, nh = api.load(args.new)
            result = compare(old, new)
            result.update(old_sha256=oh, new_sha256=nh)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if args.command == 'demo' else {
            'breaking': 1, 'review_required': 3, 'no_detected_breakage': 0}[result['status']]
    except (api.Invalid, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print('statuscheck: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
