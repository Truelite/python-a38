from . import models
from . import fields
import re

#
# This file describes the data model of the Italian Fattura Elettronica.
#
# Models and fields are inspired from Django's ORM.
#
# XML tag names are built automatically from the field names, and can be
# specified explicitly with the xmltag argument.
#
# Models can be used as fields using `fields.ModelField`. Specifying a Model
# class as a field, automatically wraps it in a `ModelField`.
#


NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"
NS10 = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.0"
NS_SIG = "http://www.w3.org/2000/09/xmldsig#"


class FullNameMixin:
    """
    Helper for classes that have the nome+cognome/denominazione way of naming.

    Validate that nome+cognome and denominazione are mutually exclusive, and
    provide a full_name property that returns whichever is set.
    """

    @property
    def full_name(self):
        """
        Return denominazione or "{nome} {cognome}", whichever is set.

        If none are set, return None
        """
        if self.denominazione is not None:
            return self.denominazione
        elif self.nome is not None and self.cognome is not None:
            return self.nome + " " + self.cognome
        else:
            return None

    def validate_model(self, validation):
        super().validate_model(validation)
        if self.denominazione is None:
            if self.nome is None and self.cognome is None:
                validation.add_error(
                        (self._meta["nome"], self._meta["cognome"], self._meta["denominazione"]),
                        "nome and cognome, or denominazione, must be set")
            elif self.nome is None:
                validation.add_error(
                        self._meta["nome"],
                        "nome and cognome must both be set if denominazione is empty")
            elif self.cognome is None:
                validation.add_error(
                        self._meta["cognome"],
                        "nome and cognome must both be set if denominazione is empty")
        else:
            should_not_be_set = []
            if self.nome is not None:
                should_not_be_set.append(self._meta["nome"])
            if self.cognome is not None:
                should_not_be_set.append(self._meta["cognome"])
            if should_not_be_set:
                validation.add_error(
                        should_not_be_set,
                        "{} must not be set if denominazione is not empty".format(
                            " and ".join(x.name for x in should_not_be_set)))


class IdFiscale(models.Model):
    id_paese = fields.StringField(length=2)
    id_codice = fields.StringField(max_length=28)


class IdTrasmittente(IdFiscale):
    pass


class IdFiscaleIVA(IdFiscale):
    pass


class ContattiTrasmittente(models.Model):
    telefono = fields.StringField(min_length=5, max_length=12, null=True)
    email = fields.StringField(min_length=7, max_length=256, null=True)


class DatiTrasmissione(models.Model):
    id_trasmittente = IdTrasmittente
    progressivo_invio = fields.ProgressivoInvioField()
    formato_trasmissione = fields.StringField(length=5, choices=("FPR12", "FPA12"))
    codice_destinatario = fields.StringField(null=True, min_length=6, max_length=7, default="0000000")
    contatti_trasmittente = fields.ModelField(ContattiTrasmittente, null=True)
    pec_destinatario = fields.StringField(null=True, min_length=8, max_length=256, xmltag="PECDestinatario")

    def validate_model(self, validation):
        super().validate_model(validation)
        if self.codice_destinatario is None and self.pec_destinatario is None:
            validation.add_error(
                    (self._meta["codice_destinatario"], self._meta["pec_destinatario"]),
                    "one of codice_destinatario or pec_destinatario must be set")

        # Se la fattura deve essere recapitata ad un soggetto che intende
        # ricevere le fatture elettroniche attraverso il canale PEC, il campo
        # deve essere valorizzato con sette zeri (“0000000”) e deve essere
        # valorizzato il campo PECDestinatario

        if self.pec_destinatario is None and self.codice_destinatario == "0000000":
            validation.add_error(
                    (self._meta["codice_destinatario"], self._meta["pec_destinatario"]),
                    "pec_destinatario has no value while codice_destinatario has value 0000000",
                    code="00426")

        if (self.pec_destinatario is not None and self.codice_destinatario is
                not None and self.codice_destinatario != "0000000"):
            validation.add_error(
                    (self._meta["codice_destinatario"], self._meta["pec_destinatario"]),
                    "pec_destinatario has value while codice_destinatario has value 0000000",
                    code="00426")

        if self.formato_trasmissione == "FPA12" and len(self.codice_destinatario) == 7:
            validation.add_error(
                    self._meta["codice_destinatario"],
                    "codice_destinatario has 7 characters on a Fattura PA",
                    code="00427")

        if self.formato_trasmissione == "FPR12" and len(self.codice_destinatario) == 6:
            validation.add_error(
                    self._meta["codice_destinatario"],
                    "codice_destinatario has 6 characters on a Fattura Privati",
                    code="00427")


