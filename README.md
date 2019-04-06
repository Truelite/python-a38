# Python A38

Library to generate Italian Fattura Elettronica from Python.

This library implements a declarative data model similar to Django models, that
is designed to describe, validate, serialize and parse Italian Fattura
Elettronica data.

Only part of the specification is implemented, with more added as needs will
arise. You are welcome to implement the missing pieces you need and send a pull
request: the idea is to have a good, free (as in freedom) library to make
billing in Italy with Python easier for everyone.

The library can generate various kinds of fatture that pass validation, and can
parse all the example XML files distributed by
[fatturapa.gov.it](https://www.fatturapa.gov.it/export/fatturazione/it/normativa/f-2.htm)


## Dependencies

Required: dateutil, pytz, asn1crypto, and the python3 standard library.

Optional:
 * yapf for formatting `a38tool python` output
 * lxml for rendering to HTML
 * the wkhtmltopdf command for rendering to PDF
 * requests for downloading CA certificates for signature verification


## `a38tool` script

A simple command line wrapper to the library functions is available as `a38tool`:

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

See [a38tool.md](a38tool.md) for more details.



## Example code

```py
import a38.fattura as a38
from a38.validation import Validation
import datetime
import sys

cedente_prestatore = a38.CedentePrestatore(
    a38.DatiAnagraficiCedentePrestatore(
        a38.IdFiscaleIVA("IT", "01234567890"),
        codice_fiscale="NTNBLN22C23A123U",
        anagrafica=a38.Anagrafica(denominazione="Test User"),
        regime_fiscale="RF01",
    ),
    a38.Sede(indirizzo="via Monferrato", numero_civico="1", cap="50100", comune="Firenze", provincia="FI", nazione="IT"),
    iscrizione_rea=a38.IscrizioneREA(
        ufficio="FI",
        numero_rea="123456",
        stato_liquidazione="LN",
    ),
    contatti=a38.Contatti(email="local_part@pec_domain.it"),
)

cessionario_committente = a38.CessionarioCommittente(
    a38.DatiAnagraficiCessionarioCommittente(
        a38.IdFiscaleIVA("IT", "76543210987"),
        anagrafica=a38.Anagrafica(denominazione="A Company SRL"),
    ),
    a38.Sede(indirizzo="via Langhe", numero_civico="1", cap="50142", comune="Firenze", provincia="FI", nazione="IT"),
)

bill_number = 1

f = a38.FatturaPrivati12()
f.fattura_elettronica_header.dati_trasmissione.id_trasmittente = a38.IdTrasmittente("IT", "10293847561")
f.fattura_elettronica_header.dati_trasmissione.codice_destinatario = "FUFUFUF"
f.fattura_elettronica_header.cedente_prestatore = cedente_prestatore
f.fattura_elettronica_header.cessionario_committente = cessionario_committente

body = f.fattura_elettronica_body[0]
body.dati_generali.dati_generali_documento = a38.DatiGeneraliDocumento(
    tipo_documento="TD01",
    divisa="EUR",
    data=datetime.date.today(),
    numero=bill_number,
    causale=["Test billing"],
)

body.dati_beni_servizi.add_dettaglio_linee(
    descrizione="Test item", quantita=2, unita_misura="kg",
    prezzo_unitario="25.50", aliquota_iva="22.00")

body.dati_beni_servizi.add_dettaglio_linee(
    descrizione="Other item", quantita=1, unita_misura="kg",
    prezzo_unitario="15.50", aliquota_iva="22.00")

body.dati_beni_servizi.build_dati_riepilogo()
body.build_importo_totale_documento()

res = Validation()
f.validate(res)
if res.warnings:
    for w in res.warnings:
        print(str(w), file=sys.stderr)
if res.errors:
    for e in res.errors:
        print(str(e), file=sys.stderr)

filename = "{}{}_{:05d}.xml".format(
    f.fattura_elettronica_header.cedente_prestatore.dati_anagrafici.id_fiscale_iva.id_paese,
    f.fattura_elettronica_header.cedente_prestatore.dati_anagrafici.id_fiscale_iva.id_codice,
    bill_number)

tree = f.build_etree()
with open(filename, "wb") as out:
    tree.write(out)
```


# Digital signatures

Digital signatures on Firma Elettronica are
[CAdES](https://en.wikipedia.org/wiki/CAdES_(computing)) signatures.

openssl cal verify the signatures, but not yet generate them. A patch to sign
with CAdES [has been recently merged](https://github.com/openssl/openssl/commit/e85d19c68e7fb3302410bd72d434793e5c0c23a0)
but not yet released as of 2019-02-26.

## Downloading CA certificates

CA certificates for validating digital certificates are
[distributed by the EU in XML format](https://ec.europa.eu/cefdigital/wiki/display/cefdigital/esignature).
See also [the AGID page about it](https://www.agid.gov.it/it/piattaforme/firma-elettronica-qualificata/certificati).

There is a [Trusted List Browser](https://webgate.ec.europa.eu/tl-browser/) but
apparently no way of getting a simple bundle of certificates useable by
openssl.

`a38tool` has basic features to download and parse CA certificate information,
and maintain a CA certificate directory:

```
a38tool update_capath certdir/ --remove-old
```

No particular effort is made to validate the downloaded certificates, besides
the standard HTTPS checks performed by the [requests
library](http://docs.python-requests.org/en/master/).

## Verifying signed `.p7m` files

Once you have a CA certificate directory, verifying signed p7m files is quite
straightforward:

```
openssl cms -verify -in tests/data/test.txt.p7m -inform der -CApath certs/
```


# Useful links

XSLT stylesheets for displaying fatture:

* From fatturapa.gov.it for
  [privati](https://www.fatturapa.gov.it/export/fatturazione/sdi/fatturapa/v1.2/fatturaordinaria_v1.2.xsl)
  and
  [PA](https://www.fatturapa.gov.it/export/fatturazione/sdi/fatturapa/v1.2/fatturapa_v1.2.xsl)
* From [AssoSoftware](http://www.assosoftware.it/allegati/assoinvoice/FoglioStileAssoSoftware.zip)


# Copyright

Copyright 2019 Truelite S.r.l.

This software is released under the Apache License 2.0
