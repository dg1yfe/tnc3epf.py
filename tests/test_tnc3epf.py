"""Compare tnc3epf.py byte-for-byte with outputs of the original winepf.exe."""
import contextlib
import io
import os
import sys
import struct
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..'))
import tnc3epf                          # noqa: E402
from inputs import CASES, make_inputs   # noqa: E402

FIXTURES = os.path.join(HERE, 'fixtures')


class TestAgainstOriginal(unittest.TestCase):
    def run_case(self, case):
        expected = os.path.join(FIXTURES, case)
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            make_inputs(d)
            inputs = set(os.listdir(d))
            stdout = io.StringIO()
            os.chdir(d)
            try:
                # the fixtures were recorded with the original's default
                # start address; argv[0] as the original printed it
                with contextlib.redirect_stdout(stdout), \
                        contextlib.redirect_stderr(io.StringIO()), \
                        mock.patch.object(tnc3epf, 'DEFAULT_ADDR',
                                          tnc3epf.ORIGINAL_DEFAULT_ADDR):
                    tnc3epf.main(['winepf.exe'] + CASES[case])
            finally:
                os.chdir(cwd)
            produced = set(os.listdir(d)) - inputs
            self.assertEqual(produced, set(os.listdir(expected)) - {'stdout.txt'})
            for name in produced:
                with open(os.path.join(d, name), 'rb') as a, \
                        open(os.path.join(expected, name), 'rb') as b:
                    self.assertEqual(a.read(), b.read(), name)
        with open(os.path.join(expected, 'stdout.txt'), encoding='latin-1') as f:
            self.assertEqual(stdout.getvalue(), f.read())


class TestDefaults(unittest.TestCase):
    def test_default_address(self):
        """Without -f, the first entry is placed at 0x208000 (Mini OS 3.12)."""
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            make_inputs(d)
            os.chdir(d)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    tnc3epf.main(['tnc3epf.py', 'TEST.APL'])
            finally:
                os.chdir(cwd)
            with open(os.path.join(d, 'EPFILE.ABS'), 'rb') as f:
                image = f.read()
        # text of the first program starts at entry + 0x20 + 0x24
        self.assertEqual(struct.unpack_from('>I', image, 0x20 + 0x16)[0], 0x208044)


def _make_test(case):
    return lambda self: self.run_case(case)


for _case in CASES:
    setattr(TestAgainstOriginal, 'test_' + _case, _make_test(_case))


if __name__ == '__main__':
    unittest.main()