class Anagrafica(FullNameMixin, models.Model):
    denominazione = fields.StringField(max_length=80, null=True)
    nome = fields.StringField(max_length=60, null=True)
    cognome = fields.StringField(max_length=60, null=True)
    titolo = fields.StringField(min_length=2, max_length=10, null=True)
    cod_eori = fields.StringField(xmltag="CodEORI", min_length=13, max_length=17, null=True)


class DatiAnagraficiCedentePrestatore(models.Model):
    __xmltag__ = "DatiAnagrafici"
    id_fiscale_iva = IdFiscaleIVA
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)
    anagrafica = Anagrafica
    albo_professionale = fields.StringField(max_length=60, null=True)
    provincia_albo = fields.StringField(length=2, null=True)
    numero_iscrizione_albo = fields.StringField(max_length=60, null=True)
    data_iscrizione_albo = fields.DateField(null=True)
    regime_fiscale = fields.StringField(
            length=4, choices=("RF01", "RF02", "RF04", "RF05", "RF06", "RF07",
                               "RF08", "RF09", "RF10", "RF11", "RF12", "RF13",
                               "RF14", "RF15", "RF16", "RF17", "RF18", "RF19"))


class IndirizzoType(models.Model):
    indirizzo = fields.StringField(max_length=60)
    numero_civico = fields.StringField(max_length=8, null=True)
    cap = fields.StringField(xmltag="CAP", length=5)
    comune = fields.StringField(max_length=60)
    provincia = fields.StringField(length=2, null=True)
    nazione = fields.StringField(length=2)


class Sede(IndirizzoType):
    pass


class IscrizioneREA(models.Model):
    ufficio = fields.StringField(length=2)
    numero_rea = fields.StringField(xmltag="NumeroREA", max_length=20)
    capitale_sociale = fields.StringField(min_length=4, max_length=15, null=True)
    socio_unico = fields.StringField(length=2, choices=("SU", "SM"), null=True)
    stato_liquidazione = fields.StringField(length=2, choices=("LS", "LN"))


class Contatti(models.Model):
    telefono = fields.StringField(min_length=5, max_length=12, null=True)
    fax = fields.StringField(min_length=5, max_length=12, null=True)
    email = fields.StringField(min_length=7, max_length=256, null=True)


class StabileOrganizzazione(IndirizzoType):
    pass


class CedentePrestatore(models.Model):
    dati_anagrafici = DatiAnagraficiCedentePrestatore
    sede = Sede
    stabile_organizzazione = fields.ModelField(StabileOrganizzazione, null=True)
    iscrizione_rea = fields.ModelField(IscrizioneREA, null=True)
    contatti = fields.ModelField(Contatti, null=True)
    riferimento_amministrazione = fields.StringField(max_length=20, null=True)


class DatiAnagraficiCessionarioCommittente(models.Model):
    __xmltag__ = "DatiAnagrafici"
    id_fiscale_iva = fields.ModelField(IdFiscaleIVA, null=True)
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)
    anagrafica = Anagrafica

    def validate_model(self, validation):
        super().validate_model(validation)
        if self.id_fiscale_iva is None and self.codice_fiscale is None:
            validation.add_error(
                    (self._meta["id_fiscale_iva"], self._meta["codice_fiscale"]),
                    "at least one of id_fiscale_iva and codice_fiscale needs to have a value",
                    code="00417")


