from typing import Dict
import re
from collections import defaultdict
import xml.etree.ElementTree as ET
import logging
import base64
import subprocess
from pathlib import Path
from . import models
from . import fields

log = logging.getLogger("__name__")

NS = "http://uri.etsi.org/02231/v2#"
NS_XMLDSIG = "http://www.w3.org/2000/09/xmldsig#"
NS_ADDTYPES = "http://uri.etsi.org/02231/v2/additionaltypes#"


class OtherInformation(models.Model):
    __xmlns__ = NS
    tsl_type = fields.NotImplementedField(xmltag="TSLType", xmlns=NS)
    scheme_territory = fields.StringField(null=True, xmlns=NS)
    mime_type = fields.StringField(null=True, xmlns=NS_ADDTYPES)
    scheme_operator_name = fields.NotImplementedField(xmlns=NS)
    scheme_type_community_rules = fields.NotImplementedField(xmlns=NS)


class AdditionalInformation(models.Model):
    __xmlns__ = NS
    other_information = fields.ModelListField(OtherInformation)


class OtherTSLPointer(models.Model):
    __xmlns__ = NS
    tsl_location = fields.StringField(xmltag="TSLLocation", xmlns=NS)
    service_digital_identities = fields.NotImplementedField(xmlns=NS)
    additional_information = AdditionalInformation


class PointersToOtherTSL(models.Model):
    __xmlns__ = NS
    other_tsl_pointer = fields.ModelListField(OtherTSLPointer)


class SchemeInformation(models.Model):
    __xmlns__ = NS
    pointers_to_other_tsl = fields.ModelField(PointersToOtherTSL)
    tsl_version_identifier = fields.NotImplementedField(xmltag="TSLVersionIdentifier", xmlns=NS)
    tsl_sequence_number = fields.NotImplementedField(xmltag="TSLSequenceNumber", xmlns=NS)
    tsl_type = fields.NotImplementedField(xmltag="TSLType", xmlns=NS)
    scheme_operator_name = fields.NotImplementedField(xmlns=NS)
    scheme_operator_address = fields.NotImplementedField(xmlns=NS)
    scheme_information_uri = fields.NotImplementedField(xmltag="SchemeInformationURI", xmlns=NS)
    scheme_name = fields.NotImplementedField(xmlns=NS)
    status_determination_approach = fields.NotImplementedField(xmlns=NS)
    scheme_type_community_rules = fields.NotImplementedField(xmlns=NS)
    scheme_territory = fields.NotImplementedField(xmlns=NS)
    policy_or_legal_notice = fields.NotImplementedField(xmlns=NS)
    historical_information_period = fields.NotImplementedField(xmlns=NS)
    list_issue_date_time = fields.NotImplementedField(xmlns=NS)
    next_update = fields.NotImplementedField(xmlns=NS)
    distribution_points = fields.NotImplementedField(xmlns=NS)


class TSPInformation(models.Model):
    __xmlns__ = NS
    tsp_name = fields.NotImplementedField(xmltag="TSPName", xmlns=NS)
    tsp_trade_name = fields.NotImplementedField(xmltag="TSPTradeName", xmlns=NS)
    tsp_address = fields.NotImplementedField(xmltag="TSPAddress", xmlns=NS)
    tsp_information_url = fields.NotImplementedField(xmltag="TSPInformationURI", xmlns=NS)


class DigitalId(models.Model):
    __xmlns__ = NS
    x509_subject_name = fields.StringField(xmltag="X509SubjectName", xmlns=NS, null=True)
    x509_ski = fields.StringField(xmltag="X509SKI", xmlns=NS, null=True)
    x509_certificate = fields.StringField(xmltag="X509Certificate", xmlns=NS, null=True)


class ServiceDigitalIdentity(models.Model):
    __xmlns__ = NS
    digital_id = fields.ModelListField(DigitalId)


class ServiceInformation(models.Model):
    __xmlns__ = NS
    service_type_identifier = fields.StringField(xmlns=NS)
    service_name = fields.NotImplementedField(xmlns=NS)
    service_digital_identity = ServiceDigitalIdentity
    service_status = fields.StringField(xmlns=NS)
    status_starting_time = fields.NotImplementedField(xmlns=NS)
    service_information_extensions = fields.NotImplementedField(xmlns=NS)


class TSPService(models.Model):
    __xmlns__ = NS
    service_information = ServiceInformation
    service_history = fields.NotImplementedField(xmlns=NS)


class TSPServices(models.Model):
    __xmlns__ = NS
    tsp_service = fields.ModelListField(TSPService)


class TrustServiceProvider(models.Model):
    __xmlns__ = NS
    tsp_information = TSPInformation
    tsp_services = TSPServices


class TrustServiceProviderList(models.Model):
    __xmlns__ = NS
    trust_service_provider = fields.ModelListField(TrustServiceProvider)


