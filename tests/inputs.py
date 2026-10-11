"""Deterministic input files for the tnc3epf regression tests."""
import os
import struct

MTIME = 1000000000          # 2001-09-09, outside any DST transition

# argv (without program name) per case; the reference outputs in
# tests/fixtures/<case>/ were produced by the original winepf.exe under wine.
CASES = {
    'verbose_split': ['-v', '-s', 'LONGNAME.TXT', 'TEST.APL', 'B.DAT'],
    'flash_addr': ['-f', '21a000', 'B.DAT', 'TEST.APL', 'LONGNAME.TXT', 'BIG.APL'],
    'no_reloc': ['-r', 'TEST.APL'],
    'ext_rules': ['-v', 'BIG.APL', 'X.TAR.APL', 'B.DAT'],
    'getopt_errors': ['-x', '-vf', '1', '-f2', 'B.DAT'],
}


def prg(text, data, blen, syms, relocs):
    """GEMDOS PRG: relocs is the list of byte offsets (ascending)."""
    sym = b''.join(n.ljust(8, b'\0') + struct.pack('>HI', t, v) for n, t, v in syms)
    rel = b''
    if relocs:
        rel = struct.pack('>I', relocs[0])
        for a, b in zip(relocs, relocs[1:]):
            d = b - a
            while d > 254:
                rel += b'\x01'
                d -= 254
            rel += bytes([d])
        rel += b'\0'
    else:
        rel = struct.pack('>I', 0)
    hdr = struct.pack('>HIIIIIIH', 0x601A, len(text), len(data), blen, len(sym), 0, 0, 0)
    return hdr + text + data + sym + rel


def make_inputs(d):
    files = {}
    files['LONGNAME.TXT'] = bytes(range(1, 0x31)) + b'\xAB'          # odd size
    files['B.DAT'] = b'hello'                                          # odd, short name
    text = struct.pack('>IIII', 0x4, 0x12, 0x30, 0x99999999)
    data = struct.pack('>II', 0x0, 0x14)
    files['TEST.APL'] = prg(text, data, 0x20,
                            [(b'start', 0xA200, 0), (b'dvar', 0xA400, 0x10),
                             (b'bvar', 0xA100, 0x1C)],
                            [0, 4, 8, 12, 16, 20])
    # 0x400 bytes text with relocations far apart (exercises the 1 = +254 code)
    text = bytearray(0x400)
    for off, val in ((0, 0x10), (0x200, 0x404), (0x3FC, 0x40C)):
        struct.pack_into('>I', text, off, val)
    data = struct.pack('>III', 0x8, 0x0, 0x400)
    syms = [(b'main', 0xA200, 0), (b'tab', 0xA200, 0x200), (b'zz', 0xA400, 0x404),
            (b'heap', 0xA100, 0x40C), (b'K', 0xA000, 0x1234), (b'aa', 0xA200, 0x10)]
    files['BIG.APL'] = prg(bytes(text), data, 0x100, syms,
                           [0, 0x200, 0x3FC, 0x400, 0x404])
    files['X.TAR.APL'] = files['TEST.APL']                             # ext "TAR.APL"
    for name, content in files.items():
        p = os.path.join(d, name)
        with open(p, 'wb') as f:
            f.write(content)
        os.utime(p, (MTIME, MTIME))
