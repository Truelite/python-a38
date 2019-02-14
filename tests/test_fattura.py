from unittest import TestCase
import a38.fattura as a38
from a38 import validation
from decimal import Decimal
import datetime
import io


class TestAnagrafica(TestCase):
    def test_validation(self):
        a = a38.Anagrafica()

        with self.assertRaises(validation.ValidationErrors) as e:
            a.validate()
        self.assertEqual(e.exception.errors[0].field_name, "nome")
        self.assertEqual(e.exception.errors[0].msg, "nome and cognome, or denominazione, must be set")
        self.assertEqual(e.exception.errors[1].field_name, "cognome")
        self.assertEqual(e.exception.errors[1].msg, "nome and cognome, or denominazione, must be set")
        self.assertEqual(e.exception.errors[2].field_name, "denominazione")
        self.assertEqual(e.exception.errors[2].msg, "nome and cognome, or denominazione, must be set")

        a.nome = "Test"
        with self.assertRaises(validation.ValidationError) as e:
            a.validate()
        self.assertEqual(e.exception.field_name, "cognome")
        self.assertEqual(e.exception.msg, "nome and cognome must both be set if denominazione is empty")

        a.cognome = "Test1"
        a.validate()

        a.nome = None
        with self.assertRaises(validation.ValidationError) as e:
            a.validate()
        self.assertEqual(e.exception.field_name, "nome")
        self.assertEqual(e.exception.msg, "nome and cognome must both be set if denominazione is empty")

        a.denominazione = "Test Test1"
        with self.assertRaises(validation.ValidationError) as e:
            a.validate()
        self.assertEqual(e.exception.field_name, "cognome")
        self.assertEqual(e.exception.msg, "cognome must not be set if denominazione is not empty")

        a.denominazione = "Test Test1"
        a.nome = "Test"
        with self.assertRaises(validation.ValidationErrors) as e:
            a.validate()
        self.assertEqual(e.exception.errors[0].field_name, "nome")
        self.assertEqual(e.exception.errors[0].msg, "nome and cognome must not be set if denominazione is not empty")
        self.assertEqual(e.exception.errors[1].field_name, "cognome")
        self.assertEqual(e.exception.errors[1].msg, "nome and cognome must not be set if denominazione is not empty")

        a.cognome = None
        with self.assertRaises(validation.ValidationError) as e:
            a.validate()
        self.assertEqual(e.exception.field_name, "nome")
        self.assertEqual(e.exception.msg, "nome must not be set if denominazione is not empty")

        a.nome = None
        a.validate()


class TestDatiTrasmissione(TestCase):
    def test_validation(self):
        dt = a38.DatiTrasmissione(
                a38.IdTrasmittente("ID", "1234567890"),
                "12345", "FPR12")

        with self.assertRaises(validation.ValidationErrors) as e:
            dt.validate()
        self.assertEqual(e.exception.errors[0].field_name, "codice_destinatario")
        self.assertEqual(e.exception.errors[0].msg, "one of codice_destinatario or pec_destinatario must be set")
        self.assertEqual(e.exception.errors[1].field_name, "pec_destinatario")
        self.assertEqual(e.exception.errors[1].msg, "one of codice_destinatario or pec_destinatario must be set")

        dt.codice_destinatario = "FUFUFU"
        dt.validate()

        dt.pec_destinatario = "local_part@example.org"
        dt.validate()

        dt.codice_destinatario = None
        dt.validate()


class TestDatiBeniServizi(TestCase):
    def test_add_dettaglio_linee(self):
        o = a38.DatiBeniServizi()
        o.add_dettaglio_linee(descrizione="Line 1", quantita=2, unita_misura="m²", prezzo_unitario=7, aliquota_iva=22)
        o.add_dettaglio_linee(descrizione="Line 2", quantita=1, unita_misura="A", prezzo_unitario="0.4", aliquota_iva=22)
        self.assertEqual(len(o.dettaglio_linee), 2)
        self.assertEqual(o.dettaglio_linee[0], a38.DettaglioLinee(1, "Line 1", 2, "m²", 7, 14, 22))
        self.assertEqual(o.dettaglio_linee[1], a38.DettaglioLinee(2, "Line 2", 1, "A", "0.4", "0.4", 22))

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
        self.assertEqual(o.dati_riepilogo[0], a38.DatiRiepilogo("10", "1.75", "0.175", "I"))
        self.assertEqual(o.dati_riepilogo[1], a38.DatiRiepilogo("22", "14.40", "3.168", "I"))