class RappresentanteFiscale(FullNameMixin, models.Model):
    id_fiscale_iva = fields.ModelField(IdFiscaleIVA, null=True)
    denominazione = fields.StringField(max_length=80, null=True)
    nome = fields.StringField(max_length=60, null=True)
    cognome = fields.StringField(max_length=60, null=True)


class CessionarioCommittente(models.Model):
    dati_anagrafici = DatiAnagraficiCessionarioCommittente
    sede = Sede
    stabile_organizzazione = fields.ModelField(StabileOrganizzazione, null=True)
    rappresentante_fiscale = fields.ModelField(RappresentanteFiscale, null=True)


class DatiAnagraficiRappresentante(models.Model):
    __xmltag__ = "DatiAnagrafici"
    id_fiscale_iva = IdFiscaleIVA
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)
    anagrafica = Anagrafica


class RappresentanteFiscaleCedentePrestatore(models.Model):
    __xmltag__ = "RappresentanteFiscale"
    dati_anagrafici = DatiAnagraficiRappresentante


class DatiAnagraficiTerzoIntermediario(models.Model):
    __xmltag__ = "DatiAnagrafici"
    id_fiscale_iva = IdFiscaleIVA
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)
    anagrafica = Anagrafica


class TerzoIntermediarioOSoggettoEmittente(models.Model):
    dati_anagrafici = DatiAnagraficiTerzoIntermediario


class FatturaElettronicaHeader(models.Model):
    dati_trasmissione = DatiTrasmissione
    cedente_prestatore = CedentePrestatore
    rappresentante_fiscale = models.ModelField(RappresentanteFiscaleCedentePrestatore, null=True)
    cessionario_committente = CessionarioCommittente
    terzo_intermediario_o_soggetto_emittente = models.ModelField(TerzoIntermediarioOSoggettoEmittente, null=True)
    soggetto_emittente = fields.StringField(length=2, choices=("CC", "TZ"), null=True)


class DatiRitenuta(models.Model):
    tipo_ritenuta = fields.StringField(length=4, choices=("RT01", "RT02"))
    importo_ritenuta = fields.DecimalField(max_length=15)
    aliquota_ritenuta = fields.DecimalField(max_length=6)
    causale_pagamento = fields.StringField(max_length=2)


class DatiBollo(models.Model):
    bollo_virtuale = fields.StringField(length=2, choices=("SI",))
    importo_bollo = fields.DecimalField(max_length=15)


class DatiCassaPrevidenziale(models.Model):
    tipo_cassa = fields.StringField(length=4, choices=["TC{:02d}".format(i) for i in range(1, 23)])
    al_cassa = fields.DecimalField(max_length=6)
    importo_contributo_cassa = fields.DecimalField(max_length=15)
    imponibile_cassa = fields.DecimalField(max_length=15)
    aliquota_iva = fields.DecimalField(max_length=6, xmltag="AliquotaIVA")
    ritenuta = fields.StringField(length=2, choices=("SI",), null=True)
    natura = fields.StringField(length=2, choices=("N1", "N2", "N3", "N4", "N5", "N6", "N7"), null=True)
    riferimento_amministrazione = fields.StringField(max_length=20, null=True)

    def validate_model(self, validation):
        super().validate_model(validation)
        if self.aliquota_iva == 0 and self.natura is None:
            validation.add_error(
                self._meta["natura"], "field is empty while aliquota_iva is zero", code="00413")
        if self.aliquota_iva != 0 and self.natura is not None:
            validation.add_error(
                self._meta["natura"], "field has value while aliquota_iva is not zero", code="00414")


