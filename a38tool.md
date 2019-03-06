# `a38tool`

General command line help:

```text
$ a38tool --help
usage: a38tool [-h] [--verbose] [--debug]
               {json,xml,python,diff,validate,html,pdf,update_capath} ...

Handle fattura elettronica files

positional arguments:
  {json,xml,python,diff,validate,html,pdf,update_capath}
                        actions
    json                output a fattura in JSON
    xml                 output a fattura in XML
    python              output a fattura as Python code
    diff                show the difference between two fatture
    validate            validate the contents of a fattura
    html                render a Fattura as HTML using a .xslt stylesheet
    pdf                 render a Fattura as PDF using a .xslt stylesheet
    update_capath       create/update an openssl CApath with CA certificates
                        that can be used to validate digital signatures

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         verbose output
  --debug               debug output
```

### Difference between two fatture

```text
$ a38tool diff --help
usage: a38tool diff [-h] first second

positional arguments:
  first       first input file (.xml or .xml.p7m)
  second      second input file (.xml or .xml.p7m)

optional arguments:
  -h, --help  show this help message and exit
```

Example:

```text
$ a38tool diff doc/IT01234567890_FPR01.xml doc/IT01234567890_FPR02.xml
fattura_elettronica_header.dati_trasmissione.codice_destinatario: first: ABC1234, second: 0000000
fattura_elettronica_header.dati_trasmissione.pec_destinatario: first is not set
fattura_elettronica_header.cedente_prestatore.dati_anagrafici.regime_fiscale: first: RF19, second: RF01
fattura_elettronica_header.cessionario_committente.dati_anagrafici.anagrafica.denominazione: first: DITTA BETA, second: …
fattura_elettronica_body.0.dati_generali.dati_contratto: second is not set
fattura_elettronica_body.0.dati_beni_servizi.dettaglio_linee.0.descrizione: first: DESCRIZIONE DELLA FORNITURA, second: …
…
$ echo $?
1
```

### Validate a fattura

```text
$ a38tool validate --help
usage: a38tool validate [-h] file

positional arguments:
  file        input file (.xml or .xml.p7m)

optional arguments:
  -h, --help  show this help message and exit
```

Example:

```text
$ a38tool validate doc/IT01234567890_FPR01.xml
fattura_elettronica_body.0.dati_beni_servizi.unita_misura: field must be present when quantita is set
$ echo $?
1
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


### Render to HTML or PDF

You can use a .xslt file to render e fattura to HTML or PDF.

```text
$ a38tool html --help
usage: a38tool html [-h] [-f] [-o OUTPUT] stylesheet files [files ...]

positional arguments:
  stylesheet            .xsl/.xslt stylesheet file to use for rendering
  files                 input files (.xml or .xml.p7m)

optional arguments:
  -h, --help            show this help message and exit
  -f, --force           overwrite existing output files
  -o OUTPUT, --output OUTPUT
                        output file; use {dirname} for the source file path,
                        {basename} for the source file name (default:
                        '{dirname}/{basename}{ext}.html'
```

Example:

```text
$ a38tool -v html -f doc/fatturaordinaria_v1.2.1.xsl doc/IT01234567890_FPR02.xml
INFO doc/IT01234567890_FPR02.xml: writing doc/IT01234567890_FPR02.xml.html
```

```text
$ a38tool -v pdf -f doc/fatturaordinaria_v1.2.1.xsl doc/IT01234567890_FPR02.xml
INFO doc/IT01234567890_FPR02.xml: writing doc/IT01234567890_FPR02.xml.pdf
```

