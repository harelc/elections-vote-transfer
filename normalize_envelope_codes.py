#!/usr/bin/env python3
"""Give the double envelopes one settlement code, 9999, in every ballot CSV.

The CEC files use 875 (K19, K20) or 99999 (K21) for the double-envelope rows
('מעטפות חיצוניות'); every analysis here drops only 9999, so in those years
the envelope rows were matched by number across elections and fed into the
transfer fit, t-SNE, maps and irregularities as if they were ballot boxes.
Rows are recognised by name. Only the code field of those lines is
rewritten; every other byte of the file stays as it is. Running it twice
changes nothing.

    python normalize_envelope_codes.py
"""
import csv
from pathlib import Path

from party_config import ELECTIONS

ENVELOPE_NAMES = {'מעטפות חיצוניות', 'מעטפות כפולות'}


def main():
    for e, cfg in sorted(ELECTIONS.items(), key=lambda kv: int(kv[0])):
        path = Path(cfg['file'])
        if not path.exists():
            continue
        enc = cfg['encoding']
        lines = path.read_bytes().decode(enc).splitlines(keepends=True)
        header = next(csv.reader([lines[0]]))
        name_i, code_i = header.index('שם ישוב'), header.index('סמל ישוב')
        changed, old_codes = 0, set()
        for n, line in enumerate(lines[1:], start=1):
            fields = next(csv.reader([line]), None)
            if not fields or len(fields) <= max(name_i, code_i):
                continue
            if fields[name_i].strip() in ENVELOPE_NAMES and fields[code_i].strip() != '9999':
                # The envelope rows have plain (unquoted) name and code fields.
                parts = line.split(',')
                old_codes.add(parts[code_i])
                parts[code_i] = '9999'
                lines[n] = ','.join(parts)
                changed += 1
        if changed:
            path.write_bytes(''.join(lines).encode(enc))
            print(f"K{e}: {changed} envelope rows, code {', '.join(sorted(old_codes))} -> 9999")


if __name__ == '__main__':
    main()