class TestFatturaElettronicaBody(TestCase):
    def test_build_importo_totale_documento(self):
        o = a38.FatturaElettronicaBody()
        o.dati_beni_servizi.add_dettaglio_linee(descrizione="Line 1", quantita=2, unita_misura="m²", prezzo_unitario=7, aliquota_iva=22)
        o.dati_beni_servizi.add_dettaglio_linee(descrizione="Line 2", quantita=1, unita_misura="A", prezzo_unitario="0.4", aliquota_iva=22)
        o.dati_beni_servizi.add_dettaglio_linee(descrizione="Line 3", quantita="3.5", unita_misura="A", prezzo_unitario="0.5", aliquota_iva=10)
        o.dati_beni_servizi.build_dati_riepilogo()
        o.build_importo_totale_documento()

        self.assertEqual(o.dati_generali.dati_generali_documento.importo_totale_documento, Decimal("19.493"))


class TestFatturaPrivati12(TestCase):
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
        f.fattura_elettronica_header.dati_trasmissione = a38.DatiTrasmissione(
            a38.IdTrasmittente("IT", "10293847561"),
            codice_destinatario="FUFUFU")
        f.fattura_elettronica_header.cedente_prestatore = cedente_prestatore
        f.fattura_elettronica_header.cessionario_committente = cessionario_committente
        f.fattura_elettronica_body.dati_generali.dati_generali_documento = a38.DatiGeneraliDocumento(
            tipo_documento="TD01",
            divisa="EUR",
            data=datetime.date(2019, 1, 1),
            numero=1,
            causale="Test billing",
        )

        f.fattura_elettronica_body.dati_beni_servizi.add_dettaglio_linee(
                descrizione="Test item", quantita=2, unita_misura="kg",
                prezzo_unitario="25.50", aliquota_iva="22.00")

        f.fattura_elettronica_body.dati_beni_servizi.add_dettaglio_linee(
                descrizione="Other item", quantita=1, unita_misura="kg",
                prezzo_unitario="15.50", aliquota_iva="22.00")

        f.fattura_elettronica_body.dati_beni_servizi.build_dati_riepilogo()
        f.fattura_elettronica_body.build_importo_totale_documento()

        return f

    def test_validate(self):
        f = self.build_sample()

        # build_etree also fills formato_trasmissione
        self.assertIsNone(f.fattura_elettronica_header.dati_trasmissione.formato_trasmissione)
        f.validate()
        self.assertEqual(f.fattura_elettronica_header.dati_trasmissione.formato_trasmissione, "FPR12")

    def test_serialize(self):
        f = self.build_sample()

        # build_etree also fills formato_trasmissione
        self.assertIsNone(f.fattura_elettronica_header.dati_trasmissione.formato_trasmissione)
        tree = f.build_etree()
        self.assertEqual(f.fattura_elettronica_header.dati_trasmissione.formato_trasmissione, "FPR12")

        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml = out.getvalue()

        self.assertIn('<ns0:FatturaElettronica xmlns:ns0="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2" versione="FPR12">', xml)
        self.assertIn('<FormatoTrasmissione>FPR12</FormatoTrasmissione>', xml)

    def test_parse(self):
        f = self.build_sample()
        tree = f.build_etree()
        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml1 = out.getvalue()

        f = a38.FatturaPrivati12()
        f.from_etree(tree.getroot())
        f.validate()
        tree = f.build_etree()
        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml2 = out.getvalue()

        self.assertEqual(xml1, xml2)

        f = a38.auto_from_etree(tree.getroot())
        f.validate()
        tree = f.build_etree()
        with io.StringIO() as out:
            tree.write(out, encoding="unicode")
            xml2 = out.getvalue()
