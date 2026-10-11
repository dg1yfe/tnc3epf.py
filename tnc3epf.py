#!/usr/bin/env python3
"""tnc3epf.py - build flash-disk images for the Symek TNC3.

Portable re-implementation of winepf.exe ("EPFILE2"). Output is byte-identical
to the original, including its quirks; see FORMAT.md.

    tnc3epf.py [-<opt>] { file }
    opt:   v verbose
           r don't relocate
           f <hex> TNC3 Flash-EPROMs
           s split output
"""
import glob
import os
import re
import struct
import sys

BUFSZ = 0x40000             # data buffer of the original (256 KiB)
PRG_HDR = 0x1C              # GEMDOS PRG header as read from the .APL file
FLASH_PRG_HDR = 0x24        # extended header written to flash
ENTRY_HDR = 0x20            # flash-disk directory entry
NAME_FIELD = 0x14           # bytes strcpy'd into before the mtime field
NAME_MAX = 13               # firmware limit (name[14], NUL-terminated)
MAGIC = b'Jimy'
DEFAULT_ADDR = 0x206000
DATA_BASE = 0x800           # data/bss of relocated programs live in RAM here
OPTSTRING = 'rRsSvVhf:F:'

USAGE = ("epfile [-<opt>] { file }\n"
         "opt:   v verbose\n"
         "       r don't relocate\n"
         "       f <hex> TNC3 Flash-EPROMs\n"
         "       s split output\n")

SYMTYPES = {0x000: 'CONST', 0x100: 'BSS', 0x200: 'TEXT', 0x400: 'DATA'}


class EpfError(Exception):
    pass


def be32(buf, off):
    if off < 0 or off + 4 > len(buf):
        raise EpfError('offset 0x%x outside of buffer' % off)
    return struct.unpack_from('>I', buf, off)[0]


def put32(buf, off, val):
    struct.pack_into('>I', buf, off, val & 0xFFFFFFFF)


def out(s):
    sys.stdout.write(s)


def warn(s):
    sys.stderr.write('tnc3epf: %s\n' % s)


def strtol16(s):
    """strtol(s, NULL, 16) as done by MSVC: optional sign and 0x, clamped."""
    m = re.match(r'\s*([+-]?)(?:0[xX](?=[0-9a-fA-F]))?([0-9a-fA-F]*)', s)
    val = int(m.group(2), 16) if m.group(2) else 0
    if m.group(1) == '-':
        val = max(-val, -0x80000000)
    else:
        val = min(val, 0x7FFFFFFF)
    return val & 0xFFFFFFFF


class GetOpt:
    """The AT&T public-domain getopt the original uses (no clustering of
    options with arguments, argument must be a separate word)."""

    def __init__(self, argv, optstring, prog):
        self.argv, self.opts, self.prog = argv, optstring, prog
        self.optind, self.sp, self.optarg = 1, 1, None

    def _err(self, msg, c):
        out('%s: %s -- %c\n' % (self.prog, msg, c))
        return '?'

    def next(self):
        argv = self.argv
        self.optarg = None
        if self.sp == 1:
            if (self.optind >= len(argv) or not argv[self.optind].startswith('-')
                    or len(argv[self.optind]) == 1):
                return None
            if argv[self.optind] == '--':
                self.optind += 1
                return None
        start = self.sp
        arg = argv[self.optind]
        c = arg[self.sp]
        self.sp += 1
        if self.sp >= len(arg):
            self.optind += 1
            self.sp = 1
        idx = self.opts.find(c) if c != ':' else -1
        if idx < 0:
            return self._err('illegal option', c)
        if self.opts[idx + 1:idx + 2] == ':':
            if start != 1:
                return self._err('option must not be clustered', c)
            if self.sp != 1:
                return self._err('option must be followed by white space', c)
            if self.optind >= len(argv):
                return self._err('option requires an argument', c)
            self.optarg = argv[self.optind]
            self.optind += 1
        return c


