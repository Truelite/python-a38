from typing import Union, BinaryIO
from asn1crypto.cms import ContentInfo
import io
import base64
import binascii
import xml.etree.ElementTree as ET
from . import fattura as a38


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

    def get_payload(self):
        """
        Return the raw XML data
        """
        if self.content_info["content_type"].native != "signed_data":
            raise RuntimeError("p7m data is not an instance of signed_data")

        signed_data = self.content_info["content"]
        if signed_data["version"].native != "v1":
            raise RuntimeError(f"ContentInfo/SignedData.version is {signed_data['version'].native} instead of v1")

        encap_content_info = signed_data["encap_content_info"]
        return encap_content_info["content"].native

    def get_fattura(self):
        """
        Return the parsed XML data
        """
        data = io.BytesIO(self.get_payload())
        tree = ET.parse(data)
        return a38.auto_from_etree(tree.getroot())
