<p align="center"><img src="assets/logo.svg" alt="tnc3epf logo" width="200"></p>

# tnc3epf

[Deutsch](#deutsch) · [English](#english)

## Deutsch

`tnc3epf.py` erzeugt Flash-Disk-Images für den **TNC3/TNC4e**. Es ersetzt das nur unter Windows lauffähige `winepf.exe` (EPFILE2) und läuft überall, wo Python 3.8 oder neuer installiert ist. Es braucht nur die Standardbibliothek und funktioniert daher unter Linux, macOS und Windows.

Das Programm packt Dateien in ein Image für die Flash-Disk des TNC3. 68000-Programme (`.APL`) werden auf die Flash-Adresse reloziert, an der sie später laufen. Bei gleicher Eingabe ist die Ausgabe Byte für Byte identisch mit der des originalen `winepf.exe`, mit zwei bewussten Ausnahmen: der Standard-Startadresse und den Dateizeiten (siehe unten).

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
| `-f <hex>` | Flash-Adresse des ersten Eintrags (Standard `208000`). Die Ausgabedateien heißen dann `EPFLASH.*` statt `EPFILE.*`. |
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

Das Image muss für die Adresse gebaut werden, an der es im Flash landet, weil die Programme auf diese Adresse reloziert werden. Die Adresse hängt vom Gerät und von den Flash-Bausteinen ab:

| Gerät | Busbreite | Flash-Typ | `-f` | Flash gesamt |
|---|---|---|---|---|
| TNC31 | 8 Bit | AM29F010 | `208000` | 128 KB |
| TNC31 | 8 Bit | AM29F040 | `210000` | 512 KB |
| TNC3 | 16 Bit | AM29F010 | `208000` | 256 KB |
| TNC3 | 16 Bit | AM29F040 | `220000` | 1 MB |
| TNC4 | 16 Bit | AM29F040 | `820000` | 1 MB |

`208000` ist der Standard, `-f` kann dann entfallen. Die Regel dahinter: Das Betriebssystem belegt die ersten 32 KiB des Flash, und die Flash-Disk beginnt an der nächsten Grenze eines Löschsektors. Ein Löschsektor ist beim AM29F010 16 KiB und beim AM29F040 64 KiB groß, bei 16 Bit Busbreite (zwei Bausteine) jeweils doppelt so groß. Der Flash beginnt beim TNC3/TNC31 an `0x200000`, beim TNC4 an `0x800000`.

Alle Dateien für die Flash-Disk gehören in einen Aufruf, zum Beispiel `python3 tnc3epf.py -v -f 220000 *.APL *.NET *.XTS *.XTP`. Nur `.APL`-Dateien werden reloziert, alle anderen werden unverändert übernommen.

Das Original verwendet ohne `-f` die Adresse `0x206000`. Die passt nicht zu Mini OS 3.12, weil das Betriebssystem selbst bis `0x206F71` reicht. Vermutlich stammt der Wert aus der Zeit eines älteren, kleineren Betriebssystems. Deshalb ist der Standard von `tnc3epf.py` `0x208000`. Einzelne `.APL`-Dateien kann der TNC3 übrigens auch selbst mit `flash -a` in die Flash-Disk aufnehmen.

#### Dateizeiten

`tnc3epf.py` speichert die tatsächliche Änderungszeit jeder Datei. Das Original liegt dabei für einen Teil des Jahres eine Stunde daneben, je nachdem, ob es während der Sommer- oder der Winterzeit läuft (Details in [FORMAT.md](FORMAT.md)).

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

The tool packs files into an image for the TNC3's flash disk. 68000 programs (`.APL`) are relocated to the flash address they will run from. For the same input, the output is byte-identical to the original `winepf.exe`, with two deliberate exceptions: the default start address and the file times (see below).

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
| `-f <hex>` | Flash address of the first entry (default `208000`). Output files are named `EPFLASH.*` instead of `EPFILE.*`. |
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

The image must be built for the address it will be written to, because the programs are relocated to that address. The address depends on the unit and its flash chips:

| Unit | Bus width | Flash type | `-f` | Total flash |
|---|---|---|---|---|
| TNC31 | 8 bit | AM29F010 | `208000` | 128 KB |
| TNC31 | 8 bit | AM29F040 | `210000` | 512 KB |
| TNC3 | 16 bit | AM29F010 | `208000` | 256 KB |
| TNC3 | 16 bit | AM29F040 | `220000` | 1 MB |
| TNC4 | 16 bit | AM29F040 | `820000` | 1 MB |

`208000` is the default, so `-f` can be left out there. The rule behind the table: the operating system occupies the first 32 KiB of the flash, and the flash disk starts at the next erase-sector boundary. An erase sector is 16 KiB on the AM29F010 and 64 KiB on the AM29F040, twice that with a 16-bit bus (two chips). The flash starts at `0x200000` on the TNC3/TNC31 and at `0x800000` on the TNC4.

Pass all files for the flash disk in one call, for example `python3 tnc3epf.py -v -f 220000 *.APL *.NET *.XTS *.XTP`. Only `.APL` files are relocated; all others are copied unchanged.

Without `-f`, the original uses `0x206000`. That doesn't fit Mini OS 3.12, whose own code reaches up to `0x206F71`; the value probably dates from an older, smaller OS. That's why `tnc3epf.py` defaults to `0x208000`. The TNC3 can also add single `.APL` files to its flash disk itself, with `flash -a`.

#### File times

`tnc3epf.py` stores each file's actual modification time. The original gets it wrong by one hour for part of the year, depending on whether it runs during summer or winter time (details in [FORMAT.md](FORMAT.md)).

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