class ScontoMaggiorazione(models.Model):
    tipo = fields.StringField(length=2, choices=("SC", "MG"))
    percentuale = fields.DecimalField(max_length=6, null=True)
    importo = fields.DecimalField(max_length=15, null=True)


class DatiGeneraliDocumento(models.Model):
    tipo_documento = fields.StringField(length=4, choices=("TD01", "TD02", "TD03", "TD04", "TD05", "TD06"))
    divisa = fields.StringField()
    data = fields.DateField()
    numero = fields.StringField(max_length=20)
    dati_ritenuta = fields.ModelField(DatiRitenuta, null=True)
    dati_bollo = fields.ModelField(DatiBollo, null=True)
    dati_cassa_previdenziale = fields.ModelListField(DatiCassaPrevidenziale, null=True)
    sconto_maggiorazione = fields.ModelListField(ScontoMaggiorazione, null=True)
    importo_totale_documento = fields.DecimalField(max_length=15, null=True)
    arrotondamento = fields.DecimalField(max_length=15, null=True)
    causale = fields.ListField(fields.StringField(max_length=200), null=True)
    art73 = fields.StringField(length=2, choices=("SI",), null=True, xmltag="Art73")

    def validate_model(self, validation):
        super().validate_model(validation)

        has_dati_cassa_previdenziale_ritenuta = False
        for dcp in self.dati_cassa_previdenziale:
            if dcp.ritenuta == "SI":
                has_dati_cassa_previdenziale_ritenuta = True
                break

        if has_dati_cassa_previdenziale_ritenuta and not self.dati_ritenuta.has_value():
            validation.add_error(
                self._meta["ritenuta"], "field empty when dati_cassa_previdenziale.ritenuta is SI", code="00415")

        if self.numero is None or not re.search(r"\d", self.numero):
            validation.add_error(
                self._meta["numero"], "numero must contain at least one number", code="00425")


class AltriDatiGestionali(models.Model):
    tipo_dato = fields.StringField(max_length=10)
    riferimento_testo = fields.StringField(max_length=60, null=True)
    riferimento_numero = fields.DecimalField(max_length=21, null=True)
    riferimento_data = fields.DateField(null=True)


class CodiceArticolo(models.Model):
    codice_tipo = fields.StringField(max_length=35)
    codice_valore = fields.StringField(max_length=35)


class DettaglioLinee(models.Model):
    numero_linea = fields.IntegerField(max_length=4)
    tipo_cessione_prestazione = fields.StringField(length=2, choices=("SC", "PR", "AB", "AC"), null=True)
    codice_articolo = fields.ModelListField(CodiceArticolo, null=True)
    descrizione = fields.StringField(max_length=1000)
    quantita = fields.DecimalField(max_length=21, decimals=2, null=True)
    unita_misura = fields.StringField(max_length=10, null=True)
    data_inizio_periodo = fields.DateField(null=True)
    data_fine_periodo = fields.DateField(null=True)
    prezzo_unitario = fields.DecimalField(max_length=21)
    sconto_maggiorazione = fields.ModelListField(ScontoMaggiorazione, null=True)
    prezzo_totale = fields.DecimalField(max_length=21)
    aliquota_iva = fields.DecimalField(xmltag="AliquotaIVA", max_length=6)
    ritenuta = fields.StringField(length=2, choices=("SI",), null=True)
    natura = fields.StringField(length=2, null=True, choices=("N1", "N2", "N3", "N4", "N5", "N6", "N7"))
    riferimento_amministrazione = fields.StringField(max_length=20, null=True)
    altri_dati_gestionali = fields.ModelListField(AltriDatiGestionali, null=True)

    def validate_model(self, validation):
        super().validate_model(validation)
        if self.quantita is None and self.unita_misura is not None:
            validation.add_error(self._meta["quantita"], "field must be present when unita_misura is set")
        if self.quantita is not None and self.unita_misura is None:
            validation.add_error(self._meta["unita_misura"], "field must be present when quantita is set")
        if self.aliquota_iva == 0 and self.natura is None:
            validation.add_error(
                self._meta["natura"], "natura non presente a fronte di aliquota_iva pari a zero", code="00400")
        if self.aliquota_iva != 0 and self.natura is not None:
            validation.add_error(
                self._meta["natura"], "natura presente a fronte di aliquota_iva diversa da zero", code="00401")