def basename(path):
    """Name part after the last '\\', '/' or ':'; '.' and '..' are skipped."""
    i = max(path.rfind('\\'), path.rfind('/'), path.rfind(':'))
    name = path[i + 1:]
    return '' if name in ('.', '..') else name


def extension(path):
    """Everything after the first '.' of the basename."""
    name = basename(path)
    return name.split('.', 1)[1] if '.' in name else ''


def sym_filename(path):
    return basename(path).split('.', 1)[0] + '.SYM'


class ImageBuilder:
    def __init__(self, addr=DEFAULT_ADDR, relocate=True, verbose=False):
        self.addr = addr
        self.relocate = relocate
        self.verbose = verbose
        # Static buffers of the original; their stale contents end up in the
        # image (name residue, padding byte), so they persist across files.
        self.hdr = bytearray(ENTRY_HDR)
        self.buf = bytearray(FLASH_PRG_HDR + BUFSZ)

    # -- .APL (GEMDOS PRG) handling -------------------------------------

    def _load_apl(self, f, load, path):
        buf = self.buf
        prg = bytearray(f.read(PRG_HDR)).ljust(FLASH_PRG_HDR, b'\0')
        body = f.read(BUFSZ)
        n = len(body)
        buf[FLASH_PRG_HDR:FLASH_PRG_HDR + n] = body
        if n == BUFSZ:
            out('Datei zu groß\n')
        tlen, dlen, blen, slen = (be32(prg, o) for o in (2, 6, 10, 14))
        text = FLASH_PRG_HDR
        symtab = text + tlen + dlen
        bss_base = (DATA_BASE + dlen) & 0xFFFFFFFF

        # Relocation: one iteration per byte of the relocation table.
        nrel = n - slen - tlen - dlen - 4
        if nrel > 0:
            rel = symtab + slen
            off = be32(buf, rel)
            rp = rel + 4
            cnt = 0
            while cnt < nrel:
                v = be32(buf, text + off)
                if v < tlen:
                    put32(buf, text + off, v + load)
                elif v < tlen + dlen:
                    put32(buf, text + off, v - tlen + DATA_BASE)
                elif v < tlen + dlen + blen:
                    put32(buf, text + off, bss_base - dlen + v - tlen)
                while buf[rp] == 1:
                    off += 0xFE
                    rp += 1
                    cnt += 1
                off += buf[rp]
                rp += 1
                cnt += 1

        nsym = slen // 14
        if nsym:
            self._write_symbols(symtab, nsym, tlen, dlen, load, bss_base, path)

        prg[0:2] = b'\x60\x1b'
        put32(prg, 0x16, load)
        put32(prg, 0x1C, DATA_BASE)
        put32(prg, 0x20, bss_base)
        buf[0:FLASH_PRG_HDR] = prg
        return FLASH_PRG_HDR + tlen + dlen

    def _write_symbols(self, symtab, nsym, tlen, dlen, load, bss_base, path):
        buf = self.buf
        end = symtab + nsym * 14
        if end > len(buf):
            raise EpfError('symbol table outside of buffer')
        syms = []
        for o in range(symtab, end, 14):
            t = struct.unpack_from('>H', buf, o + 8)[0]
            v = be32(buf, o + 10)
            if t & 0x100:
                v += bss_base - dlen - tlen
            if t & 0x400:
                v += DATA_BASE - tlen
            if t & 0x200:
                v += load
            put32(buf, o + 10, v)
            syms.append(bytes(buf[o:o + 14]))
        syms.sort(key=lambda s: (s[8] & 7, be32(s, 10)))
        buf[symtab:end] = b''.join(syms)
        try:
            sf = open(sym_filename(path), 'w', encoding='latin-1', newline='\r\n')
        except OSError:
            return      # the original silently skips the listing
        with sf:
            sf.write('\t%-12s %-8s %-8s\n\n' % ('Symbol', 'Typ', 'Wert'))
            for s in syms:
                t = struct.unpack_from('>H', s, 8)[0]
                name = s[:8].split(b'\0', 1)[0].decode('latin-1')
                sf.write('\t%-12s %-8s %8x %04x\n'
                         % (name, SYMTYPES.get(t & 0x700, '?'), be32(s, 10), t))

    # -- one directory entry ---------------------------------------------

    def add_file(self, path):
        """Return the entry (header + padded data) for one file."""
        f = open(path, 'rb')
        st = os.fstat(f.fileno())
        if self.verbose:
            out('%-30s' % path)
        size = st.st_size
        name = os.fsencode(basename(path))
        if len(name) > NAME_MAX:
            warn('%s: name longer than %d characters' % (path, NAME_MAX))
        # strcpy(): bytes behind the NUL keep the previous (longer) name
        nm = (name + b'\0')[:NAME_FIELD]
        self.hdr[0:len(nm)] = nm
        struct.pack_into('>II4s', self.hdr, 0x14,
                         int(st.st_mtime) & 0xFFFFFFFF, size & 0xFFFFFFFF, MAGIC)
        with f:
            if self.relocate and extension(path).upper() == 'APL':
                size = self._load_apl(f, (self.addr + ENTRY_HDR + FLASH_PRG_HDR)
                                      & 0xFFFFFFFF, path)
                put32(self.hdr, 0x18, size)
            else:
                data = f.read(BUFSZ)
                self.buf[0:len(data)] = data
                if len(data) != size:
                    out('Fehler beim Lesen der Datei %s aufgetreten\n' % path)
        if self.verbose:
            out('%8d Bytes\n' % size)
        padded = (size + 1) & ~1
        self.addr = (self.addr + padded + ENTRY_HDR) & 0xFFFFFFFF
        data = bytes(self.buf[:padded])
        return bytes(self.hdr) + data.ljust(padded, b'\0')


