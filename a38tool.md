# `a38tool`

General command line help:

```text
$ a38tool --help
usage: a38tool [-h] [--verbose] [--debug] {json,xml,python} ...

Handle fattura elettronica files

positional arguments:
  {json,xml,python}  actions
    json             Output a fattura in JSON
    xml              Output a fattura in XML
    python           Output a fattura as Python code

optional arguments:
  -h, --help         show this help message and exit
  --verbose, -v      verbose output
  --debug            debug output
```

### Convert a fattura to JSON

```text
$ a38tool json --help
usage: a38tool json [-h] [-o OUTPUT] [--indent INDENT] files [files ...]

positional arguments:
  files                 input files (.xml or .xml.p7m)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output file (default: standard output)
  --indent INDENT       indentation space (default: 1, use 'no' for all in one
                        line)
```

Example:

```text
$ a38tool json doc/IT01234567890_FPR02.xml
{
 "fattura_elettronica_header": {
  "dati_trasmissione": {
   "id_trasmittente": {
    "id_paese": "IT",
    "id_codice": "01234567890"
…
```

Use `--indent=no` to output a json per line, making it easy to separate reparse
a group of JSON fatture:

```text
$ a38tool json --indent=no doc/*.xml
{"fattura_elettronica_header": {"dati_tr…
{"fattura_elettronica_header": {"dati_tr…
{"fattura_elettronica_header": {"dati_tr…
…
```

### Extract XML from a `.p7m` signed fattura

```text
$ a38tool xml --help
usage: a38tool xml [-h] [-o OUTPUT] files [files ...]

positional arguments:
  files                 input files (.xml or .xml.p7m)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output file (default: standard output)
```

### Generate Python code

You can convert a fattura to Python code: this is a quick way to start writing
a software that generates fatture similar to an existing one.

```text
$ a38tool python --help
usage: a38tool python [-h] [-o OUTPUT] [--namespace NAMESPACE] [--unformatted]
                      files [files ...]

positional arguments:
  files                 input files (.xml or .xml.p7m)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output file (default: standard output)
  --namespace NAMESPACE
                        namespace to use for the model classes (default: the
                        module fully qualified name)
  --unformatted         disable code formatting, outputting a single-line
                        statement
```

Example:

```text
$ a38tool python doc/IT01234567890_FPR02.xml
a38.fattura.FatturaPrivati12(
    fattura_elettronica_header=a38.fattura.FatturaElettronicaHeader(
        dati_trasmissione=a38.fattura.DatiTrasmissione(
            id_trasmittente=a38.fattura.IdTrasmittente(
                id_paese='IT', id_codice='01234567890'),
            progressivo_invio='00001',
…
```
