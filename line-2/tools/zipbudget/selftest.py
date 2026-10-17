#!/usr/bin/env python3
"""Offline tests, confined to workspace scratch; never extract any member."""
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zipbudget as budget


def packed(items=(('a', b'hello'),), comment=b''):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in items:
            info = zipfile.ZipInfo(name)
            info.comment = comment
            archive.writestr(info, payload)
    return stream.getvalue()


class BudgetTests(unittest.TestCase):
    def setUp(self):
        scratch = budget.local_path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch, prefix='zipbudget-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'input.zip'

    def run_budget(self, data=None, **kwargs):
        if data is not None:
            self.source.write_bytes(data)
        return budget.inspect(self.source, kwargs.pop('max_files', 10),
                              kwargs.pop('max_bytes', 100), **kwargs)

    def before_parser(self, data, **kwargs):
        with patch.object(zipfile, 'ZipFile', side_effect=AssertionError('parser reached')):
            with self.assertRaises(budget.Rejected):
                self.run_budget(data, **kwargs)

    def test_exact_file_and_byte_budget(self):
        report = self.run_budget(packed(), max_files=1, max_bytes=5)
        self.assertTrue(report['ok'])
        self.assertEqual((report['files'], report['bytes']), (1, 5))
        self.assertEqual(report['entries'], [{'name': 'a', 'bytes': 5}])
        self.assertTrue(report['counts_complete'])

    def test_file_budget_breach(self):
        report = self.run_budget(packed((('a', b'x'), ('b', b'y'))), max_files=1)
        self.assertFalse(report['ok'])
        self.assertFalse(report['counts_complete'])

    def test_byte_budget_breach(self):
        report = self.run_budget(packed(), max_bytes=4)
        self.assertFalse(report['ok'])
        self.assertEqual(report['reason'], 'budget exceeded')

    def test_empty(self):
        report = self.run_budget(packed(()), max_files=1, max_bytes=1)
        self.assertEqual((report['files'], report['bytes']), (0, 0))

    def test_directory_only_archive_counts_entries(self):
        data = packed((('a/', b''), ('b/', b'')))
        self.before_parser(data, max_entries=1)
        report = self.run_budget(data, max_entries=2, max_files=1)
        self.assertEqual(report['files'], 0)
        self.assertEqual(report['preflight']['entries'], 2)

    def test_archive_limit_before_parser(self):
        data = packed()
        self.before_parser(data, archive_bytes=len(data)-1)
        self.assertTrue(self.run_budget(data, archive_bytes=len(data))['ok'])

    def test_directory_limit_before_parser(self):
        data = packed(comment=b'x' * 2000)
        self.before_parser(data, directory_bytes=1024)
        size = budget.directory_gate(data)['directory_bytes']
        self.assertTrue(self.run_budget(data, directory_bytes=size)['ok'])
        self.before_parser(data, directory_bytes=size-1)

    def test_underreported_entries(self):
        data = bytearray(packed((('a', b'x'), ('b', b'y'))))
        struct.pack_into('<HH', data, data.rfind(b'PK\x05\x06') + 8, 1, 1)
        self.before_parser(data, max_entries=1)

    def test_all_truncations(self):
        data = packed()
        for length in range(len(data)):
            with self.subTest(length=length):
                self.before_parser(data[:length])

    def test_trailing_bytes(self):
        self.before_parser(packed() + b'trailer')

    def test_invalid_api_limits(self):
        self.source.write_bytes(packed())
        for name in ('max_files', 'max_bytes', 'archive_bytes', 'max_entries', 'directory_bytes'):
            for value in (False, True, 0, -1, 1.5, '2', None):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(budget.Rejected):
                        self.run_budget(**{name: value})

    def test_workspace_confinement(self):
        # No path outside the workspace is accessed: local_path rejects first.
        with self.assertRaisesRegex(budget.Rejected, 'inside'):
            budget.inspect(Path.cwd().parent / 'not-read.zip', 1, 1)

    def test_source_symlink(self):
        self.source.write_bytes(packed())
        link = self.root / 'link.zip'
        link.symlink_to(self.source)
        with self.assertRaisesRegex(budget.Rejected, 'symlink'):
            budget.inspect(link, 1, 5)

    def test_directory_source(self):
        with self.assertRaises(budget.Rejected):
            budget.inspect(self.root, 1, 1)

    def test_missing_source(self):
        with self.assertRaises(budget.Rejected):
            self.run_budget()

    def test_digest_and_no_payload_reads(self):
        data = packed()
        with patch.object(zipfile.ZipFile, 'open', side_effect=AssertionError('payload read')):
            report = self.run_budget(data)
        self.assertEqual(report['archive_sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(report['archive_bytes'], len(data))
        self.assertFalse(report['content_checked'])

    def test_path_replacement_uses_snapshot(self):
        data = packed()
        real_gate = budget.directory_gate
        def replace(snapshot, **kwargs):
            self.source.write_bytes(packed((('other', b'different'),)))
            return real_gate(snapshot, **kwargs)
        with patch.object(budget, 'directory_gate', side_effect=replace):
            report = self.run_budget(data)
        self.assertEqual(report['entries'][0]['name'], 'a')
        self.assertEqual(report['archive_sha256'], hashlib.sha256(data).hexdigest())

    def test_growth_while_reading_is_bounded(self):
        data = packed()
        self.source.write_bytes(data)
        original_open = Path.open
        def grow(path, *args, **kwargs):
            if path == self.source and args == ('rb',):
                with original_open(path, 'ab') as writer:
                    writer.write(b'extra')
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', grow), patch.object(zipfile, 'ZipFile',
                side_effect=AssertionError('parser reached')):
            with self.assertRaisesRegex(budget.Rejected, 'while reading'):
                self.run_budget(archive_bytes=len(data))

    def test_does_not_claim_path_validation(self):
        report = self.run_budget(packed((('../not-extracted', b'hello'),)))
        self.assertTrue(report['ok'])
        self.assertFalse(report['content_checked'])
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['input.zip'])

    def test_cli_exit_codes(self):
        self.source.write_bytes(packed())
        for options, code in (([], 0), (['--max-bytes', '1'], 1),
                              (['--max-entries', '0'], 2),
                              (['--directory-bytes', '1'], 2)):
            run = subprocess.run([sys.executable, '-B', budget.__file__,
                                  str(self.source), *options],
                                 capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, code, run.stderr)
            if run.stdout:
                self.assertEqual(json.loads(run.stdout)['ok'], code == 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