class DatiRiepilogo(models.Model):
    aliquota_iva = fields.DecimalField(xmltag="AliquotaIVA", max_length=6)
    natura = fields.StringField(length=2, null=True, choices=("N1", "N2", "N3", "N4", "N5", "N6", "N7"))
    spese_accessorie = fields.DecimalField(max_length=15, null=True)
    arrotondamento = fields.DecimalField(max_length=21, null=True)
    # FIXME: Su questo valore il sistema effettua un controllo per verificare
    # la correttezza del calcolo; per i dettagli sull’algoritmo di calcolo si
    # rimanda al file Elenco controlli versione 1.4 presente sul sito
    # www.fatturapa.gov.it.
    imponibile_importo = fields.DecimalField(max_length=15)
    imposta = fields.DecimalField(max_length=15)
    esigibilita_iva = fields.StringField(xmltag="EsigibilitaIVA", length=1, choices=("I", "D", "S"), null=True)
    riferimento_normativo = fields.StringField(max_length=100, null=True)

    def validate_model(self, validation):
        super().validate_model(validation)
        if self.aliquota_iva == 0 and self.natura is None:
            validation.add_error(
                self._meta["natura"], "field is empty while aliquota_iva is zero", code="00429")
        if self.aliquota_iva != 0 and self.natura is not None:
            validation.add_error(
                self._meta["natura"], "field has value while aliquota_iva is not zero", code="00430")


class DatiBeniServizi(models.Model):
    dettaglio_linee = fields.ModelListField(DettaglioLinee)
    dati_riepilogo = fields.ModelListField(DatiRiepilogo)

    def add_dettaglio_linee(self, **kw):
        """
        Convenience method to add entries to dettaglio_linee, autocomputing
        numero_linea and prezzo_totale when missing.

        prezzo_totale is just computed as prezzo_unitario * quantita.

        For anything more complicated, you need to compute prezzo_totale
        yourself add pass it explicitly, or better, extend this function and
        submit a pull request.
        """
        kw.setdefault("numero_linea", len(self.dettaglio_linee) + 1)
        self.dettaglio_linee.append(DettaglioLinee(**kw))

        # Compute prezzo_totale where not set
        for d in self.dettaglio_linee:
            if d.prezzo_totale is not None:
                continue
            if d.quantita is None:
                d.prezzo_totale = d.prezzo_unitario
            else:
                d.prezzo_totale = d.prezzo_unitario * d.quantita

    def build_dati_riepilogo(self):
        """
        Convenience method to compute dati_riepilogo. It replaces existing
        values in dati_riepilogo.

        It only groups dettaglio_linee by aliquota, sums prezzo_totale to
        compute imponibile, and applies IVA.

        For anything more complicated, you need to compute dati_riepilogo
        yourself, or better, extend this function and submit a pull request.
        """
        from collections import defaultdict

        # Group by aliquota
        by_aliquota = defaultdict(list)
        for linea in self.dettaglio_linee:
            by_aliquota[linea.aliquota_iva].append(linea)

        self.dati_riepilogo = []
        for aliquota, linee in sorted(by_aliquota.items()):
            imponibile = sum(l.prezzo_totale for l in linee)
            imposta = imponibile * aliquota / 100
            self.dati_riepilogo.append(
                    DatiRiepilogo(
                        aliquota_iva=aliquota, imponibile_importo=imponibile,
                        imposta=imposta, esigibilita_iva="I"))


