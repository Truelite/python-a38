from unittest import TestCase, SkipTest
import a38.fattura as a38
from a38 import validation
from decimal import Decimal
import datetime
import io


class TestFatturaMixin:
    def assert_validates(self, value, warnings=[], errors=[]):
        val = validation.Validation()
        value.validate(val)
        self.assertEqual([str(x) for x in val.warnings], warnings)
        self.assertEqual([str(x) for x in val.errors], errors)


class TestAnagrafica(TestFatturaMixin, TestCase):
    def test_validation(self):
        a = a38.Anagrafica()

        self.assert_validates(a, errors=[
            'nome: nome and cognome, or denominazione, must be set',
            'cognome: nome and cognome, or denominazione, must be set',
            'denominazione: nome and cognome, or denominazione, must be set',
        ])

        a.nome = "Test"
        self.assert_validates(a, errors=[
            "cognome: nome and cognome must both be set if denominazione is empty",
        ])

        a.cognome = "Test1"
        self.assert_validates(a)

        a.nome = None
        self.assert_validates(a, errors=[
            "nome: nome and cognome must both be set if denominazione is empty",
        ])

        a.denominazione = "Test Test1"
        self.assert_validates(a, errors=[
            "cognome: cognome must not be set if denominazione is not empty",
        ])

        a.denominazione = "Test Test1"
        a.nome = "Test"
        self.assert_validates(a, errors=[
            "nome: nome and cognome must not be set if denominazione is not empty",
            "cognome: nome and cognome must not be set if denominazione is not empty",
        ])

        a.cognome = None
        self.assert_validates(a, errors=[
            "nome: nome must not be set if denominazione is not empty",
        ])

        a.nome = None
        self.assert_validates(a)


class TestDatiTrasmissione(TestFatturaMixin, TestCase):
    def test_validation(self):
        dt = a38.DatiTrasmissione(
                a38.IdTrasmittente("ID", "1234567890"),
                "12345", "FPR12")

        self.assert_validates(dt, errors=[
            # "codice_destinatario: one of codice_destinatario or pec_destinatario must be set",
            # "pec_destinatario: one of codice_destinatario or pec_destinatario must be set",
            "codice_destinatario: [00426] pec_destinatario has no value while codice_destinatario has value 0000000",
            "pec_destinatario: [00426] pec_destinatario has no value while codice_destinatario has value 0000000",
        ])

        dt.codice_destinatario = "FUFUFU"
        self.assert_validates(dt, errors=[
            "codice_destinatario: [00427] codice_destinatario has 6 characters on a Fattura Privati",
        ])

        dt.codice_destinatario = "FUFUFUF"
        self.assert_validates(dt)

        dt.pec_destinatario = "local_part@example.org"
        self.assert_validates(dt, errors=[
            "codice_destinatario: [00426] pec_destinatario has value while codice_destinatario has value 0000000",
            "pec_destinatario: [00426] pec_destinatario has value while codice_destinatario has value 0000000",
        ])

        dt.codice_destinatario = None
        self.assert_validates(dt)


class TestDatiBeniServizi(TestFatturaMixin, TestCase):
    def test_add_dettaglio_linee(self):
        o = a38.DatiBeniServizi()
        o.add_dettaglio_linee(descrizione="Line 1", quantita=2, unita_misura="m²", prezzo_unitario=7, aliquota_iva=22)
        o.add_dettaglio_linee(descrizione="Line 2", quantita=1, unita_misura="A", prezzo_unitario="0.4", aliquota_iva=22)
        self.assertEqual(len(o.dettaglio_linee), 2)
        self.assertEqual(o.dettaglio_linee[0], a38.DettaglioLinee(
            numero_linea=1, descrizione="Line 1", quantita=2, unita_misura="m²",
            prezzo_unitario=7, prezzo_totale=14, aliquota_iva=22))
        self.assertEqual(o.dettaglio_linee[1], a38.DettaglioLinee(
            numero_linea=2, descrizione="Line 2", quantita=1, unita_misura="A",
            prezzo_unitario="0.4", prezzo_totale="0.4", aliquota_iva=22))

    def test_add_dettaglio_linee_without_quantita(self):
        o = a38.DatiBeniServizi()
        o.add_dettaglio_linee(descrizione="Line 1", prezzo_unitario=7, aliquota_iva=22)
        self.assertEqual(len(o.dettaglio_linee), 1)
        self.assertEqual(o.dettaglio_linee[0], a38.DettaglioLinee(1, descrizione="Line 1", prezzo_unitario=7, prezzo_totale=7, aliquota_iva=22))

    def test_build_dati_riepilogo(self):
        o = a38.DatiBeniServizi()
        o.add_dettaglio_linee(descrizione="Line 1", quantita=2, unita_misura="m²", prezzo_unitario=7, aliquota_iva=22)
        o.add_dettaglio_linee(descrizione="Line 2", quantita=1, unita_misura="A", prezzo_unitario="0.4", aliquota_iva=22)
        o.add_dettaglio_linee(descrizione="Line 3", quantita="3.5", unita_misura="A", prezzo_unitario="0.5", aliquota_iva=10)
        o.build_dati_riepilogo()

        self.assertEqual(len(o.dati_riepilogo), 2)
        self.assertEqual(o.dati_riepilogo[0], a38.DatiRiepilogo(aliquota_iva="10", imponibile_importo="1.75",  imposta="0.175", esigibilita_iva="I"))
        self.assertEqual(o.dati_riepilogo[1], a38.DatiRiepilogo(aliquota_iva="22", imponibile_importo="14.40", imposta="3.168", esigibilita_iva="I"))


