from .fattura import (
    IdTrasmittente, IdFiscaleIVA, Sede, StabileOrganizzazione, IscrizioneREA,
    FullNameMixin, Allegati
)
from . import models
from . import fields

NS10 = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.0"


class DatiTrasmissione(models.Model):
    id_trasmittente = IdTrasmittente
    progressivo_invio = fields.ProgressivoInvioField()
    formato_trasmissione = fields.StringField(length=5, choices=("FSM10",))
    codice_destinatario = fields.StringField(null=True, min_length=6, max_length=7, default="0000000")
    pec_destinatario = fields.StringField(null=True, min_length=8, max_length=256, xmltag="PECDestinatario")


class RappresentanteFiscale(FullNameMixin, models.Model):
    id_fiscale_iva = IdFiscaleIVA
    denominazione = fields.StringField(max_length=80, null=True)
    nome = fields.StringField(max_length=60, null=True)
    cognome = fields.StringField(max_length=60, null=True)


class CedentePrestatore(FullNameMixin, models.Model):
    id_fiscale_iva = IdFiscaleIVA
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)
    denominazione = fields.StringField(max_length=80, null=True)
    nome = fields.StringField(max_length=60, null=True)
    cognome = fields.StringField(max_length=60, null=True)
    sede = Sede
    stabile_organizzazione = fields.ModelField(StabileOrganizzazione, null=True)
    rappresentante_fiscale = models.ModelField(RappresentanteFiscale, null=True)
    iscrizione_rea = fields.ModelField(IscrizioneREA, null=True)
    regime_fiscale = fields.StringField(
            length=4, choices=("RF01", "RF02", "RF04", "RF05", "RF06", "RF07",
                               "RF08", "RF09", "RF10", "RF11", "RF12", "RF13",
                               "RF14", "RF15", "RF16", "RF17", "RF18", "RF19"))


class IdentificativiFiscali(models.Model):
    id_fiscale_iva = IdFiscaleIVA
    codice_fiscale = fields.StringField(min_length=11, max_length=16, null=True)


class AltriDatiIdentificativi(FullNameMixin, models.Model):
    denominazione = fields.StringField(max_length=80, null=True)
    nome = fields.StringField(max_length=60, null=True)
    cognome = fields.StringField(max_length=60, null=True)
    sede = Sede
    stabile_organizzazione = fields.ModelField(StabileOrganizzazione, null=True)
    rappresentante_fiscale = models.ModelField(RappresentanteFiscale, null=True)


class CessionarioCommittente(models.Model):
    identificativi_fiscali = IdentificativiFiscali
    altri_dati_identificativi = AltriDatiIdentificativi


class FatturaElettronicaHeader(models.Model):
    dati_trasmissione = DatiTrasmissione
    cedente_prestatore = CedentePrestatore
    cessionario_committente = CessionarioCommittente
    soggetto_emittente = fields.StringField(length=2, choices=("CC", "TZ"), null=True)


class DatiGeneraliDocumento(models.Model):
    tipo_documento = fields.StringField(length=4, choices=("TD07", "TD08", "TD09"))
    divisa = fields.StringField()
    data = fields.DateField()
    numero = fields.StringField(max_length=20)


class DatiFatturaRettificata(models.Model):
    numero_fr = fields.StringField(max_length=20, xmltag="NumeroFR")
    data_fr = fields.DateField(xmltag="DataFR")
    elementi_rettificati = fields.StringField(max_length=1000)


class DatiGenerali(models.Model):
    dati_generali_documento = DatiGeneraliDocumento
    dati_fattura_rettificata = fields.ModelField(DatiFatturaRettificata, null=True)


class DatiIVA(models.Model):
    imposta = fields.DecimalField(max_length=15)
    aliquota = fields.DecimalField(max_length=6)


class DatiBeniServizi(models.Model):
    descrizione = fields.StringField(max_length=1000)
    importo = fields.DecimalField(max_length=15)
    dati_iva = DatiIVA
    natura = fields.StringField(length=2, null=True, choices=("N1", "N2", "N3", "N4", "N5", "N6", "N7"))
    riferimento_normativo = fields.StringField(max_length=100, null=True)


class FatturaElettronicaBody(models.Model):
    dati_generali = DatiGenerali
    dati_beni_servizi = fields.ModelListField(DatiBeniServizi)
    allegati = fields.ModelListField(Allegati, null=True)


class FatturaElettronicaSemplificata(models.Model):
    """
    Fattura elettronica semplificata
    """
    __xmlns__ = NS10
    fattura_elettronica_header = FatturaElettronicaHeader
    fattura_elettronica_body = fields.ModelListField(FatturaElettronicaBody, min_num=1)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.fattura_elettronica_header.dati_trasmissione.formato_trasmissione = self.get_versione()

    def get_versione(self):
        return "FSM10"

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
        builder.default_namespace = NS10
        self.to_xml(builder)
        return builder.get_tree()

    def from_etree(self, el):
        versione = el.attrib.get("versione", None)
        if versione is None:
            raise RuntimeError("root element {} misses attribute 'versione'".format(el.tag))

        if versione != self.get_versione():
            raise RuntimeError("root element versione is {} instead of {}".format(versione, self.get_versione()))

        return super().from_etree(el)
