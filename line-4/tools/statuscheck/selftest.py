#!/usr/bin/env python3
"""Offline regression and independently enumerated selector tests."""
import copy
import contextlib
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import statuscheck as s


def response(kind='string'):
    return {'description': 'test', 'content': {'application/json': {'schema': {'type': kind}}}}


def doc(responses):
    return {'openapi': '3.1.0', 'paths': {'/a~b/c': {'get': {'responses': responses}}}}


def codes(result):
    return {f['code'] for f in result['findings']}


class Tests(unittest.TestCase):
    def test_unchanged(self):
        d = doc({'200': response(), '2XX': response('integer'), 'default': response('boolean')})
        r = s.compare(d, d)
        self.assertEqual(r['status'], 'no_detected_breakage')
        self.assertEqual(r['selector_groups'], [])
        self.assertEqual(r['status_visits'], 500)

    def test_exhaustive_precedence(self):
        # Independent oracle constructs a concrete table by painting broadest first.
        keys = ('default', '1XX', '2XX', '5XX', '100', '200', '299', '599')
        for bits in itertools.product((False, True), repeat=len(keys)):
            mapping = {k: {} for k, active in zip(keys, bits) if active}
            expected = [None] * 500
            if 'default' in mapping:
                expected = ['default'] * 500
            for key in ('1XX', '2XX', '5XX'):
                if key in mapping:
                    start = (int(key[0]) - 1) * 100
                    expected[start:start + 100] = [key] * 100
            for key in ('100', '200', '299', '599'):
                if key in mapping:
                    expected[int(key) - 100] = key
            self.assertEqual([s.selected(mapping, x) for x in range(100, 600)], expected)

    def test_explicit_over_range(self):
        a = doc({'2XX': response()})
        b = copy.deepcopy(a)
        b['paths']['/a~b/c']['get']['responses']['200'] = response('integer')
        r = s.compare(a, b)
        self.assertIn('schema_type_incompatible', codes(r))
        self.assertEqual(r['selector_groups'][0]['statuses'], [200])
        finding = next(f for f in r['findings'] if f['code'] == 'schema_type_incompatible')
        self.assertEqual(finding['location'], '/paths/~1a~0b~1c/get/responses/200/content/application~1json/schema/type')

    def test_fallback_after_removal(self):
        a = doc({'200': response(), 'default': response('integer')})
        b = doc({'default': response('integer')})
        self.assertIn('schema_type_incompatible', codes(s.compare(a, b)))

    def test_range_over_default(self):
        r = s.compare(doc({'default': response()}), doc({'default': response(), '2XX': response('integer')}))
        self.assertEqual(r['selector_groups'][0]['statuses'], list(range(200, 300)))
        self.assertEqual(sum(f['code'] == 'schema_type_incompatible' for f in r['findings']), 1)

    def test_response_direction(self):
        a = doc({'2XX': response('number')})
        b = doc({'2XX': response('number'), '200': response('integer')})
        self.assertNotIn('schema_type_incompatible', codes(s.compare(a, b)))
        self.assertIn('schema_type_incompatible', codes(s.compare(b, a)))

    def test_missing_description_is_review(self):
        r = s.compare(doc({'200': response()}), doc({}))
        self.assertEqual(r['status'], 'review_required')
        self.assertEqual(r['selector_groups'][0]['new_selector'], None)

    def test_new_coverage_is_review(self):
        r = s.compare(doc({}), doc({'default': response()}))
        self.assertEqual(r['status'], 'review_required')
        self.assertEqual(len(r['selector_groups'][0]['statuses']), 500)

    def test_same_schema_remap_is_review(self):
        r = s.compare(doc({'2XX': response()}), doc({'2XX': response(), '200': response()}))
        self.assertEqual(r['status'], 'review_required')

    def test_ref_target_override(self):
        a = doc({'default': {'$ref': '#/components/responses/base'}})
        a['components'] = {'responses': {'base': response()}}
        b = copy.deepcopy(a)
        b['components']['responses']['override'] = response('integer')
        b['paths']['/a~b/c']['get']['responses']['200'] = {'$ref': '#/components/responses/override'}
        self.assertIn('schema_type_incompatible', codes(s.compare(a, b)))

    def test_unchanged_invalid_selector(self):
        for key in ('600', '099', '2xx', '20X', 'DEFAULT', '200 ', ''):
            d = doc({key: response()})
            with self.subTest(key=key), self.assertRaises(s.api.Invalid):
                s.compare(d, d)

    def test_invalid_operation(self):
        for value in (None, False, []):
            d = doc({})
            d['paths']['/a~b/c']['get'] = value
            with self.subTest(value=value), self.assertRaises(s.api.Invalid):
                s.compare(d, d)

    def test_invalid_response(self):
        for value in (False, [], None, {'content': []}):
            d = doc({'200': value})
            with self.subTest(value=value), self.assertRaises(s.api.Invalid):
                s.compare(d, d)

    def test_no_remote_ref(self):
        d = doc({'200': {'$ref': 'https://example.com/response'}})
        with self.assertRaises(s.api.Invalid):
            s.compare(d, d)

    def test_alias_cycle(self):
        d = doc({'200': {'$ref': '#/paths/~1a~0b~1c/get/responses/200'}})
        with self.assertRaises(s.api.Invalid):
            s.compare(d, d)

    def test_extensions_ignored_for_selection(self):
        d = doc({'200': response(), 'x-owner': {'anything': True}})
        r = s.compare(d, d)
        self.assertEqual(r['selector_groups'], [])

    def test_inherited_finding_retained(self):
        a = doc({'200': response()})
        b = copy.deepcopy(a)
        b['paths']['/a~b/c']['get']['parameters'] = [
            {'name': 'q', 'in': 'query', 'required': True, 'schema': {'type': 'string'}}]
        self.assertIn('parameter_added', codes(s.compare(a, b)))

    def test_budget_refuses_whole_comparison(self):
        with patch.object(s, 'MAX_STATUS_VISITS', 499), self.assertRaises(s.api.Invalid):
            s.compare(doc({'200': response()}), doc({'200': response()}))

    def test_no_mutation_deterministic(self):
        a = doc({'default': response()})
        b = doc({'200': response('integer'), 'default': response()})
        saved = copy.deepcopy((a, b))
        result = s.compare(a, b)
        self.assertEqual((a, b), saved)
        b['paths']['/a~b/c']['get']['responses'] = dict(reversed(list(b['paths']['/a~b/c']['get']['responses'].items())))
        self.assertEqual(result, s.compare(a, b))

    def test_media_change_across_selector(self):
        a = doc({'default': response()})
        r = response()
        r['content'] = {'text/plain': {'schema': {'type': 'string'}}}
        b = doc({'default': response(), '200': r})
        self.assertIn('media_type_removed', codes(s.compare(a, b)))
        self.assertIn('media_type_added', codes(s.compare(a, b)))

    def test_cli_exits(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd() / 'test/scratch') as folder:
            p = Path(folder)
            a = doc({'2XX': response()})
            variants = [(a, 0), (doc({'2XX': response(), '200': response('integer')}), 1),
                        (doc({'2XX': response(), '200': response()}), 3), (doc({'600': response()}), 2)]
            (p / 'old.json').write_text(json.dumps(a))
            for b, expected in variants:
                (p / 'new.json').write_text(json.dumps(b))
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(s.main(['compare', str(p / 'old.json'), str(p / 'new.json')]), expected)

    def test_demo(self):
        self.assertIn('schema_type_incompatible', codes(s.demo()))


if __name__ == '__main__':
    (Path.cwd() / 'test/scratch').mkdir(parents=True, exist_ok=True)
    unittest.main()
