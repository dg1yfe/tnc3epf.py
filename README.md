# tnc3epf

[Deutsch](#deutsch) · [English](#english)

## Deutsch

`tnc3epf.py` erzeugt Flash-Disk-Images für den **TNC3/TNC4e**. Es ersetzt das nur unter Windows lauffähige `winepf.exe` (EPFILE2) und läuft überall, wo Python 3.8 oder neuer installiert ist. Es braucht nur die Standardbibliothek und funktioniert daher unter Linux, macOS und Windows.

Das Programm packt Dateien in ein Image für die Flash-Disk des TNC3. 68000-Programme (`.APL`) werden auf die Flash-Adresse reloziert, an der sie später laufen. Bei gleicher Eingabe ist die Ausgabe Byte für Byte identisch mit der des originalen `winepf.exe`.

### Aufruf

```
python3 tnc3epf.py [-<opt>] { file }
opt:   v verbose
       r don't relocate
       f <hex> TNC3 Flash-EPROMs
       s split output
```

| Option | Wirkung |
|---|---|
| `-v` | Gibt jede Datei mit ihrer Größe aus, am Ende die nächste freie Flash-Adresse. |
| `-r` | Kopiert `.APL`-Dateien unverändert, statt sie zu relozieren. |
| `-f <hex>` | Flash-Adresse des ersten Eintrags (Standard `206000`). Die Ausgabedateien heißen dann `EPFLASH.*` statt `EPFILE.*`. |
| `-s` | Schreibt das Image zusätzlich aufgeteilt für zwei byteweise organisierte EPROMs: `.UPR` erhält die geraden Bytes, `.LWR` die ungeraden. |

Groß- und Kleinschreibung der Optionen spielt keine Rolle. Eine Option mit Argument muss allein stehen, und nach ihr muss ein Leerzeichen folgen (`-f 208000`, nicht `-f208000` oder `-vf 208000`), genau wie beim Original.

Beispiel:

```
python3 tnc3epf.py -v -f 208000 *.APL
```

Damit entstehen im aktuellen Verzeichnis:
- `EPFLASH.ABS`: das Image.
- `<name>.SYM`: eine Symbolliste für jedes relozierte Programm, das eine Symboltabelle hat.

Platzhalter (`*`, `?`) expandiert das Programm selbst, wenn die Shell es nicht tut (zum Beispiel cmd.exe).

#### Wahl der Startadresse

Die untersuchte Firmware-Version sucht den ersten Eintrag nur an 16-KiB-Grenzen von `0x208000` bis `0x2FC000`. Der Standardwert des Originals, `0x206000`, gehört nicht dazu. Gib deshalb mit `-f` eine Adresse an, die zu deiner Firmware passt.

### Dateiformat

[FORMAT.md](FORMAT.md) (englisch) beschreibt das Image-Format, die Relozierung der `.APL`-Dateien und die Eigenheiten des Originals, die `tnc3epf.py` nachbildet.

### Tests

```
python3 -m unittest discover -s tests
```

Die Tests erzeugen synthetische Eingabedateien und vergleichen die Ausgabe Byte für Byte mit dem, was das originale `winepf.exe` daraus erzeugt hat (`tests/fixtures/`). Um diese Referenzdaten neu zu erzeugen, brauchst du wine und eine Kopie von `winepf.exe`:

```
tests/make_fixtures.py pfad/zu/winepf.exe
```

### Lizenz

BSD 3-Clause, siehe [LICENSE](LICENSE).

## English

`tnc3epf.py` builds flash-disk images for the **Symek TNC3** packet-radio controller. It replaces the Windows-only `winepf.exe` (EPFILE2) and runs anywhere Python 3.8 or later is installed. It needs only the standard library, so it works on Linux, macOS and Windows.

The tool packs files into an image for the TNC3's flash disk. 68000 programs (`.APL`) are relocated to the flash address they will run from. For the same input, the output is byte-identical to the original `winepf.exe`.

### Usage

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

#### Choosing the start address

The firmware version examined looks for the first entry only at 16 KiB boundaries from `0x208000` to `0x2FC000`. The original's default of `0x206000` is not one of them, so pass `-f` with an address that fits your firmware.

### File format

[FORMAT.md](FORMAT.md) describes the image format, the `.APL` relocation and the original tool's quirks, which `tnc3epf.py` reproduces.

### Tests

```
python3 -m unittest discover -s tests
```

The tests build a set of synthetic input files and compare the output byte for byte with what the original `winepf.exe` produced for them (`tests/fixtures/`). To regenerate the fixtures you need wine and a copy of `winepf.exe`:

```
tests/make_fixtures.py path/to/winepf.exe
```

### License

BSD 3-Clause, see [LICENSE](LICENSE).
