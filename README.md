# tnc3epf

`tnc3epf.py` builds flash-disk images for the **Symek TNC3** packet-radio controller. It replaces the Windows-only `winepf.exe` (EPFILE2) and runs anywhere Python 3.8 or later is installed. It needs only the standard library, so it works on Linux, macOS and Windows.

The tool packs files into an image for the TNC3's flash disk. 68000 programs (`.APL`) are relocated to the flash address they will run from. For the same input, the output is byte-identical to the original `winepf.exe`.

## Usage

```
python3 tnc3epf.py [-<opt>] { file }
opt:   v verbose
       r don't relocate
       f <hex> TNC3 Flash-EPROMs
       s split output
```

| Option | Effect |
|---|---|
| `-v` | Print each file with its size, then the next free flash address. |
| `-r` | Copy `.APL` files unchanged instead of relocating them. |
| `-f <hex>` | Flash address of the first entry (default `206000`). Output files are named `EPFLASH.*` instead of `EPFILE.*`. |
| `-s` | Also write the image split for two byte-wide EPROMs: `.UPR` gets the even bytes, `.LWR` the odd bytes. |

The options are case-insensitive. An option that takes an argument must stand alone and be followed by a space (`-f 208000`, not `-f208000` or `-vf 208000`), exactly as in the original.

Example:

```
python3 tnc3epf.py -v -f 208000 *.APL
```

This writes the following to the current directory:
- `EPFLASH.ABS`: the image.
- `<name>.SYM`: a symbol listing for every relocated program that has a symbol table.

Wildcards are expanded by the program itself if the shell doesn't do it (for example cmd.exe).

### Choosing the start address

The firmware version examined looks for the first entry only at 16 KiB boundaries from `0x208000` to `0x2FC000`. The original's default of `0x206000` is not one of them, so pass `-f` with an address that fits your firmware.

## File format

[FORMAT.md](FORMAT.md) describes the image format, the `.APL` relocation and the original tool's quirks, which `tnc3epf.py` reproduces.

## Tests

```
python3 -m unittest discover -s tests
```

The tests build a set of synthetic input files and compare the output byte for byte with what the original `winepf.exe` produced for them (`tests/fixtures/`). To regenerate the fixtures you need wine and a copy of `winepf.exe`:

```
tests/make_fixtures.py path/to/winepf.exe
```

## License

BSD 3-Clause, see [LICENSE](LICENSE).