class DatiDocumentiCorrelati(models.Model):
    riferimento_numero_linea = fields.ListField(fields.IntegerField(max_length=4), null=True)
    id_documento = fields.StringField(max_length=20)
    data = fields.DateField(null=True)
    num_item = fields.StringField(max_length=20, null=True)
    codice_commessa_convenzione = fields.StringField(max_length=100, null=True)
    codice_cup = fields.StringField(max_length=15, xmltag="CodiceCUP", null=True)
    codice_cig = fields.StringField(max_length=15, xmltag="CodiceCIG", null=True)


class DatiOrdineAcquisto(DatiDocumentiCorrelati):
    pass


class DatiContratto(DatiDocumentiCorrelati):
    pass


class DatiConvenzione(DatiDocumentiCorrelati):
    pass


class DatiRicezione(DatiDocumentiCorrelati):
    pass


class DatiFattureCollegate(DatiDocumentiCorrelati):
    pass


class DatiAnagraficiVettore(models.Model):
    id_fiscale_iva = IdFiscaleIVA
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)
    anagrafica = Anagrafica
    numero_licenza_guida = fields.StringField(max_length=20, null=True)


class IndirizzoResa(IndirizzoType):
    pass


class DatiTrasporto(models.Model):
    dati_anagrafici_vettore = fields.ModelField(DatiAnagraficiVettore, null=True)
    mezzo_trasporto = fields.StringField(max_length=80, null=True)
    causale_trasporto = fields.StringField(max_length=100, null=True)
    numero_colli = fields.IntegerField(max_length=4, null=True)
    descrizione = fields.StringField(max_length=100, null=True)
    unita_misura_peso = fields.StringField(max_length=10, null=True)
    peso_lordo = fields.DecimalField(max_length=7, null=True)
    peso_netto = fields.DecimalField(max_length=7, null=True)
    data_ora_ritiro = fields.DateTimeField(null=True)
    data_inizio_trasporto = fields.DateField(null=True)
    tipo_resa = fields.StringField(length=3, null=True)
    indirizzo_resa = fields.ModelField(IndirizzoResa, null=True)
    data_ora_consegna = fields.DateTimeField(null=True)


class DatiDDT(models.Model):
    __xmltag__ = "DatiDDT"
    numero_ddt = fields.StringField(max_length=20, xmltag="NumeroDDT")
    data_ddt = fields.DateField(xmltag="DataDDT")
    riferimento_numero_linea = fields.ListField(fields.IntegerField(max_length=4), null=True)


class FatturaPrincipale(models.Model):
    numero_fattura_principale = fields.StringField(max_length=20)
    data_fattura_principale = fields.DateField()


class DatiGenerali(models.Model):
    dati_generali_documento = DatiGeneraliDocumento
    dati_ordine_acquisto = fields.ModelListField(DatiOrdineAcquisto, null=True)
    dati_contratto = fields.ModelListField(DatiContratto, null=True)
    dati_convenzione = fields.ModelListField(DatiConvenzione, null=True)
    dati_ricezione = fields.ModelListField(DatiRicezione, null=True)
    dati_fatture_collegate = fields.ModelListField(DatiFattureCollegate, null=True)
    # dati_sal =
    dati_ddt = fields.ModelListField(DatiDDT, null=True)
    dati_trasporto = fields.ModelField(DatiTrasporto, null=True)
    fattura_principale = fields.ModelField(FatturaPrincipale, null=True)

    def validate_model(self, validation):
        super().validate_model(validation)
        dfc_dates = [x.data for x in self.dati_fatture_collegate if x.data is not None]
        if dfc_dates and self.dati_generali_documento.data < min(dfc_dates):
            validation.add_error(
                (self.dati_fatture_collegate._meta["data"],
                 self.dati_generali_documento._meta["data"]),
                "dati_generali_documento.data is earlier than dati_fatture_collegate.data",
                code="00418")


