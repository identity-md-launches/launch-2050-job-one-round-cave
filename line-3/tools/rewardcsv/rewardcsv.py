#!/usr/bin/env python3
"""Verified, deterministic CSV review copies of exact unsigned ZTO allocations."""
import argparse
import csv
import importlib.util
import io
from pathlib import Path
import sys

SPEC = importlib.util.spec_from_file_location(
    'rewardreceipt', Path(__file__).resolve().parents[1] / 'rewardreceipt' / 'rewardreceipt.py')
rr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rr)
rs = rr.rs
FIELDS = ('id', 'address', 'units', 'amount', 'rounding_unit_awarded',
          'chain_id', 'token_address', 'report_sha256')


def render(request, report, metadata):
    """Validate the entire source report before returning any review bytes."""
    receipt = rr.verify(request, report, metadata)
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, quoting=csv.QUOTE_ALL, lineterminator='\n')
    writer.writerow(FIELDS)
    for row in report['allocations']:
        writer.writerow((row['id'], row.get('address', ''), row['units'], row['amount'],
                         'true' if row['rounding_unit_awarded'] else 'false',
                         str(report['token']['chain_id']), report['token']['address'],
                         receipt['report_sha256']))
    result = stream.getvalue().encode('ascii')
    rs.require(len(result) <= rs.MAX_BYTES, 'CSV exceeds 256-KiB limit; use a smaller roster')
    return result


def verify(request, report, metadata, data):
    expected = render(request, report, metadata)
    rs.require(isinstance(data, bytes) and data == expected,
               'CSV differs from the exact verified export (including order and formatting)')
    import hashlib
    return {'schema': 'rewardcsv-verification-v1', 'csv_sha256': hashlib.sha256(data).hexdigest(),
            'source': rr.verify(request, report, metadata),
            'scope': 'exact review-copy bytes only; no identity, entitlement, balance or payment verified'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='print a verified address-free three-role ZTO CSV')
    for name in ('export', 'verify'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--request', required=True)
        cmd.add_argument('--report', required=True)
        cmd.add_argument('--metadata', default=str(rr.ROOT / 'zto-mainnet.json'))
        if name == 'export':
            cmd.add_argument('--output', help='new workspace CSV; refuses overwrite')
        else:
            cmd.add_argument('--csv', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            request = rs.read_json(rr.ROOT / 'example.json')
            metadata = rs.read_json(rr.ROOT / 'zto-mainnet.json')
            report = rs.allocate(request, metadata)
        else:
            request = rs.read_json(args.request)
            report = rs.read_json(args.report)
            metadata = rs.read_json(args.metadata)
        if args.command == 'verify':
            with rs.workspace_path(args.csv).open('rb') as source:
                data = source.read(rs.MAX_BYTES + 1)
            rs.require(len(data) <= rs.MAX_BYTES, 'CSV exceeds 256-KiB limit')
            rs.write_json(verify(request, report, metadata, data))
        else:
            data = render(request, report, metadata)
            if getattr(args, 'output', None):
                with rs.workspace_path(args.output).open('xb') as destination:
                    destination.write(data)
            else:
                sys.stdout.write(data.decode('ascii'))
        return 0
    except (rs.Invalid, OSError, ValueError, OverflowError, RecursionError) as exc:
        print('rewardcsv: ' + (str(exc) if isinstance(exc, rs.Invalid) else type(exc).__name__), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
