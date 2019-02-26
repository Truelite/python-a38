from unittest import TestCase
import tempfile
from contextlib import contextmanager
import os
from a38.crypto import P7M, InvalidSignatureError, SignerCertificateError

CA_CERT = """
-----BEGIN CERTIFICATE-----
MIIFJjCCBA6gAwIBAgIBATANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMCSVQx
FTATBgNVBAoMDElORk9DRVJUIFNQQTEiMCAGA1UECwwZQ2VydGlmaWNhdG9yZSBB
Y2NyZWRpdGF0bzEUMBIGA1UEBRMLMDc5NDUyMTEwMDYxJTAjBgNVBAMMHEluZm9D
ZXJ0IEZpcm1hIFF1YWxpZmljYXRhIDIwHhcNMTMwNDE5MTQyNjE1WhcNMjkwNDE5
MTUyNjE1WjCBhTELMAkGA1UEBhMCSVQxFTATBgNVBAoMDElORk9DRVJUIFNQQTEi
MCAGA1UECwwZQ2VydGlmaWNhdG9yZSBBY2NyZWRpdGF0bzEUMBIGA1UEBRMLMDc5
NDUyMTEwMDYxJTAjBgNVBAMMHEluZm9DZXJ0IEZpcm1hIFF1YWxpZmljYXRhIDIw
ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDFoW5eA0k3AcU+/v2uKclE
hGrxXlqOUptAQJLSjysP7IaKKtGxIeX8HNavxRaDkLkQNElql+t4GgIPyJk4lzHb
H72c1Ls2SH06X7uCo5iGRH3+FU1ScbcrzviAPB+yeqUZ1cKkGyyGQ1wBsorxpREU
eajkW2wsDiY/DYyeTG1I3ECOk/2sZW1U/xGWeVIlNCg9lkqrjvwu6swKVg3LPRiD
L4Cqzsh4w9VZzJeDvKfer6lp/fRRduY5fSajtttgCoERrw0hZH/PkkmDCcnbLSjx
59Knu3jHip5prgGVU29MKANf573VZAAZfau/lAxf1K91DEXxtPWknEUULt3beGef
AgMBAAGjggGdMIIBmTAPBgNVHRMBAf8EBTADAQH/MFgGA1UdIARRME8wTQYEVR0g
ADBFMEMGCCsGAQUFBwIBFjdodHRwOi8vd3d3LmZpcm1hLmluZm9jZXJ0Lml0L2Rv
Y3VtZW50YXppb25lL21hbnVhbGkucGhwMCUGA1UdEgQeMByBGmZpcm1hLmRpZ2l0
YWxlQGluZm9jZXJ0Lml0MIHVBgNVHR8Egc0wgcowgceggcSggcGGKmh0dHA6Ly9j
cmwuaW5mb2NlcnQuaXQvY3Jscy9maXJtYTIvQVJMLmNybIaBkmxkYXA6Ly9sZGFw
LmluZm9jZXJ0Lml0L2NuJTNESW5mb0NlcnQlMjBGaXJtYSUyMFF1YWxpZmljYXRh
JTIwMixvdSUzRENlcnRpZmljYXRvcmUlMjBBY2NyZWRpdGF0byxvJTNESU5GT0NF
UlQlMjBTUEEsYyUzRElUP2F1dGhvcml0eVJldm9jYXRpb25MaXN0MA4GA1UdDwEB
/wQEAwIBBjAdBgNVHQ4EFgQUk90h/APQFQpyraPM1ZoJnTiLnekwDQYJKoZIhvcN
AQELBQADggEBAJYdIAO8JCHr9dTT/kpy5AZpgo8XoIQW/q9tNQPwZkdd/bAfgLib
olvbk7ZTsiVlVv35Bb9rhM58SKP1Xa9c26Cf8y4zhoplVbhfKRGVCLj1u1EXdPhC
UQb8WWcM0AyLOXj3qhbMh77UL0K9eaRrwTAENbl43Jy65HPHubNnk9U9wIUUtLgR
Hl5Oog1ZUSV5oLEkeSwzHyk5ZQnv24BzU9UXJ/amAt2ff1Krr3/PsY4Juwgtpg1N
qq8tid5L+lN7qJ8xXfxMuUX2aWkWftCBL8H75U7NnYm/Zx6XyRaULFzCDw0RBSHa
WGPH+t5X7ZMMERXn8Z/2LTYWuj9w1+WeieY=
-----END CERTIFICATE-----
"""

CA_CERT_HASH = "af603d58.0"


class TestAnagrafica(TestCase):
    @contextmanager
    def capath(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, CA_CERT_HASH), "wt") as fd:
                fd.write(CA_CERT)
            yield td

    def test_load(self):
        p7m = P7M("tests/data/test.txt.p7m")
        data = p7m.get_payload()
        self.assertEqual(
                data,
                "This is only a test payload.\n"
                "\n"
                "Questo è solo un payload di test.\n".encode("utf8"))

    def test_verify(self):
        p7m = P7M("tests/data/test.txt.p7m")
        with self.capath() as capath:
            p7m.verify_signature(capath)

    def test_verify_corrupted_random(self):
        p7m = P7M("tests/data/test.txt.p7m")
        data_mid = len(p7m.data) // 2
        p7m.data = p7m.data[:data_mid] + bytes([p7m.data[data_mid] + 1]) + p7m.data[data_mid + 1:]
        with self.capath() as capath:
            with self.assertRaises(InvalidSignatureError):
                p7m.verify_signature(capath)

    def test_verify_corrupted_payload(self):
        p7m = P7M("tests/data/test.txt.p7m")
        signed_data = p7m.get_signed_data()
        encap_content_info = signed_data["encap_content_info"]
        encap_content_info["content"] = b"All your base are belong to us"
        p7m.data = p7m.content_info.dump()
        with self.capath() as capath:
            with self.assertRaisesRegexp(InvalidSignatureError, r"routines:CMS_verify:content verify error"):
                p7m.verify_signature(capath)

    def test_verify_noca(self):
        p7m = P7M("tests/data/test.txt.p7m")
        with tempfile.TemporaryDirectory() as capath:
            with self.assertRaisesRegexp(InvalidSignatureError, r"Verify error:unable to get local issuer certificate"):
                p7m.verify_signature(capath)