class DettaglioPagamento(models.Model):
    beneficiario = fields.StringField(max_length=200, null=True)
    modalita_pagamento = fields.StringField(length=4, choices=["MP{:02d}".format(i) for i in range(1, 23)])
    data_riferimento_termini_pagamento = fields.DateField(null=True)
    giorni_termini_pagamento = fields.IntegerField(max_length=3, null=True)
    data_scadenza_pagamento = fields.DateField(null=True)
    importo_pagamento = fields.DecimalField(max_length=15)
    cod_ufficio_postale = fields.StringField(max_length=20, null=True)
    cognome_quietanzante = fields.StringField(max_length=60, null=True)
    nome_quietanzante = fields.StringField(max_length=60, null=True)
    cf_quietanzante = fields.StringField(max_length=16, null=True, xmltag="CFQuietanzante")
    titolo_quietanzante = fields.StringField(min_length=2, max_length=10, null=True)
    istituto_finanziario = fields.StringField(max_length=80, null=True)
    iban = fields.StringField(min_length=15, max_length=34, null=True, xmltag="IBAN")
    abi = fields.StringField(length=5, null=True, xmltag="ABI")
    cab = fields.StringField(length=5, null=True, xmltag="CAB")
    bic = fields.StringField(min_length=8, max_length=11, null=True, xmltag="BIC")
    sconto_pagamento_anticipato = fields.DecimalField(max_length=15, null=True)
    data_limite_pagamento_anticipato = fields.DateField(null=True)
    penalita_pagamenti_ritardati = fields.DecimalField(max_length=15, null=True)
    data_decorrenza_penale = fields.DateField(null=True)
    codice_pagamento = fields.StringField(max_length=60, null=True)


class DatiPagamento(models.Model):
    condizioni_pagamento = fields.StringField(length=4, choices=("TP01", "TP02", "TP03"))
    dettaglio_pagamento = fields.ModelListField(DettaglioPagamento)


class Allegati(models.Model):
    nome_attachment = fields.StringField(max_length=60)
    algoritmo_compressione = fields.StringField(max_length=10, null=True)
    formato_attachment = fields.StringField(max_length=10, null=True)
    descrizione_attachment = fields.StringField(max_length=100, null=True)
    attachment = fields.Base64BinaryField()


class DatiVeicoli(models.Model):
    data = fields.DateField()
    totale_percorso = fields.StringField(max_length=15)


class FatturaElettronicaBody(models.Model):
    dati_generali = DatiGenerali
    dati_beni_servizi = DatiBeniServizi
    dati_veicoli = models.ModelField(DatiVeicoli, null=True)
    dati_pagamento = fields.ModelListField(DatiPagamento, null=True)
    allegati = fields.ModelListField(Allegati, null=True)

    def build_importo_totale_documento(self):
        """
        Convenience method to compute
        dati_generali.dati_generali_documento.importo_totale_documento.
        It replaces an existing value in importo_totale_documento.

        It only adds imponibile_importo and imposta values from
        dati_beni_servizi.dati_riepilogo.

        For anything more complicated, you need to compute
        importo_totale_documento yourself, or better, extend this function and
        submit a pull request.
        """
        totale = sum(r.imponibile_importo + r.imposta for r in self.dati_beni_servizi.dati_riepilogo)
        self.dati_generali.dati_generali_documento.importo_totale_documento = totale

    def validate_model(self, validation):
        super().validate_model(validation)

        has_ritenute = False
        has_aliquote_iva = False
        for dl in self.dati_beni_servizi.dettaglio_linee:
            if dl.ritenuta == "SI":
                has_ritenute = True
            if dl.aliquota_iva is not None:
                has_aliquote_iva = True

        if has_ritenute and not self.dati_generali.dati_generali_documento.dati_ritenuta.has_value():
            validation.add_error(
                self.dati_generali.dati_generali_documento._meta["dati_ritenuta"],
                "field empty while at least one of dati_beni_servizi.dettaglio_linee.ritenuta is SI",
                code="00411",
            )

        for dcp in self.dati_generali.dati_generali_documento.dati_cassa_previdenziale:
            if dcp.aliquota_iva is not None:
                has_aliquote_iva = True

        if not self.dati_beni_servizi.dati_riepilogo and has_aliquote_iva:
            validation.add_error(
                    self.dati_beni_servizi._meta["dati_riepilogo"],
                    "dati_riepilogo is empty while there is at least an aliquota_iva"
                    " in dettaglio_linee or dati_cassa_previdenziale",
                    code="00419")


