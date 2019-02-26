from . import models
from . import fields
import xml.etree.ElementTree as ET

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


def load_url(url):
    import requests
    res = requests.get(url)
    res.raise_for_status()
    root = ET.fromstring(res.content)
    return auto_from_etree(root)