class TestFatturaElettronicaBody(TestFatturaMixin, TestCase):
    def test_build_importo_totale_documento(self):
        o = a38.FatturaElettronicaBody()
        o.dati_beni_servizi.add_dettaglio_linee(descrizione="Line 1", quantita=2, unita_misura="m²", prezzo_unitario=7, aliquota_iva=22)
        o.dati_beni_servizi.add_dettaglio_linee(descrizione="Line 2", quantita=1, unita_misura="A", prezzo_unitario="0.4", aliquota_iva=22)
        o.dati_beni_servizi.add_dettaglio_linee(descrizione="Line 3", quantita="3.5", unita_misura="A", prezzo_unitario="0.5", aliquota_iva=10)
        o.dati_beni_servizi.build_dati_riepilogo()
        o.build_importo_totale_documento()

        self.assertEqual(o.dati_generali.dati_generali_documento.importo_totale_documento, Decimal("19.493"))


class TestFatturaPrivati12(TestFatturaMixin, TestCase):
    def build_sample(self):
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

        f = a38.FatturaPrivati12()
        f.fattura_elettronica_header.dati_trasmissione.update(
            a38.IdTrasmittente("IT", "10293847561"),
            codice_destinatario="FUFUFUF",
        )
        f.fattura_elettronica_header.cedente_prestatore = cedente_prestatore
        f.fattura_elettronica_header.cessionario_committente = cessionario_committente

        body = f.fattura_elettronica_body[0]
        body.dati_generali.dati_generali_documento = a38.DatiGeneraliDocumento(
            tipo_documento="TD01",
            divisa="EUR",
            data=datetime.date(2019, 1, 1),
            numero=1,
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

        return f

    def test_initial_body_exists(self):
        f = a38.FatturaPrivati12()
        self.assertEqual(len(f.fattura_elettronica_body), 1)
        self.assertFalse(f.fattura_elettronica_body[0].has_value())

    def test_validate(self):
        f = self.build_sample()
        self.assertEqual(f.fattura_elettronica_header.dati_trasmissione.formato_trasmissione, "FPR12")
        self.assert_validates(f)

    def test_serialize(self):
        f = self.build_sample()
        self.assertEqual(f.fattura_elettronica_header.dati_trasmissione.formato_trasmissione, "FPR12")
        tree = f.build_etree()
        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml = out.getvalue()

        self.assertIn('<ns0:FatturaElettronica xmlns:ns0="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2" versione="FPR12">', xml)
        self.assertIn('<FormatoTrasmissione>FPR12</FormatoTrasmissione>', xml)

    def test_serialize_lxml(self):
        from a38 import builder
        if not builder.HAVE_LXML:
            raise SkipTest("lxml is not available")

        f = self.build_sample()
        tree = f.build_etree(lxml=True)
        with io.BytesIO() as out:
            tree.write(out)
            xml = out.getvalue()

        self.assertIn(b'<ns0:FatturaElettronica xmlns:ns0="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2" versione="FPR12">', xml)
        self.assertIn(b'<FormatoTrasmissione>FPR12</FormatoTrasmissione>', xml)

    def test_to_python(self):
        f = self.build_sample()
        py = f.to_python(namespace="a38")
        parsed = eval(py)
        self.assertEqual(f, parsed)

    def test_parse(self):
        f = self.build_sample()
        tree = f.build_etree()
        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml1 = out.getvalue()

        f = a38.FatturaPrivati12()
        f.from_etree(tree.getroot())
        self.assert_validates(f)
        tree = f.build_etree()
        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml2 = out.getvalue()

        self.assertEqual(xml1, xml2)

        f = a38.auto_from_etree(tree.getroot())
        self.assert_validates(f)
        tree = f.build_etree()
        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml2 = out.getvalue()


class TestSamples(TestFatturaMixin, TestCase):
    def test_parse_dati_trasporto(self):
        import xml.etree.ElementTree as ET
        tree = ET.parse("tests/data/dati_trasporto.xml")
        a38.auto_from_etree(tree.getroot())
