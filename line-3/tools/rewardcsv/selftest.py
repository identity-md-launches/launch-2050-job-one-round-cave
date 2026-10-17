#!/usr/bin/env python3
"""Offline exact-copy, tampering, resource-bound and CLI integration tests."""
import contextlib
import copy
import csv
import io
from pathlib import Path
import random
import tempfile
import unittest
import rewardcsv as rc


class Tests(unittest.TestCase):
    def setUp(self):
        self.metadata = rc.rs.read_json(rc.rr.ROOT / 'zto-mainnet.json')
        self.request = rc.rs.read_json(rc.rr.ROOT / 'example.json')

    def report(self, request=None):
        return rc.rs.allocate(request or self.request, self.metadata)

    def test_exact_strings_and_receipt(self):
        report = self.report()
        data = rc.render(self.request, report, self.metadata)
        rows = list(csv.DictReader(io.StringIO(data.decode())))
        self.assertEqual(sum(int(row['units']) for row in rows), 10**18)
        self.assertEqual(rows[0]['units'], '333333333333333334')
        self.assertTrue(all(row['address'] == '' for row in rows))
        self.assertTrue(all(row['report_sha256'] == rc.rr.digest(report) for row in rows))
        self.assertEqual(rc.verify(self.request, report, self.metadata, data)['source']['budget_units'], str(10**18))

    def test_seeded_roundtrips(self):
        rng = random.Random(32)
        for _ in range(100):
            request = {'budget': rc.rs.display_units(rng.randrange(1, 10**25), 18),
                       'contributors': [{'id': 'worker'+str(i), 'weight': str(rng.randrange(1, 30))}
                                        for i in range(rng.randrange(1, 30))]}
            report = self.report(request)
            data = rc.render(request, report, self.metadata)
            rows = list(csv.DictReader(io.StringIO(data.decode())))
            self.assertEqual([(r['id'], r['units'], r['amount']) for r in rows],
                             [(r['id'], r['units'], r['amount']) for r in report['allocations']])
            rc.verify(request, report, self.metadata, data)

    def test_uint256_and_zero_rows(self):
        request = {'budget': rc.rs.display_units(rc.rs.UINT256_MAX, 18),
                   'contributors': [{'id': 'large', 'weight': '1'}, {'id': 'zero', 'weight': '0'}]}
        data = rc.render(request, self.report(request), self.metadata)
        rows = list(csv.DictReader(io.StringIO(data.decode())))
        self.assertEqual(rows[0]['units'], str(rc.rs.UINT256_MAX))
        self.assertEqual(rows[1]['units'], '0')

    def test_source_tampering(self):
        report = self.report()
        for key, value in [('units', '0'), ('amount', '0'), ('rounding_unit_awarded', False)]:
            altered = copy.deepcopy(report)
            altered['allocations'][0][key] = value
            with self.assertRaises(rc.rs.Invalid):
                rc.render(self.request, altered, self.metadata)
        altered = copy.deepcopy(report)
        altered['paid'] = True
        with self.assertRaises(rc.rs.Invalid):
            rc.render(self.request, altered, self.metadata)

    def test_csv_tampering_and_format(self):
        report = self.report()
        data = rc.render(self.request, report, self.metadata)
        for changed in (data + b'\n', data.replace(b'build', b'other'), data.replace(b'\n', b'\r\n'),
                        b'\xef\xbb\xbf'+data, data[:-1]):
            with self.assertRaises(rc.rs.Invalid):
                rc.verify(self.request, report, self.metadata, changed)

    def test_resource_bound(self):
        request = {'budget': rc.rs.display_units(rc.rs.UINT256_MAX, 18), 'contributors': [{'id': 'a'*60+str(i), 'weight': '1'} for i in range(1000)]}
        with self.assertRaises(rc.rs.Invalid):
            rc.render(request, self.report(request), self.metadata)

    def test_formula_id_refused(self):
        for name in ('=SUM(1)', '+1', '-1', '@foo', '\tfoo'):
            request = {'budget': '1', 'contributors': [{'id': name, 'weight': '1'}]}
            with self.assertRaises(rc.rs.Invalid):
                self.report(request)

    def test_cli_roundtrip_and_no_overwrite(self):
        # Temporary files stay inside the workspace for inherited I/O validation.
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory)
            request, report, output = [root / n for n in ('request.json', 'report.json', 'review.csv')]
            rc.rs.write_json(self.request, request)
            rc.rs.write_json(self.report(), report)
            base = ['--request', str(request), '--report', str(report)]
            self.assertEqual(rc.main(['export'] + base + ['--output', str(output)]), 0)
            before = output.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(rc.main(['export'] + base + ['--output', str(output)]), 2)
            self.assertEqual(output.read_bytes(), before)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rc.main(['verify'] + base + ['--csv', str(output)]), 0)
            report.write_text('{"bad":1,"bad":2}')
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(rc.main(['export'] + base), 2)


if __name__ == '__main__':
    unittest.main()
