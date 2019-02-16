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


# Dependencies

Required: dateutil, pytz, asn1crypto, and the python3 standard library.

Optional: yapf for formatting `a38tool python` output


# Example

```py
import a38.fattura as a38
import datetime

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
f.fattura_elettronica_header.dati_trasmissione = a38.DatiTrasmissione(
    a38.IdTrasmittente("IT", "10293847561"),
    codice_destinatario="FUFUFU")
f.fattura_elettronica_header.cedente_prestatore = cedente_prestatore
f.fattura_elettronica_header.cessionario_committente = cessionario_committente

body = a38.FatturaElettronicaBody()
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

f.fattura_elettronica_body.append(body)

f.validate()

filename = "{}{}_{:05d}.xml".format(
    f.fattura_elettronica_header.cedente_prestatore.dati_anagrafici.id_fiscale_iva.id_paese,
    f.fattura_elettronica_header.cedente_prestatore.dati_anagrafici.id_fiscale_iva.id_codice,
    bill_number)

tree = f.build_etree()
with open(filename, "wb") as out:
    tree.write(out)
```

# Copyright

Copyright 2019 Truelite S.r.l.

This software is released under the Apache License 2.0
