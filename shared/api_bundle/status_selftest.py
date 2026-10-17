"""Response fallback analysis through the approved, non-extracting ZIP boundary."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import api_bundle as bundle


def response(kind='string'):
    return {'description': 'Illustrative response',
            'content': {'application/json': {'schema': {'type': kind}}}}


class StatusBundleTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='status-tests-', dir=scratch)
        self.root = Path(self.temp.name)
        self.doc = {'openapi': '3.1.0', 'paths': {'/items': {'get': {
            'operationId': 'listItems', 'responses': {'2XX': response()}}}}}

    def tearDown(self):
        self.temp.cleanup()

    def archive(self, name, document):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(zipfile.ZipInfo('docs/openapi.json'), json.dumps(document))
            archive.writestr(zipfile.ZipInfo('inert.py'), 'raise RuntimeError("do not execute")')
        return path

    def compare(self, old, new, **kwargs):
        a, b = self.archive('old.zip', old), self.archive('new.zip', new)
        return bundle.compare(a, b, member='docs/openapi.json', statuses=True,
            old_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),
            new_sha256=hashlib.sha256(b.read_bytes()).hexdigest(), **kwargs)

    def codes(self, report):
        return {finding['code'] for finding in report['findings']}

    def test_approved_public_capture_without_extraction(self):
        capture = json.loads(Path(__file__).with_name('imd-openapi.json').read_bytes())
        report = self.compare(capture, capture)
        self.assertEqual(report['status'], 'no_detected_breakage')
        self.assertEqual(report['operations_compared'], 5)
        self.assertEqual(report['status_visits'], 2500)
        self.assertEqual(report['selector_groups'], [])
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['new.zip', 'old.zip'])
        for side in ('old', 'new'):
            self.assertTrue(report['bundle_inputs'][side]['approved_sha256_checked'])
            self.assertTrue(report['bundle_inputs'][side]['all_payloads_crc_checked'])
            self.assertEqual(len(report['bundle_inputs'][side]['checked_files']), 2)

    def test_explicit_override_is_opt_in_and_keeps_review(self):
        new = copy.deepcopy(self.doc)
        new['paths']['/items']['get']['responses']['200'] = response('integer')
        report = self.compare(self.doc, new)
        self.assertTrue({'schema_type_incompatible', 'response_selector_changed',
                         'response_status_changed'} <= self.codes(report))
        self.assertEqual(report['selector_groups'][0]['statuses'], [200])
        finding = next(f for f in report['findings'] if f['code'] == 'schema_type_incompatible')
        self.assertEqual(finding['location'],
            '/paths/~1items/get/responses/200/content/application~1json/schema/type')
        a, b = self.root / 'old.zip', self.root / 'new.zip'
        for options in ({}, {'oauth': True}, {'servers': True}, {'parameters': True}):
            prior = bundle.compare(a, b, member='docs/openapi.json', **options)
            self.assertEqual(prior['status'], 'review_required')
            self.assertNotIn('selector_groups', prior)

    def test_default_range_and_removed_override_grouping(self):
        old = copy.deepcopy(self.doc)
        old['paths']['/items']['get']['responses'] = {'default': response()}
        new = copy.deepcopy(old)
        new['paths']['/items']['get']['responses']['2XX'] = response('integer')
        report = self.compare(old, new)
        self.assertEqual(report['selector_groups'][0]['statuses'], list(range(200, 300)))
        self.assertEqual(sum(f['code'] == 'schema_type_incompatible' for f in report['findings']), 1)
        old['paths']['/items']['get']['responses'] = {
            'default': response('integer'), '200': response()}
        new['paths']['/items']['get']['responses'] = {'default': response('integer')}
        report = self.compare(old, new)
        self.assertEqual(report['selector_groups'][0]['old_selector'], '200')
        self.assertEqual(report['selector_groups'][0]['new_selector'], 'default')
        self.assertIn('schema_type_incompatible', self.codes(report))

    def test_response_direction_and_missing_coverage_stay_conservative(self):
        old = copy.deepcopy(self.doc)
        old['paths']['/items']['get']['responses']['2XX'] = response('number')
        new = copy.deepcopy(old)
        new['paths']['/items']['get']['responses']['200'] = response('integer')
        self.assertEqual(self.compare(old, new)['status'], 'review_required')
        self.assertEqual(self.compare(new, old)['status'], 'breaking')
        new['paths']['/items']['get']['responses'] = {}
        report = self.compare(old, new)
        self.assertEqual(report['status'], 'review_required')
        self.assertIsNone(report['selector_groups'][0]['new_selector'])

    def test_unchanged_bad_selector_and_remote_reference_refused(self):
        for responses in ({'2xx': response()}, {'600': response()},
                          {'200': {'$ref': 'https://example.invalid/response'}}):
            bad = copy.deepcopy(self.doc)
            bad['paths']['/items']['get']['responses'] = responses
            with self.subTest(responses=responses), self.assertRaises(ValueError):
                self.compare(bad, bad)

    def test_local_response_references_and_inherited_findings(self):
        old = copy.deepcopy(self.doc)
        old['components'] = {'responses': {'fallback': response()}}
        op = old['paths']['/items']['get']
        op['responses'] = {'2XX': {'$ref': '#/components/responses/fallback'}}
        op['parameters'] = [{'name': 'tags', 'in': 'query',
                             'schema': {'type': 'array', 'items': {'type': 'string'}}}]
        new = copy.deepcopy(old)
        new['components']['responses']['override'] = response('integer')
        op = new['paths']['/items']['get']
        op['responses']['200'] = {'$ref': '#/components/responses/override'}
        op['parameters'][0]['explode'] = False
        op['operationId'] = 'renamedItems'
        op['servers'] = [{'url': '/migrated'}]
        self.assertTrue({'schema_type_incompatible', 'parameter_wire_explode_changed',
                         'operation_id_changed', 'server_destination_removed'} <=
                        self.codes(self.compare(old, new)))

    def test_approval_directory_and_crc_precede_status_analysis(self):
        path = self.archive('checks.zip', self.doc)
        with mock.patch.object(bundle.statuscheck, 'compare') as analyzer:
            with self.assertRaisesRegex(ValueError, 'approved digest'):
                bundle.compare(path, path, statuses=True, old_sha256='1' * 64)
            with self.assertRaisesRegex(ValueError, 'directory'):
                bundle.compare(path, path, statuses=True, directory_bytes=1)
            raw = path.read_bytes()
            path.write_bytes(raw.replace(b'do not execute', b'DO NOT EXECUTE'))
            with self.assertRaises(zipfile.BadZipFile):
                bundle.compare(path, path, statuses=True, member='docs/openapi.json')
            analyzer.assert_not_called()

    def test_status_budget_refuses_whole_comparison(self):
        with mock.patch.object(bundle.statuscheck, 'MAX_STATUS_VISITS', 499):
            with self.assertRaisesRegex(ValueError, 'status visits'):
                self.compare(self.doc, self.doc)

    def test_cli_all_four_exits_and_combined_flags(self):
        a = self.archive('a.zip', self.doc)
        changed = copy.deepcopy(self.doc)
        changed['paths']['/items']['get']['responses']['200'] = response('integer')
        review = copy.deepcopy(self.doc)
        review['paths']['/items']['get']['responses']['200'] = response()
        bad = copy.deepcopy(self.doc)
        bad['paths']['/items']['get']['responses'] = {'600': response()}
        for document, expected in ((self.doc, 0), (changed, 1), (bad, 2), (review, 3)):
            b = self.archive('b.zip', document)
            with self.subTest(expected=expected):
                result = subprocess.run([sys.executable, '-B', bundle.__file__, str(a), str(b),
                    '--member', 'docs/openapi.json', '--old-sha256', hashlib.sha256(a.read_bytes()).hexdigest(),
                    '--new-sha256', hashlib.sha256(b.read_bytes()).hexdigest(), '--statuses',
                    '--parameters', '--servers', '--oauth'], capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                parsed = json.loads(result.stdout)
                if expected != 2:
                    self.assertTrue(parsed['extension'].startswith('statuscheck-v1'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
