# TNC3 flash-disk image format

This describes what `winepf.exe` (EPFILE2) writes, and therefore what `tnc3epf.py` writes. It was reconstructed from the original binary and checked against the TNC3 firmware. Numbers are hexadecimal where they start with `0x`; multi-byte values are big-endian (68000 byte order).

## 1. Command-line behaviour

- The options are `v`, `r`, `s` and `f <hex>`, case-insensitive. `-h` or an invalid option prints the usage and continues.
- Options are parsed with the classic AT&T `getopt`:
  - An option that takes an argument must not be combined with others and must be followed by a space. Otherwise `getopt` reports `option must not be clustered` or `option must be followed by white space`.
  - Option parsing stops at the first argument that isn't an option. Everything after it is treated as a file name.
- `-f <hex>` is parsed like C `strtol(…, 16)`. It sets the flash address of the first entry and changes the output base name from `FILE` to `FLASH`.
- The default start address is `0x206000`; relocation is on by default.
- Files are processed in the order they are given.
- Outputs go to the current directory:
  - `EP<base>.ABS`: the image, always written.
  - `EP<base>.UPR` and `EP<base>.LWR`: with `-s`.
  - `<name>.SYM`: one per relocated `.APL` that has a symbol table.
- Verbose output: `EPFILE2`, a blank line, then one line per file with the path padded to 30 characters and the size (`%8ld Bytes`), and finally the next free flash address (`%lx OK`).
- Messages (German, as in the original):
  - `Ausgabedatei konnte nicht geöffnet werden`: an output file couldn't be created; exit code 1.
  - `Fehler beim Lesen der Datei %s aufgetreten`: fewer bytes were read than the file size. Processing continues.
  - `Datei zu groß`: an `.APL` body is 256 KiB or larger. Processing continues.

## 2. Image layout

The image is a plain sequence of entries. There is nothing before the first entry and no terminator after the last one. The firmware stops at the first position that doesn't hold the magic, which is normally erased flash (`0xFF`).

```
entry = header (0x20 bytes) + data, padded to an even length
next  = entry + 0x20 + ((size + 1) & ~1)
```

The firmware version examined searches for the first entry at 16 KiB boundaries from `0x208000` up to (not including) `0x300000`. From there it follows the chain as shown above. The start address passed with `-f` must therefore be one of those boundaries. The default `0x206000` is not.

### Entry header (0x20 bytes)

| Offset | Size | Content | Firmware's use |
|---|---|---|---|
| 0x00 | 20 | File name (basename as given), NUL-terminated | `name[14]` (at most 13 characters + NUL). Bytes 0x0E–0x13 are runtime fields (data pointer, reader/writer counts) that the firmware fills in. |
| 0x14 | 4 | Modification time of the file, seconds since 1970 | `mtime` |
| 0x18 | 4 | Size of the data (for relocated `.APL` see §3) | `size` |
| 0x1C | 4 | Magic `"Jimy"` (`0x4A696D79`) | entry is valid |

## 3. Relocation of `.APL` programs

This applies when relocation is on and the file's extension is `APL` (case-insensitive). The extension is everything after the **first** dot, so `X.TAR.APL` is not relocated.

The input is a GEMDOS-style PRG (as produced by Pure C):
- a 0x1C-byte header: `0x601A`, `tlen`, `dlen`, `blen`, `slen`, `res1`, `prgflags`, `absflag`
- the text segment, then the data segment
- a DRI symbol table of 14-byte entries: `name[8]`, `type` (16 bit), `value` (32 bit)
- the relocation table: a 32-bit offset of the first fixup, then one byte per step. A byte `1` means "advance 254 without a fixup"; any other byte `n` means "advance `n` and fix up".

Addresses used:

```
load  = entry address + 0x20 + 0x24     # where the text starts in flash
dbase = 0x800                           # data segment in RAM (fixed)
bbase = 0x800 + dlen                    # bss follows data
```

### Fixups

The loop runs once per byte of the relocation table: `nrel = bytes after the header − tlen − dlen − slen − 4` times. A first offset of 0 is **not** treated as "no relocations".

Each pass does the following:
1. Read the 32-bit value `v` at `text + offset`.
2. Rewrite it by range:
   - `v < tlen` → `v + load`
   - `v < tlen + dlen` → `v − tlen + dbase`
   - `v < tlen + dlen + blen` → `v − tlen − dlen + bbase`
   - otherwise leave it unchanged.
3. Read the next relocation bytes: each `1` adds 254 to the offset, then one byte `n` adds `n`. Every byte read counts towards `nrel`.

### Symbols

The symbol values are moved to their final addresses:
- `type & 0x0100` (BSS): `value += bbase − dlen − tlen`
- `type & 0x0400` (DATA): `value += dbase − tlen`
- `type & 0x0200` (TEXT): `value += load`

The adjustments add up when several bits are set. The table is sorted by `(type >> 8) & 7`, then by value, and written to `<name>.SYM`, where `<name>` is the part of the file name before the first dot. The file uses CRLF line endings:

```
\t%-12s %-8s %-8s\n\n          "Symbol", "Typ", "Wert"
\t%-12s %-8s %8lx %04x\n       name, CONST|BSS|TEXT|DATA|?, value, type
```

The original sorts with C `qsort`, which isn't stable. Symbols with the same class and value can therefore appear in a different order there.

### Data written to the image

The entry's data is a new 0x24-byte header followed by the relocated text and data. The symbol table and relocation table are not written.

| Offset | Content |
|---|---|
| 0x00 | `0x601B` (instead of `0x601A`) |
| 0x02 | `tlen`, `dlen`, `blen`, `slen`, `res1`, copied |
| 0x16 | `load` (replaces `prgflags`) |
| 0x1A | `absflag`, copied |
| 0x1C | `dbase` (`0x800`) |
| 0x20 | `bbase` |

The entry's `size` is `0x24 + tlen + dlen`.

All other files, and every file when `-r` is given, are copied unchanged (up to 256 KiB).

## 4. Split output (`-s`)

The TNC3's 68000 has a 16-bit data bus served by two byte-wide EPROMs. `.UPR` gets the bytes at even offsets of the image (D15–D8), `.LWR` the bytes at odd offsets (D7–D0). The `.ABS` image is written as well.

## 5. Quirks of the original

The original keeps the entry header and the data buffer in static memory and reuses both for every file. Two effects reach the output, and `tnc3epf.py` reproduces them so the output stays byte-identical:
- **Name residue.** The file name is copied with `strcpy`. When a name is shorter than the previous one, the old name's remaining bytes stay behind the terminating NUL.
- **Padding byte.** For an odd size, the padding byte is the buffer byte right after the data. That is left over from an earlier, larger file, `0` if there was none, or for an `.APL` the first byte of its own symbol or relocation table.

The modification time comes from the Windows C runtime and matches the file's Unix mtime, apart from possible differences around daylight-saving changes.

## 6. Deliberate differences in tnc3epf.py

These only affect messages on stderr, or cases where the original would crash or write undefined data:
- Missing files and directories are reported as warnings; the original skipped them silently or crashed.
- File names longer than 13 characters get a warning, because the firmware can't handle them.
- Messages use proper `ß` and `ö`.
- Files larger than 256 KiB are padded with zeros where the original read past its buffer.
- Truncated `.APL` files are rejected.
- Wildcards (`*`, `?`) are expanded by the program, sorted by name. The original expanded them in directory order.
