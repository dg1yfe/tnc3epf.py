#!/usr/bin/env python3
"""Regenerate tests/fixtures from the original winepf.exe (needs wine).

    tests/make_fixtures.py path/to/winepf.exe
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inputs import CASES, make_inputs   # noqa: E402

if len(sys.argv) != 2:
    sys.exit('usage: %s path/to/winepf.exe' % sys.argv[0])
EXE = sys.argv[1]

for case, args in CASES.items():
    with tempfile.TemporaryDirectory() as d:
        make_inputs(d)
        inputs = set(os.listdir(d))
        shutil.copy(EXE, os.path.join(d, 'winepf.exe'))
        r = subprocess.run(['wine', 'winepf.exe'] + args, cwd=d, capture_output=True,
                           env=dict(os.environ, WINEDEBUG='-all'))
        dst = os.path.join(HERE, 'fixtures', case)
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(dst)
        for name in sorted(set(os.listdir(d)) - inputs - {'winepf.exe'}):
            shutil.copy(os.path.join(d, name), dst)
        out = r.stdout.replace(b'\r\n', b'\n')
        # argv[0] is a full Windows path under wine
        out = re.sub(rb'^[^\n]*\\winepf\.exe:', b'winepf.exe:', out, flags=re.M)
        with open(os.path.join(dst, 'stdout.txt'), 'wb') as f:
            f.write(out)
        print(case, sorted(os.listdir(dst)))