def expand(pattern):
    """Wildcard expansion like the original's _findfirst loop (needed where
    the shell does not expand, e.g. cmd.exe)."""
    if re.search(r'[*?]', pattern):
        names = sorted(glob.glob(pattern))
    else:
        names = [pattern] if os.path.lexists(pattern) else []
    if not names:
        warn('%s: no such file' % pattern)
    files = []
    for n in names:
        if os.path.isdir(n):
            warn('%s: is a directory, skipped' % n)
        else:
            files.append(n)
    return files


def main(argv=None):
    argv = sys.argv if argv is None else argv
    prog = os.path.basename(argv[0]) if argv else 'tnc3epf'
    addr, base = DEFAULT_ADDR, 'FILE'
    relocate, split, verbose = True, False, False

    g = GetOpt(argv, OPTSTRING, prog)
    while True:
        c = g.next()
        if c is None:
            break
        if c in 'fF':
            addr = strtol16(g.optarg)
            base = 'FLASH'
        elif c in 'rR':
            relocate = False
        elif c in 'sS':
            split = True
        elif c in 'vV':
            verbose = True
        elif c in '?h':
            out(USAGE)

    outs = []
    try:
        if split:
            upr = open('EP%s.UPR' % base, 'wb')
            outs.append(upr)
            lwr = open('EP%s.LWR' % base, 'wb')
            outs.append(lwr)
        abs_ = open('EP%s.ABS' % base, 'wb')
        outs.append(abs_)
    except OSError:
        out('Ausgabedatei konnte nicht geöffnet werden\n')
        return 1

    builder = ImageBuilder(addr, relocate, verbose)
    try:
        if verbose:
            out('EPFILE2\n\n')
        for pattern in argv[g.optind:]:
            for path in expand(pattern):
                try:
                    entry = builder.add_file(path)
                except OSError as e:
                    warn('%s: %s' % (path, e.strerror))
                    continue
                except EpfError as e:
                    warn('%s: invalid program file (%s)' % (path, e))
                    return 1
                if split:
                    upr.write(entry[0::2])     # even bytes: D15..D8
                    lwr.write(entry[1::2])     # odd bytes:  D7..D0
                abs_.write(entry)
    finally:
        for o in outs:
            o.close()
    if verbose:
        out('\n%x OK\n' % builder.addr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
