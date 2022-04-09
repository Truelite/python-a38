import logging
from io import StringIO
from typing import List, Tuple

import requests
from lxml import etree


def inspect_vat(vat_state_code: str, vat_number: str) -> Tuple[str, int]:
    params = {
        "memberStateCode": vat_state_code,
        "number": vat_number,
    }
    res = requests.post(
        "https://ec.europa.eu/taxation_customs/vies/vatResponse.html",
        data=params,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "a38",
        },
        timeout=5,
    )
    html_content = res.text
    return html_content, res.status_code


def get_vat_details(vat_state_code: str, vat_number: str) -> List:
    html_content, _ = inspect_vat(vat_state_code, vat_number)
    parser = etree.HTMLParser()
    html_doc = etree.parse(StringIO(html_content), parser).getroot()
    vat_details = []
    keys = html_doc.xpath('//div[@class="static-field"]/label')
    values = html_doc.xpath('//div[@class="static-field"]/div')
    if len(keys) != len(values):
        logging.warning(
            "There's a mismatch between the VIES categories and their content"
        )

    for idx, _ in enumerate(keys):
        vat_details.append(
            {
                "detail": "".join(keys[idx].itertext()).strip(),
                "content": "".join(values[idx].itertext()).strip(),
            }
        )

    return vat_details
