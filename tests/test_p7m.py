import os
import tempfile
from contextlib import contextmanager
from unittest import TestCase

from a38.crypto import P7M, InvalidSignatureError

# This is the CA certificate used to validate tests/data/test.txt.p7m
#
# The signature on the test file will expire (next expiration date: May  6 23:59:59 2024 GMT)
#
# To refresh it:
#
# 1. Sign tests/data/test.txt with a CAdES envelope
# 2. Extract the signature:
#      openssl smime -verify -in tests/data/test.txt.p7m -inform der -noverify -signer /tmp/cert.pem -out /dev/null
# 3. Get signature information:
#      openssl x509 -inform pem -in /tmp/cert.pem -text
# 4. Compute the issuer hash to find the CA certificate:
#      openssl x509 -inform pem -in /tmp/cert.pem -issuer_hash
# 5. Download/refresh the CA certificate database:
#      ./a38tool update_capath certs
# 6. Find the file named with the issuer hash in certs/
# 7. Update the CA_CERT_HASH variable below with the name of the file you just
#    found in certs/
# 8. Replace the value of CA_CERT with its contents
#
CA_CERT = """
-----BEGIN CERTIFICATE-----
MIIE+jCCA+KgAwIBAgIQbK2AXjA4PMWG8x+rL26V9zANBgkqhkiG9w0BAQsFADBs
MQswCQYDVQQGEwJJVDEYMBYGA1UECgwPQXJ1YmFQRUMgUy5wLkEuMSEwHwYDVQQL
DBhDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eUMxIDAeBgNVBAMMF0FydWJhUEVDIFMu
cC5BLiBORyBDQSAzMB4XDTEwMTAyMjAwMDAwMFoXDTMwMTAyMjIzNTk1OVowbDEL
MAkGA1UEBhMCSVQxGDAWBgNVBAoMD0FydWJhUEVDIFMucC5BLjEhMB8GA1UECwwY
Q2VydGlmaWNhdGlvbiBBdXRob3JpdHlDMSAwHgYDVQQDDBdBcnViYVBFQyBTLnAu
QS4gTkcgQ0EgMzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKtkY4EH
G+Nh4VYLL4R5tvmX6J+AYlL2BPDUCLN92+zi9QMbsh84zbRE+om9KE8P67mST2my
bhGTz6dzeK1BrQfSdKJ8AGxePzqUq+uGHGULoy4A6ey4EyqTfxY+pGzjB7OVcuiw
y7iV6k1YjshIsmNjTmYOAQepZMgBmxHPnR6IW9MsAOFBBQH/vJFQDeBts/rA6lbM
/VsURwzr6XOqCzwJK/csKvuE/rAaRKY+IPzah8mou//yEi4V401J1JYfPanbCJOW
nIty9HaioUe5Fu2jw4UP7T5Cbw4lND1sP7HVhsVRDuTj3gF9ulJ7EBmcR/2THDZC
ozD76uwuTmkm4VsCAwEAAaOCAZYwggGSMD8GCCsGAQUFBwEBBDMwMTAvBggrBgEF
BQcwAYYjaHR0cDovL29jc3AuYXJ1YmFwZWMudHJ1c3RpdGFsaWEuaXQwEgYDVR0T
AQH/BAgwBgEB/wIBADBGBgNVHSAEPzA9MDsGCisGAQQBgegtAQEwLTArBggrBgEF
BQcCARYfaHR0cHM6Ly9jYS5hcnViYXBlYy5pdC9jcHMuaHRtbDBqBgNVHR8EYzBh
MF+gXaBbhllodHRwOi8vb25zaXRlY3JsLmFydWJhcGVjLnRydXN0aXRhbGlhLml0
L0FydWJhUEVDU3BBQ2VydGlmaWNhdGlvbkF1dGhvcml0eUMvTGF0ZXN0Q1JMLmNy
bDArBgNVHRIEJDAipCAwHjEcMBoGA1UEAxMTR09WVlNQLUMxLTIwNDgtMS0xMDAO
BgNVHQ8BAf8EBAMCAQYwKwYDVR0RBCQwIqQgMB4xHDAaBgNVBAMTE0dPVlZTUC1D
MS0yMDQ4LTEtMTAwHQYDVR0OBBYEFPDARbG2NbTqXyn6gwNK3C/1s33oMA0GCSqG
SIb3DQEBCwUAA4IBAQBRGwGypquxMawPV6ZN5l/2eJdaaqgnYolin1PGXJUFRQy3
k5FK0Fwk/90U/j/ue83cYdsRpPVpo17LOk7hCNSFk/W2SRVGvqaM77/cVpgFwm25
Ab2x5sMxwJ9Uoouba00CDl2SiYgn9KN+Bd3LHrwtpO8IkzwSE7k0kKmDLdCZTyUO
ZPR8RKpwedjLJoiyXCtq9PKA3avI1R6N8yOxbK954+nSOsHfmGDP4wQi8PUJIWBm
dlpHNM669BLdLwj6lpCjNI6AuP4K5Jw1qkOmcccnVWxkk0r2qNu87AlVosHpKf6G
jkJbJNWfBsgjRHGg6Pq3enAf8/7DfkoCyKUzI8zZ
-----END CERTIFICATE-----
"""

CA_CERT_HASH = "b72ed47c.0"


class TestSignature(TestCase):
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
        if p7m.is_expired():
            self.skipTest("test signature has expired and needs to be regenerated")
        with self.capath() as capath:
            p7m.verify_signature(capath)

    def test_verify_corrupted_random(self):
        p7m = P7M("tests/data/test.txt.p7m")
        if p7m.is_expired():
            self.skipTest("test signature has expired and needs to be regenerated")
        data_mid = len(p7m.data) // 2
        p7m.data = p7m.data[:data_mid] + bytes([p7m.data[data_mid] + 1]) + p7m.data[data_mid + 1:]
        with self.capath() as capath:
            with self.assertRaises(InvalidSignatureError):
                p7m.verify_signature(capath)

    def test_verify_corrupted_payload(self):
        p7m = P7M("tests/data/test.txt.p7m")
        if p7m.is_expired():
            self.skipTest("test signature has expired and needs to be regenerated")
        signed_data = p7m.get_signed_data()
        encap_content_info = signed_data["encap_content_info"]
        encap_content_info["content"] = b"All your base are belong to us"
        p7m.data = p7m.content_info.dump()
        with self.capath() as capath:
            with self.assertRaisesRegex(InvalidSignatureError, r"routines:CMS_verify:content verify error"):
                p7m.verify_signature(capath)

    def test_verify_noca(self):
        p7m = P7M("tests/data/test.txt.p7m")
        if p7m.is_expired():
            self.skipTest("test signature has expired and needs to be regenerated")
        with tempfile.TemporaryDirectory() as capath:
            with self.assertRaisesRegex(
                    InvalidSignatureError, r"Verify error:\s*unable to get local issuer certificate"):
                p7m.verify_signature(capath)