class TrustServiceStatusList(models.Model):
    __xmlns__ = NS
    scheme_information = SchemeInformation
    signature = fields.NotImplementedField(xmlns=NS_XMLDSIG)
    trust_service_provider_list = TrustServiceProviderList

    def get_tsl_pointer_by_territory(self, territory):
        for other_tsl_pointer in self.scheme_information.pointers_to_other_tsl.other_tsl_pointer:
            territory = None
            for oi in other_tsl_pointer.additional_information.other_information:
                if oi.scheme_territory is not None:
                    territory = oi.scheme_territory
                    break
            if territory != "IT":
                continue
            return other_tsl_pointer.tsl_location


def auto_from_etree(root):
    expected_tag = "{{{}}}TrustServiceStatusList".format(NS)
    if root.tag != expected_tag:
        raise RuntimeError("Root element {} is not {}".format(root.tag, expected_tag))

    res = TrustServiceStatusList()
    res.from_etree(root)
    return res


def load_url(url: str):
    """
    Return a TrustedServiceStatusList instance from the XML downloaded from the
    given URL
    """
    import requests
    res = requests.get(url)
    res.raise_for_status()
    root = ET.fromstring(res.content)
    return auto_from_etree(root)


def load_certs() -> Dict[str, "cryptography.x509.Certificate"]:
    """
    Download trusted list certificates for Italy, parse them and return a dict
    mapping certificate names good for use as file names to cryptography.x509
    certificates
    """
    re_clean_fname = re.compile(r"[^A-Za-z0-9_-]")

    eu_url = "https://ec.europa.eu/information_society/policy/esignature/trusted-list/tl-mp.xml"
    log.info("Downloading EU index from %s", eu_url)
    eu_tl = load_url(eu_url)
    it_url = eu_tl.get_tsl_pointer_by_territory("IT")
    log.info("Downloading IT data from %s", it_url)
    trust_service_status_list = load_url(it_url)

    by_name = defaultdict(list)
    for tsp in trust_service_status_list.trust_service_provider_list.trust_service_provider:
        for tsp_service in tsp.tsp_services.tsp_service:
            si = tsp_service.service_information
            if si.service_status not in (
                    "http://uri.etsi.org/TrstSvc/TrustedList/Svcstatus/recognisedatnationallevel",
                    "http://uri.etsi.org/TrstSvc/TrustedList/Svcstatus/granted"):
                continue
            if si.service_type_identifier not in (
                    "http://uri.etsi.org/TrstSvc/Svctype/CA/QC",):
                continue
            # print("identifier", si.service_type_identifier)
            # print("status", si.service_status)
            cert = []
            sn = []
            for di in si.service_digital_identity.digital_id:
                if di.x509_subject_name is not None:
                    sn.append(di.x509_subject_name)
                # if di.x509_ski is not None:
                #    print("  SKI:", di.x509_ski)
                if di.x509_certificate is not None:
                    from cryptography import x509
                    from cryptography.hazmat.backends import default_backend
                    der = base64.b64decode(di.x509_certificate)
                    cert.append(x509.load_der_x509_certificate(der, default_backend()))

            if len(cert) == 0:
                raise RuntimeError("{} has no certificates".format(sn))
            elif len(cert) > 1:
                raise RuntimeError("{} has {} certificates".format(sn, len(cert)))
            else:
                from cryptography.x509.oid import NameOID
                cert = cert[0]
                cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                # print("sn", sn)
                # print(cert)
                # print("full cn", cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME))
                # print("cn", cn)
                fname = re_clean_fname.sub("_", cn)
                by_name[fname].append(cert)

    res = {}
    for name, certs in by_name.items():
        if len(certs) == 1:
            if name in res:
                raise RuntimeError("{} already in result".format(name))
            res[name] = certs[0]
        else:
            for idx, cert in enumerate(certs, start=1):
                idxname = name + "_a38_{}".format(idx)
                if idxname in res:
                    raise RuntimeError("{} already in result".format(name))
                res[idxname] = cert
    return res


def update_capath(destdir: Path, remove_old=False):
    from cryptography.hazmat.primitives import serialization
    certs = load_certs()
    if destdir.is_dir():
        current = set(c.name for c in destdir.iterdir() if c.name.endswith(".crt"))
    else:
        current = set()
        destdir.mkdir(parents=True)
    for name, cert in certs.items():
        fname = name + ".crt"
        current.discard(fname)
        pathname = destdir / fname
        with pathname.open(mode="wb") as fd:
            fd.write(cert.public_bytes(serialization.Encoding.PEM))
            log.info("%s: written", pathname)
    if remove_old:
        for fname in current:
            pathname = destdir / fname
            pathname.unlink()
            log.info("%s: removed", pathname)

    subprocess.run(["openssl", "rehash", destdir], check=True)
