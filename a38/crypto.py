from typing import Union, BinaryIO
from asn1crypto.cms import ContentInfo
import io
import base64
import binascii
import subprocess
import xml.etree.ElementTree as ET
from . import fattura as a38


class SignatureVerificationError(Exception):
    pass


class InvalidSignatureError(SignatureVerificationError):
    pass


class SignerCertificateError(SignatureVerificationError):
    pass


class P7M:
    """
    Parse a Fattura Elettronica encoded as a .p7m file
    """
    def __init__(self, data: Union[str, bytes, BinaryIO]):
        """
        If data is a string, it is taken as a file name.

        If data is bytes, it is taken as p7m data.

        Otherwise, data is taken as a file-like object that reads bytes data.
        """
        if isinstance(data, str):
            with open(data, "rb") as fd:
                self.data = fd.read()
        elif isinstance(data, bytes):
            self.data = data
        else:
            self.data = data.read()

        # Data might potentially be base64 encoded

        try:
            self.data = base64.b64decode(self.data, validate=True)
        except binascii.Error:
            pass

        self.content_info = ContentInfo.load(self.data)

    def get_signed_data(self):
        """
        Return the SignedData part of the P7M file
        """
        if self.content_info["content_type"].native != "signed_data":
            raise RuntimeError("p7m data is not an instance of signed_data")

        signed_data = self.content_info["content"]
        if signed_data["version"].native != "v1":
            raise RuntimeError(f"ContentInfo/SignedData.version is {signed_data['version'].native} instead of v1")

        return signed_data

    def get_payload(self):
        """
        Return the raw signed data
        """
        signed_data = self.get_signed_data()
        encap_content_info = signed_data["encap_content_info"]
        return encap_content_info["content"].native

    def get_fattura(self):
        """
        Return the parsed XML data
        """
        data = io.BytesIO(self.get_payload())
        tree = ET.parse(data)
        return a38.auto_from_etree(tree.getroot())

    def verify_signature(self, certdir):
        """
        Verify the signature on the file
        """
        res = subprocess.run([
            "openssl", "cms", "-verify", "-inform", "DER", "-CApath", certdir, "-noout"],
            input=self.data,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE)

        # From openssl cms manpage:
        # 0   The operation was completely successfully.
        # 1   An error occurred parsing the command options.
        # 2   One of the input files could not be read.
        # 3   An error occurred creating the CMS file or when reading the MIME message.
        # 4   An error occurred decrypting or verifying the message.
        # 5   The message was verified correctly but an error occurred writing out the signers certificates.

        if res.returncode == 0:
            pass
        elif res.returncode == 4:
            raise InvalidSignatureError(res.stderr)
        elif res.returncode == 5:
            raise SignerCertificateError(res.stderr)
        else:
            raise RuntimeError(res.stderr)