class Fattura(models.Model):
    __xmlns__ = NS
    __xmltag__ = "FatturaElettronica"

    fattura_elettronica_header = FatturaElettronicaHeader
    fattura_elettronica_body = fields.ModelListField(FatturaElettronicaBody, min_num=1)
    signature = fields.NotImplementedField(null=True, xmlns=NS_SIG)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.fattura_elettronica_header.dati_trasmissione.formato_trasmissione = self.get_versione()

    def get_versione(self):
        return None

    def get_xmlattrs(self):
        return {"versione": self.get_versione()}

    def validate_model(self, validation):
        super().validate_model(validation)
        if self.get_versione() != self.fattura_elettronica_header.dati_trasmissione.formato_trasmissione:
            validation.add_error(
                    self.fattura_elettronica_header.dati_trasmissione._meta["formato_trasmissione"],
                    "formato_trasmissione should be {}".format(self.get_versione()),
                    code="00428")

    def to_xml(self, builder):
        with builder.element(self.get_xmltag(), **self.get_xmlattrs()) as b:
            with b.override_default_namespace(None) as b1:
                for name, field in self._meta.items():
                    field.to_xml(b1, getattr(self, name))

    def build_etree(self, lxml=False):
        """
        Build and return an ElementTree with the fattura in XML format
        """
        self.fattura_elettronica_header.dati_trasmissione.formato_trasmissione = self.get_versione()
        if lxml:
            from a38.builder import LXMLBuilder
            builder = LXMLBuilder()
        else:
            from a38.builder import Builder
            builder = Builder()
        builder.default_namespace = NS
        self.to_xml(builder)
        return builder.get_tree()

    def from_etree(self, el):
        versione = el.attrib.get("versione", None)
        if versione is None:
            raise RuntimeError("root element {} misses attribute 'versione'".format(el.tag))

        if versione != self.get_versione():
            raise RuntimeError("root element versione is {} instead of {}".format(versione, self.get_versione()))

        return super().from_etree(el)


class FatturaPrivati12(Fattura):
    """
    Fattura privati 1.2
    """
    def get_versione(self):
        return "FPR12"


class FatturaPA12(Fattura):
    """
    Fattura PA 1.2
    """
    def get_versione(self):
        return "FPA12"


def auto_from_etree(root):
    from .fattura_semplificata import NS10, FatturaElettronicaSemplificata
    tagname_ordinaria = "{{{}}}FatturaElettronica".format(NS)
    tagname_semplificata = "{{{}}}FatturaElettronicaSemplificata".format(NS10)

    versione = root.attrib.get("versione", None)

    if root.tag == tagname_ordinaria:
        if versione is None:
            raise RuntimeError("root element {} misses attribute 'versione'".format(root.tag))
        if versione == "FPR12":
            res = FatturaPrivati12()
        elif versione == "FPA12":
            res = FatturaPA12()
        else:
            raise RuntimeError("unsupported versione {}".format(versione))
    elif root.tag == tagname_semplificata:
        if versione is None:
            raise RuntimeError("root element {} misses attribute 'versione'".format(root.tag))
        if versione == "FSM10":
            res = FatturaElettronicaSemplificata()
        else:
            raise RuntimeError("unsupported versione {}".format(versione))
    else:
        raise RuntimeError("Root element {} is neither {} nor {}".format(
            root.tag, tagname_ordinaria, tagname_semplificata))

    res.from_etree(root)
    return res
