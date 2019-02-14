from unittest import TestCase
import a38.fattura as a38
from a38 import validation
from decimal import Decimal


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
